import queue
import threading
import tkinter as tk
import tkinter.font as tkFont
import time
import os
import vlc
import unidecode
import wmctrl
import argparse

from utils.logging_wrapper import setup_logging
from browser_wrapper import TBrowser
from yandex_mus import TYandexMusic
from request_process import TReqProcessor
from zvuchki.config import TConfig



class TZvuchki(tk.Frame):
    def __init__(self, master=None):
        self.args = parse_args()
        self.config = TConfig()

        log_path = os.path.join(os.path.dirname(__file__), "zvuchki.log")
        self.logger = setup_logging(log_file_name=log_path, append_mode=True)

        # Инициализация браузера
        self.browser = TBrowser(self.logger, self.args.use_cache)
        self.is_running = True

        # Очередь для команд (Thread-safe)
        self.browser_queue = queue.Queue()

        # Инициализация Selenium (делаем это до запуска GUI)
        if self.args.attach_browser_address is not None:
            self.browser.attach_to_browser(self.args.attach_browser_address)
        else:
            self.browser.start_browser()

        # Запуск единого воркера для Selenium
        self.worker_thread = threading.Thread(target=self._browser_worker, daemon=True)
        self.worker_thread.start()

        # Настройка TKinter
        self.master = master if master else tk.Tk()
        self.window_title = "ZvuchkiApp"
        self.master.title(self.window_title)

        if self.args.enable_ya_music:
            self.yandex_music_client = TYandexMusic(self, self.args.prefer_rap)
        else:
            self.yandex_music_client = None

        super().__init__(self.master)
        self.master.geometry("1600x200")
        self.master.attributes("-topmost", True)

        self._init_ui_elements()
        self.audioplayer = None

    def _init_ui_elements(self):
        editor_font_size = int(self.args.font_size * 1.28)
        self.editor_font = tkFont.Font(family="DejaVu Sans Mono", size=editor_font_size)
        self.entry_text = tk.StringVar()
        self.text_widget = tk.Entry(self.master, textvariable=self.entry_text, font=self.editor_font)

        # Биндинги
        self.text_widget.bind('<Return>', self.on_return)
        self.text_widget.bind('<Escape>', self.on_stop_playing)
        self.text_widget.bind('<Right>', self.on_right)
        self.text_widget.bind('<Left>', self.on_left)
        self.text_widget.bind('<F1>', self.on_backspace)

        self.master.bind_all('<KeyPress>', self.report_key_press)
        self.text_widget.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.text_widget.focus_force()
        self.video_stop_requested = False

    def _browser_worker(self):
        while self.is_running:
            try:
                task = self.browser_queue.get(timeout=0.5)
                cmd = task.get("cmd")
                self.logger.info("_browser_worker got cmd {}".format(cmd))

                if cmd == "PROCESS_REQUEST":
                    self.video_stop_requested = False  # Сбрасываем флаг перед новым видео
                    self._handle_search_and_play(task["request_str"])

                elif cmd == "BROWSER_KEY":
                    # Только если браузер жив
                    if self.browser.driver:
                        action = task["action"]
                        try:
                            if action == "LEFT":
                                self.browser.send_left()
                            elif action == "RIGHT":
                                self.browser.send_right()
                            elif action == "FULLSCREEN":
                                self.browser.send_f()
                        except Exception as e:
                            self.logger.error(f"Key error: {e}")

                elif cmd == "STOP":
                    # Esc теперь просто взводит флаг
                    self.video_stop_requested = True
                    # Если нужно именно закрыть окна, вызываем:
                    # self.browser.close_all_windows()

                self.browser_queue.task_done()
            except queue.Empty:
                continue

    def _handle_search_and_play(self, request_str):
        """Внутренняя логика воркера: поиск URL и управление воспроизведением"""
        self.logger.info(f"Processing request in worker: {request_str}")

        # 1. Парсим запрос (индексы, прибавки по времени и т.д.)
        req = TReqProcessor(self.logger, self.config, request_str, self.args.transliterate)
        if not req.process_req():
            self.logger.warning("Failed to process request string")
            return

        # 2. Получаем URL видео
        url = None
        duration = self.args.max_play_seconds  # Значение по умолчанию

        if req.use_old_urls:
            # Поиск в локально сохраненных URL (если есть такая логика в конфиге)
            key = f"{req.query}{req.clip_index}".lower()
            url_data = self.config.saved_urls.get(key)
            if url_data:
                url, saved_timeout = url_data
                duration = min(self.args.max_play_seconds, saved_timeout) + req.add_sec
        else:
            # Поиск через Selenium (Google или YouTube)
            query = unidecode.unidecode(req.query) if self.args.transliterate else req.query
            url = self.get_url_video_from_google_or_cached(
                query, req.clip_index, req.use_cache, req.channel_id is not None
            )
            # Если URL найден, TBrowser обновит self.browser.last_clip_length после play_youtube
            duration = self.args.max_play_seconds + req.add_sec

        if not url:
            self.logger.warning(f"No URL found for query: {req.query}")
            return

        # 3. Запуск воспроизведения
        if not self.browser.play_youtube(url):
            if not self.browser.is_alive():
                self.quit()

        # Возвращаем фокус в окно приложения, чтобы можно было печатать дальше
        self.master.after(0, self.set_window_focus)

        # Если браузер смог достать длину клипа, уточняем duration
        if self.browser.last_clip_length:
            real_duration = self.browser.last_clip_length + req.add_sec
            duration = min(duration, real_duration)

        self.logger.info(f"Starting playback: {url} for {duration} seconds")

        # 4. Цикл ожидания окончания видео
        start_time = time.time()
        while time.time() - start_time < duration:
            # ПРОВЕРЯЕМ ОЧЕРЕДЬ прямо во время ожидания
            if not self.browser_queue.empty():
                # "Заглядываем" в очередь без извлечения
                try:
                    # Если там лежит команда STOP, извлекаем её и выходим
                    # Мы проверяем тип команды, чтобы не пропустить нажатия кнопок (LEFT/RIGHT)
                    # которые должны обрабатываться параллельно
                    peek_task = self.browser_queue.queue[0]
                    if peek_task.get("cmd") == "STOP":
                        self.browser_queue.get()  # Удаляем STOP из очереди
                        self.video_stop_requested = True
                        self.browser_queue.task_done()
                except (IndexError, queue.Empty):
                    pass

            if self.video_stop_requested:
                self.logger.info("Playback interrupted by Esc (detected in loop)")
                break

            if not self.browser.is_alive():
                break

            time.sleep(0.5)

        try:
            self.browser.save_play_history(url)
        except Exception as e:
            self.logger.error(f"Error during  save play_history: {e}")

        assert self.browser.is_alive()

        # 5.1 Завершение: сохраняем историю и чистим окна
        try:
            self.browser.reset_to_one_empty_window()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

        # Очищаем поле ввода в GUI
        self.master.after(0, self.on_video_finish)

    def get_url_video_from_google_or_cached(self, request, position, use_cache, use_youtube):
        # Эта логика перенесена из вашего старого main.py, но теперь она "живет" в воркере
        if use_cache and self.browser.use_cache:
            search_results = self.browser.get_cached_request(request)
        else:
            search_results = None

        if search_results is None:
            if not use_youtube:
                search_results = self.browser.send_search_request(request)
            else:
                search_results = self.browser.collect_youtube_clips(request)
            self.browser.reset_to_one_empty_window()

        idx = max(0, position - 1)
        if search_results and idx < len(search_results):
            return search_results[idx]
        return None

    # --- ОБРАБОТЧИКИ СОБЫТИЙ GUI (ТОЛЬКО КЛАДУТ В ОЧЕРЕДЬ) ---

    def on_return(self, event):
        s = self.entry_text.get()
        if s:
            self.play_audio("enter.wav", 50)
            self.browser_queue.put({"cmd": "PROCESS_REQUEST", "request_str": s})

    def on_stop_playing(self, event):
        # 1. Сразу выставляем флаг для прерывания текущего цикла в воркере
        self.video_stop_requested = True

        # 2. Очищаем очередь
        while not self.browser_queue.empty():
            try:
                self.browser_queue.get_nowait()
            except queue.Empty:
                break

        self.logger.info("send stop cmd and set flag")
        # 3. Кладем STOP на случай, если воркер ничем не занят
        self.browser_queue.put({"cmd": "STOP"})

    def on_left(self, event):
        self.browser_queue.put({"cmd": "BROWSER_KEY", "action": "LEFT"})

    def on_right(self, event):
        self.browser_queue.put({"cmd": "BROWSER_KEY", "action": "RIGHT"})

    def on_toggle_full(self, event):
        self.browser_queue.put({"cmd": "BROWSER_KEY", "action": "FULLSCREEN"})

    # --- ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ GUI ---

    def on_video_finish(self):
        self.entry_text.set("")
        self.text_widget.focus_force()

    def set_window_focus(self):
        try:
            wmctrl.Window.by_name(self.window_title)[0].activate()
        except:
            pass

    def report_key_press(self, e):
        # Ваша логика озвучки клавиш
        ch = e.char.upper()
        if self.args.audio_keys:
            # ... (код озвучки из вашего оригинала)
            pass

    def on_backspace(self, event):
        self.play_audio("backspace.wav", 50)
        s = self.entry_text.get()
        self.entry_text.set(s[:-1])

    def play_audio(self, file_path, volume=100):
        full_path = os.path.join(os.path.dirname(__file__), "sound", file_path)
        if os.path.exists(full_path):
            if self.audioplayer: self.audioplayer.stop()
            self.audioplayer = vlc.MediaPlayer(full_path)
            self.audioplayer.audio_set_volume(volume)
            self.audioplayer.play()

    def main_loop(self):
        try:
            self.master.mainloop()
        finally:
            self.is_running = False
            #self.browser.reset_to_one_empty_window()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--font-size", default=100, type=int)
    parser.add_argument("--max-play-seconds", default=540, type=int)
    parser.add_argument("--audio-keys", action="store_true")
    parser.add_argument("--transliterate", action="store_true")
    parser.add_argument("--attach-browser-address", help="например 127.0.0.1:8888")
    parser.add_argument("--disable-cache", action="store_false", dest='use_cache', default=True)
    parser.add_argument("--disable-ya-music", action="store_false", dest='enable_ya_music', default=True)
    parser.add_argument("--prefer-rap", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    app = TZvuchki()
    app.main_loop()