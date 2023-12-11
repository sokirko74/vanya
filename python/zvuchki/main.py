import json

from car_brands import CARS, URLS, BIRDS, COMPOSERS, OTHER_SRC
from browser_wrapper import TBrowser
from yandex_mus import TYandexMusic

import os
import sys
import argparse
import tkinter as tk
import tkinter.font as tkFont
import time
import vlc
from functools import partial
import threading
import re


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
    def __init__(self, parent,url, seconds):
        threading.Thread.__init__(self)
        self.parent = parent
        self.url = url
        self.seconds = seconds
        self._interrupted = False
        self.browser = None

    def stop_playing(self):
        self._interrupted = True
        self.browser.close_browser()

    def next_track(self):
        self.browser.send_shift_n()

    def prev_track(self):
        self.browser.send_shift_p()

    def run(self):
        for try_index in range(2):
            if not self.parent.is_running or self._interrupted:
                break
            self.browser = TBrowser()
            self.parent.logger.info("Number of cached urls: {}".format(len(self.browser.all_requests)))
            self.browser.start_browser()
            res = self.browser.play_youtube(self.url, self.seconds)
            self.browser.close_browser()
            if res:
                break
        self.parent.on_video_finish()


class TZvuchki(tk.Frame):
    def __init__(self, master=None):
        self.args = parse_args()
        log_path = os.path.join(os.path.dirname(__file__), "zvuchki.log")
        self.logger = setup_logging(log_file_name=log_path, append_mode=True)
        self.left_offset = 80
        self.is_running = True
        self.font_size = self.args.font_size
        self.keyboard_column_count = 12
        self.master = tk.Tk()
        self.yandex_music_client = TYandexMusic(self.logger, self.args.prefer_rap)
        super().__init__(master)
        if self.args.fullscreen:
            if self.master.winfo_screenwidth() > 2000:
                self.master.geometry("1600x800+2000+0")
            self.master.attributes("-fullscreen", True)
        else:
            self.master.geometry("1600x800")
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

        self.text_widget.bind('<Return>', self.on_text_click)
        self.text_widget.bind('<Escape>', self.on_text_click)
        self.text_widget.bind('<F1>', self.on_backspace)
        self.bind('<Return>', self.on_text_click)
        self.bind('<Escape>', self.on_text_click)
        self.text_widget.place(relx=0, rely=0, relwidth=1, relheight=self.editor_coef_height)
        self.text_widget.bind("<Button-1>", self.on_text_click)

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

        self.key_row_count = 4
        self.keys = dict()
        self.last_char = None
        self.last_char_timestamp = time.time()
        self.init_all_abc_keyboard_layout(self.args.layout)
        self.video_player_thread = None

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
            canvas.bind("<Button-1>", partial(self.keyboard_click, key_info['char']))
            left += button_width

    def on_video_finish(self):
        self.logger.info('on_video_finish...')
        #self.video_player_thread.join(0.1)
        self.video_player_thread = None
        self.entry_text.set("")

    def on_backspace(self, event):
        s = self.entry_text.get()
        self.entry_text.set(s[:-1])
        self.text_widget.select_clear()

    def on_text_click(self, event):
        self.text_widget.select_clear()
        self.logger.info("clicked")
        if self.video_player_thread is not None:
            self.video_player_thread.stop_playing()
            self.on_video_finish()
        elif  self.yandex_music_client.is_playing():
            self.logger.info("stop yandex music player")
            self.yandex_music_client.stop_player()
        else:
            s = self.entry_text.get()
            self.play_request(s)

    def get_url_video_from_google_or_cached(self, request, position):
        browser = TBrowser()
        search_results = browser.get_cached_request(request)
        if search_results is None:
            browser.start_browser()
            search_results = browser.send_request(request)
            browser.close_browser()
        if position > 0:
            position -= 1
        if position >= len(search_results):
            position = len(search_results) - 1
        return search_results[position]

    def play_youtube_video(self, url, seconds):
        self.video_player_thread = VideoPlayer(self, url, seconds)
        self.video_player_thread.start()

    def play_request(self, request):
        words = request.strip().split(' ')
        query_words = list()
        clip_index = None
        add_to_query = list()
        add_sec = 0
        use_old_urls = False
        use_yandex_music = False
        free_request = False
        test_drive = "тест драйв от первого лица"
        for token_index, token in enumerate(words):
            if token.isdigit() and clip_index is None and int(token) < 10 and token_index > 0:
                clip_index = int(token)
                continue

            if token == 'Д':
                add_sec = 120
            elif token == 'ДД':
                add_sec = 240
            elif token == 'Т':
                add_to_query.append(test_drive)
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
            elif token == 'ЗВУК':
                add_to_query.append( "звук")
            elif token == 'R':
                add_to_query.append("rapper")
            elif token == 'СТ':
                add_to_query.append("СТАРЫЙ")
            elif token == 'М':
                add_to_query.append("МАШИНА")
            elif token == 'Э':
                add_to_query.append( "эксплуатация")
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
                    return True
                else:
                    self.logger.error("bad artist")
                    return False
            else:
                #digit = re.search(r'(\d)', search_obj)
                #if digit is not None:
                #    search_obj = search_obj[:digit.regs[0][0]]

                if not free_request:
                    if search_obj not in CARS and search_obj not in BIRDS and search_obj not in COMPOSERS \
                            and search_obj not in OTHER_SRC:
                        self.logger.error("bad query search")
                        return False
                duration = 300 + add_sec
                #duration = 10 + add_sec
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

    def keyboard_click(self, char, event):
        if self.video_player_thread is not None:
            if char and char.upper() == 'Н':
                self.video_player_thread.next_track()
            if char and char.upper() == 'П':
                self.video_player_thread.prev_track()
        if char == TChars.BACKSPACE:
            self.on_backspace()
            self.play_audio("key_sound.wav")
        if char == TChars.BACKSPACE:
            self.backspace()
            self.play_audio("key_sound.wav")
        else:
            ts = time.time()
            if ts - self.last_char_timestamp < 1 and char == self.last_char:
                return
            self.last_char_timestamp = ts
            self.last_char = char
            self.play_audio("key_sound.wav")
            self.add_char(char)
        self.logger.info("text={}".format(self.entry_text.get()))

    def play_audio(self, file_path):
        file_path = os.path.join(os.path.dirname(__file__), "sound", file_path)
        if self.audioplayer is not None:
            self.audioplayer.stop()
        self.audioplayer = vlc.MediaPlayer(file_path)
        self.audioplayer.play()

    def main_loop(self):
        self.master.mainloop()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fullscreen", dest='fullscreen', default=False, action="store_true")
    parser.add_argument("--layout", dest='layout', default='anc_ru.json')
    parser.add_argument("--font-size", dest='font_size', default=100, type=int)
    parser.add_argument("--max-play-seconds", dest='max_play_seconds', default=540, type=int)
    parser.add_argument("--prefer-rap", dest='prefer_rap', default=False, action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    game = TZvuchki()
    game.main_loop()

# shift N


