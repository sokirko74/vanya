from car_brands import CARS, URLS, BIRDS, COMPOSERS, OTHER_SRC, CAR_EN
from browser_wrapper import TBrowser
from yandex_mus import TYandexMusic
import selenium

import os
import sys
import argparse
import json
import tkinter as tk
import tkinter.font as tkFont
import time
import vlc
from functools import partial
import threading
import unidecode
import wmctrl


sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logging_wrapper import setup_logging


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (228, 155, 0)

MAX_TEXT_LEN = 25


class TChars:
    BACKSPACE = '⌫'
    PLAY = '𝄞'
    SPACE = ' '


class VideoPlayer (threading.Thread):
    def __init__(self, parent, url, seconds):
        threading.Thread.__init__(self)
        self.parent = parent
        self.browser: TBrowser = parent.browser
        self.url = url
        self.seconds = seconds
        self._interrupted = False

    def stop_playing(self):
        self._interrupted = True
        time.sleep(1)

    def next_track(self):
        self.browser.send_shift_n()

    def prev_track(self):
        self.browser.send_shift_p()

    def run(self):
        for try_index in range(2):
            if not self.parent.is_running or self._interrupted:
                break
            if self.browser.play_youtube(self.url):
                self.parent.set_window_focus()
                print("sleep for  {} seconds (video duration)".format(self.seconds))
                for i in range(self.seconds):
                    if self._interrupted:
                        break
                    time.sleep(1)
                self.browser.close_all_windows()
                self.parent.on_video_finish()
                return
            if self._interrupted:
                return



def transliterate(s):
    return unidecode.unidecode(s)


class TZvuchki(tk.Frame):
    def __init__(self, master=None):
        self.args = parse_args()
        self.browser:TBrowser  = TBrowser()
        log_path = os.path.join(os.path.dirname(__file__), "zvuchki.log")
        self.logger = setup_logging(log_file_name=log_path, append_mode=True)

        self.logger.info("Number of cached urls: {}".format(len(self.browser.all_requests)))
        if self.args.attach_browser_address is not None:
            self.browser.attach_to_browser(self.args.attach_browser_address)
        else:
            self.browser.start_browser()

        self.left_offset = 80
        self.is_running = True
        self.font_size = self.args.font_size
        self.keyboard_column_count = 12
        self.master = tk.Tk()
        self.window_title = "ZvuchkiApp"
        self.master.title(self.window_title)
        if self.args.enable_ya_music:
            self.yandex_music_client = TYandexMusic(self, self.args.prefer_rap)
        else:
            self.yandex_music_client = None

        self.key_row_count = 4
        self.keys = dict()
        self.last_char = None
        self.last_char_timestamp = time.time()


        super().__init__(master)
        if self.args.fullscreen:
            if self.master.winfo_screenwidth() > 2000:
                self.master.geometry("1600x800+2000+0")
            self.master.attributes("-fullscreen", True)
        else:
            if self.args.gui_keyboard:
                self.master.geometry("1600x800")
            else:
                self.master.geometry("1600x200")
        self.master.attributes("-topmost", True)
        self.audioplayer = None
        self.music_player_pid = None
        self.editor_coef_height = 0.28
        editor_font_size = int(self.args.font_size * (1.0 + self.editor_coef_height))
        self.editor_font = tkFont.Font(family="DejaVu Sans Mono", size=editor_font_size)
        self.entry_text = tk.StringVar()
        self.text_widget = tk.Entry(self.master,
                                   width=15,
                                   textvariable = self.entry_text,
                                   font=self.editor_font)

        self.text_widget.bind('<Return>', self.on_return)
        self.text_widget.bind('<Escape>', self.on_stop_playing)
        self.text_widget.bind('<Right>', self.on_right)
        self.text_widget.bind('<Left>', self.on_left)
        self.text_widget.bind('<F1>', self.on_backspace)
        self.bind('<Return>', self.on_return)
        self.bind('<Escape>', self.on_stop_playing)
        self.bind('<Left>', self.on_left)
        self.bind('<Right>', self.on_right)

        self.text_widget.focus_force()
        if self.args.audio_keys:
            self.master.bind_all('<KeyPress>', self.report_key_press)
        if not self.args.gui_keyboard:
            self.text_widget.place(relx=0, rely=0, relwidth=1,
                                   relheight=1)
            self.master.update()
        else:
            self.text_widget.place(relx=0, rely=0, relwidth=1, relheight=self.editor_coef_height)
            self.keyb_window = tk.Frame(
                self.master,
                #background="yellow"
            )
            self.keyb_window.place(
                relx=0,
                rely=self.editor_coef_height,
                relwidth=1,
                relheight=(1.0-self.editor_coef_height),
            )
            self.master.update()
            self.key_font = tkFont.Font(family="DejaVu Sans Mono", size=self.args.font_size)
            self.key_font_umlaut = tkFont.Font(family="DejaVu Sans Mono", size=int(self.args.font_size * 0.7))

            self.init_all_abc_keyboard_layout(self.args.layout)
        self.video_player_thread = None

    def report_key_press(self, e):
        ch = e.char.upper()
        if (ch  == "П" or ch  == "G") and self.get_playing_source():
            self.on_toggle_full(e)

        if ch == '*':
            return
        if ch == '\x08':
            self.play_audio('backspace.wav', 50)
        #print ('press '+ ch)
        if ch == ' ':
            ch = 'space'
        filename = 'char.' + ch + '.mp3'
        path = os.path.join(os.path.dirname(__file__), 'sound', filename)
        if os.path.exists(path):
            self.play_audio(filename)

    def init_all_abc_keyboard_layout(self, layout_path):
        with open(layout_path) as inp:
            keyb_layout = json.load(inp)
        assert len(keyb_layout) == self.key_row_count
        for row_index, row in enumerate(keyb_layout):
            self.add_keyboard_row(row_index, row)

    def get_key_row_height(self):
        h = self.keyb_window.winfo_height() / self.key_row_count
        return int(h)

    def add_keyboard_row(self, row_index, row):
        normal_btn_width = self.master.winfo_width() / self.keyboard_column_count
        left = row_index * normal_btn_width / 3.0
        top = row_index * (self.get_key_row_height() + 5)

        for key_info in row:
            key_title = key_info['char']
            if key_info.get("long"):
                key_title = " " + key_title + " "
            background = key_info.get("background")
            font = self.key_font
            title_top = -5

            if key_info.get("umlaut"):
                font = self.key_font_umlaut
                title_top = 0

            button_width = len(key_title) * normal_btn_width
            canvas = tk.Canvas(
                self.keyb_window,
                background=background,
                width=button_width
            )
            canvas.create_text(
                15,
                title_top,
                text=key_title,
                font=font, anchor=tk.NW)
            canvas.place(
                x=left,
                y=top,
                width=button_width,
                relheight=1 / self.key_row_count
            )
            canvas.bind("<Button-1>", partial(self.gui_keyboard_click, key_info['char']))
            left += button_width

    def on_video_finish(self):
        self.logger.info('on_video_finish...')
        self.video_player_thread = None
        self.entry_text.set("")

    def on_backspace(self, event):
        self.play_audio("backspace.wav", 50)
        s = self.entry_text.get()
        self.entry_text.set(s[:-1])
        self.text_widget.select_clear()

    def get_playing_source(self):
        if self.video_player_thread is not None:
            return "youtube"
        elif  self.yandex_music_client and self.yandex_music_client.is_playing():
            return "yandex_music"
        else:
            return None

    def on_left(self, event):
        src = self.get_playing_source()
        if src == "youtube":
            self.browser.send_left()
            self.set_window_focus()

    def set_window_focus(self):
        print("set_window_focus")
        wmctrl.Window.by_name(self.window_title)[0].activate()

    def on_toggle_full(self, event):
        self.logger.info("on_toggle_full")
        self.browser.send_f()
        self.set_window_focus()

    def on_right(self, event):
        src = self.get_playing_source()
        if src == "youtube":
            self.browser.send_right()
            self.set_window_focus()

    def on_stop_playing(self, event):
        src = self.get_playing_source()
        if src == "youtube":
            self.logger.info("stop playing youtube")
            try:
                self.video_player_thread.stop_playing()
                self.on_video_finish()
            except selenium.common.exceptions.WebDriverException:
                pass
        elif src == "yandex_music":
            self.logger.info("stop yandex music player")
            self.yandex_music_client.stop_player()

    def on_return(self, event):
        if self.get_playing_source() is not None:
            self.logger.info("press esc to stop player")
            return

        ts = time.time()
        if ts - self.last_char_timestamp < 2 and '\n' == self.last_char:
            return
        self.last_char_timestamp = ts
        self.last_char = '\n'
        self.play_audio("enter.wav", 50)
        self.text_widget.select_clear()
        self.logger.info("on_return")
        s = self.entry_text.get()
        self.play_request(s)

    def get_url_video_from_google_or_cached(self, request, position):
        search_results = self.browser.get_cached_request(request)
        if search_results is None:
            search_results = self.browser.send_request(request)
            self.browser.close_all_windows()
        if position > 0:
            position -= 1
        if position >= len(search_results):
            position = len(search_results) - 1
        return search_results[position]

    def set_focus_to_text(self):
        print("set_focus_to_text")
        time.sleep(0.1)
        self.set_window_focus()
        self.text_widget.focus_force()

    def is_relevant(self, w):
        return w in CARS or w in BIRDS or w in COMPOSERS or w in OTHER_SRC or w in CAR_EN

    def is_relevant_plus(self, w ):
        if self.is_relevant(w):
            return True
        for i in w.split(' '):
            if self.is_relevant(i):
                return True
        return False

    def play_youtube_video(self, url, seconds):
        self.video_player_thread = VideoPlayer(self, url, seconds)
        self.logger.info("video_player_thread.start()")
        self.video_player_thread.start()
        self.set_focus_to_text()

    def play_request(self, request):
        words = request.strip().split(' ')
        query_words = list()
        clip_index = None
        add_to_query = list()
        add_sec = 0
        use_old_urls = False
        use_yandex_music = False
        free_request = self.args.free_request
        test_drive = "тест драйв от первого лица"
        test_drive_en  = "test drive"
        for token_index, token in enumerate(words):
            if token.isdigit() and clip_index is None and int(token) < 10 and token_index > 0:
                clip_index = int(token)
                continue
            token = token.upper()
            if token == 'Д':
                add_sec = 120
            elif token == 'ДД':
                add_sec = 240
            elif token == 'Т':
                if self.args.transliterate:
                    add_to_query.append(test_drive_en)
                else:
                    add_to_query.append(test_drive)
            elif token == 'T':
                self.logger.info('add en test drive')
                add_to_query.append(test_drive_en)
            elif token == 'R':
                add_to_query.append('retro')
            elif token == 'ТД':
                add_to_query.append( test_drive)
                add_sec = 120
            elif token == 'ТДД':
                add_to_query.append( test_drive)
                add_sec = 240
            elif token == 'К':
                add_to_query.append("в кабине водителя")
            elif token == 'КРИК':
                add_to_query.append( "крик")
            elif token == 'З':
                add_to_query.append( "звук двигателя")
            elif token == 'S':
                add_to_query.append("engine start")
            elif token == 'ЗВУК':
                add_to_query.append( "звук")
            elif token == 'ЗПМ':
                add_to_query.append("звук пишущей машинки")
            elif token == 'R':
                add_to_query.append("rapper")
            elif token == 'СТ':
                add_to_query.append("СТАРЫЙ")
            elif token == 'М':
                add_to_query.append("МАШИНА")
            elif token == 'Э':
                add_to_query.append( "эксплуатация")
            elif token == 'Р':
                add_to_query.append("реставрация")
            elif token == 'П':
                use_old_urls = True
            elif token == 'Г':
                free_request = True
            elif token.lower() == 'я':
                use_yandex_music = True
            elif token.lower() == 'y':
                use_yandex_music = True
            else:
                if len(token) > 0:
                    query_words.append(token)
        if clip_index is None:
            self.logger.error("specify video clip index (integer after query)")
            return False
        if len(query_words) == 0:
            self.logger.error("no query")
            return False
        query = " ".join(query_words)
        if use_old_urls:
            key = '{}{}'.format(query, clip_index).lower()
            if key not in URLS:
                self.logger.error("no stored key {}".format(key))
                return False
            url, timeout = URLS[key]
            if self.args.max_play_seconds < timeout:
                timeout = self.args.max_play_seconds
            duration = timeout + add_sec
        else:
            search_obj = query.lower()
            if use_yandex_music:
                pid = self.yandex_music_client.play_track(search_obj, clip_index)
                if pid is not None:
                    self.entry_text.set("")
                    self.set_focus_to_text()
                    return True
                else:
                    self.logger.error("bad artist")
                    return False
            else:
                if not free_request:
                    if not self.is_relevant_plus(search_obj):
                        self.logger.error("bad query search: " + search_obj)
                        return False
                duration = 300 + add_sec
                #duration = 10 + add_sec
                if self.args.transliterate:
                    query = transliterate(query)
                if add_to_query:
                    query += " " + " ".join(add_to_query)
                self.logger.info("req={}, dur={}, serp_index={}".format(query, duration, clip_index))
                url = self.get_url_video_from_google_or_cached(query, clip_index)
        self.play_youtube_video(url, duration)
        return True

    def backspace(self):
        s = self.entry_text.get()
        if len(s) > 0:
            self.entry_text.set(s[:-1])

    def add_char(self, char):
        s = self.entry_text.get()
        if len(s) > MAX_TEXT_LEN:
            return
        self.entry_text.set(s + char)

    def gui_keyboard_click(self, char, event):
        if self.video_player_thread is not None:
            if char and char.upper() == 'Н':
                self.video_player_thread.next_track()
            if char and char.upper() == 'П':
                self.video_player_thread.prev_track()
        if char == TChars.BACKSPACE:
            self.on_backspace()
            self.play_audio("key_sound.wav")
        elif char == '*':
            pass
        else:
            ts = time.time()
            if ts - self.last_char_timestamp < 1 and char == self.last_char:
                return
            self.last_char_timestamp = ts
            self.last_char = char
            self.play_audio("key_sound.wav")
            self.add_char(char)
        self.logger.info("text={}".format(self.entry_text.get()))

    def play_audio(self, file_path, volume=None):
        file_path = os.path.join(os.path.dirname(__file__), "sound", file_path)
        if self.audioplayer is not None:
            self.audioplayer.stop()
        self.audioplayer = vlc.MediaPlayer(file_path)
        self.audioplayer.audio_set_volume(100)
        # if volume is not None:
        #     save_volume = self.audioplayer.audio_get_volume()
        #     self.audioplayer.audio_set_volume(volume)
        # else:
        #     save_volume =  None

        self.audioplayer.play()
        # if save_volume is not None:
        #     self.audioplayer.audio_set_volume(save_volume)

    def main_loop(self):
        self.master.mainloop()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fullscreen", dest='fullscreen', default=False, action="store_true")
    parser.add_argument("--layout", dest='layout', default='anc_ru.json')
    parser.add_argument("--font-size", dest='font_size', default=100, type=int)
    parser.add_argument("--max-play-seconds", dest='max_play_seconds', default=540, type=int)
    parser.add_argument("--prefer-rap", dest='prefer_rap', default=False, action="store_true")
    parser.add_argument("--no-gui-keyboard", dest='gui_keyboard', default=True, action="store_false")
    parser.add_argument("--audio-keys", dest='audio_keys', default=False, action="store_true")
    parser.add_argument("--transliterate", dest='transliterate', default=False, action="store_true")
    parser.add_argument("--free", dest='free_request', default=False, action="store_true")
    parser.add_argument("--disable-ya-music", dest='enable_ya_music', default=True, action="store_false")
    parser.add_argument("--attach-browser-address", help="run before google-chrome --remote-debugging-port=8888")
    return parser.parse_args()


if __name__ == "__main__":
    game = TZvuchki()
    game.main_loop()


