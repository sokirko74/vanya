import queue
import threading
import tkinter as tk
import tkinter.font as tkFont
import time
import os
import vlc
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


        # Инициализация Selenium (делаем это до запуска GUI)
        if self.args.attach_browser_address is not None:
            self.browser.attach_to_browser(self.args.attach_browser_address)
        else:
            self.browser.start_browser()

        # Запуск единого воркера для Selenium
        self.worker_thread = threading.Thread(target=self._browser_worker, daemon=True)
        self.worker_thread.start()

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
        self.is_playing = False

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

    def put_browser_cmd(self, cmd, action):
        d = {"cmd": cmd, "action": action}
        self.browser.browser_queue.put(d)

    def _end_video(self, req):
        self.is_playing = False
        self.browser.end_video(req)
        self.entry_text.set("")
        self.text_widget.focus_force()

    def _browser_worker(self):
        req = None
        while self.is_running:
            if req is not None:
                if time.time() > req.endtime:
                    self.logger.info("stop video since time is over")
                    self._end_video(req)
                    req = None

            try:
                task = self.browser.browser_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            self.logger.info("_browser_worker got task {}".format(task))
            cmd = task.get("cmd")

            if cmd == "PROCESS_REQUEST":
                req = self._handle_search_and_play(task["action"])

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
            elif cmd == "STOP" and req:
                self._end_video(req)
                req = None

            self.browser.browser_queue.task_done()

    def _handle_search_and_play(self, request_str):
        self.logger.info(f"Processing request in worker: {request_str}")

        req = TReqProcessor(self.logger,
                            self.config,
                            request_str,
                            self.args.transliterate,
                            self.args.max_play_seconds
                            )

        if not req.process_req():
            self.logger.warning("Failed to process request string")
            return None

        if req.request_command == "ПАМ":
            if self.browser.last_channel_id:
                self.config.save_channel_alias(
                    self.browser.last_channel_name,
                    self.browser.last_channel_id,
                    req.query)
                self.logger.error("saved {}".format(self.browser.last_channel_id))
                self.play_audio("saved.wav", 30)
                self.entry_text.set("")
            else:
                self.logger.error("no channel name")
            return None

        req.determine_url_and_duration(self.args, self.browser)

        if not req.url:
            self.logger.warning(f"No URL found for query: {req.query}")
            return None

        if not self.browser.play_youtube(req):
            if not self.browser.is_alive():
                self.quit()

        self.is_playing = True

        return req


    def on_return(self, event):
        s = self.entry_text.get()
        if s:
            self.play_audio("enter.wav", 50)
            self.put_browser_cmd("PROCESS_REQUEST", s)

    def on_stop_playing(self, event):
        self.logger.info("send stop cmd and set flag")
        if self.is_playing:
            self.put_browser_cmd("STOP", None)

    def on_left(self, event):
        if self.is_playing:
            self.put_browser_cmd("BROWSER_KEY", "LEFT")

    def on_right(self, event):
        if self.is_playing:
            self.put_browser_cmd("BROWSER_KEY", "RIGHT")

    def on_toggle_full(self, event):
        self.put_browser_cmd("BROWSER_KEY", "FULLSCREEN")

    def set_window_focus(self):
        try:
            wmctrl.Window.by_name(self.window_title)[0].activate()
        except:
            pass

    def report_key_press(self, e):
        ch = e.char.upper()
        if (ch  == "П" or ch  == "G") and self.is_playing:
            self.logger.debug("toggle_full")
            self.on_toggle_full(e)
            return

        if ch == '*':
            return

        if self.args.audio_keys:
            if ch == '\x08':
                self.play_audio('backspace.wav', 50)
            if ch == ' ':
                ch = 'space'
            filename = 'char.' + ch + '.mp3'
            path = os.path.join(os.path.dirname(__file__), 'sound', filename)
            if os.path.exists(path):
                self.play_audio(filename)

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