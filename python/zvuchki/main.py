from car_brands import CARS, URLS, BIRDS, COMPOSERS, OTHER_SRC
from browser_wrapper import TBrowser

import os
import sys
import argparse
import tkinter as tk
import tkinter.font as tkFont
import time
import vlc
from functools import partial
import threading


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
            self.browser.start_browser()
            res = self.browser.play_youtube(self.url, self.seconds)
            self.browser.close_browser()
            if res:
                break
        self.parent.on_video_finish()


class TZvuchki(tk.Frame):
    def __init__(self, master=None):
        self.args = parse_args()
        self.logger = setup_logging("office.log")
        self.left_offset = 80
        self.is_running = True
        self.font_size = self.args.font_size
        self.master = tk.Tk()
        super().__init__(master)

        if self.args.fullscreen:
            self.master.attributes("-fullscreen", True)
            self.main_wnd_left = 0
            self.main_wnd_top = 0
            self.main_wnd_width = self.master.winfo_screenwidth()
            self.main_wnd_height = self.master.winfo_screenheight()
        else:
            self.main_wnd_left = 0
            self.main_wnd_top = 0
            self.main_wnd_width = 1600
            self.main_wnd_height = 800
            self.master.geometry("{}x{}".format(self.main_wnd_width, self.main_wnd_height))
        self.audioplayer = None
        self.editor_font = ("DejaVu Sans Mono", self.args.font_size+20)
        self.key_font = tkFont.Font(family="DejaVu Sans Mono", size=self.args.font_size)
        self.key_font_umlaut = tkFont.Font(family="DejaVu Sans Mono", size=self.args.font_size - 20)

        self.master.grid_columnconfigure((0, 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12 ), weight=1)
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_rowconfigure((1, 2, 3), weight=2)

        self.text_widget = tk.Text(self.master,
                                   width=100,
                                   height=1,
                                   font=self.editor_font)
        self.text_widget.grid(column=0,  columnspan=13)
        self.text_widget.bind("<Button-1>", self.on_text_click)
        self.text_widget.tag_config('green_tag', background='lightgreen')

        self.keys = dict()
        self.last_char = None
        self.last_char_timestamp = time.time()
        self.init_all_abc_keyboard()
        self.video_player_thread = None

    def init_all_abc_keyboard(self):
        self.add_keyboard_row(1, "123456780" + TChars.BACKSPACE)
        self.add_keyboard_row(2, "ЙЦУКЕНГШЩЗХ")
        self.add_keyboard_row(3, "ФЫВАПРОЛДЖЭ")
        self.add_keyboard_row(4, "ЯЧСМИТЬБЮ"+TChars.SPACE)

    def add_keyboard_row(self, row_index, chars):
        self.last_char_timestamp = time.time()
        column_index = 0
        for char_index, char in enumerate(chars):
            colspan = 1
            width = 1
            background = None
            if column_index == 0:
                padx = (30, 0)
            else:
                padx = 0
            if char == TChars.SPACE:
                colspan *= 2
                width *= 2
                background = "lightgreen"

            if char == TChars.BACKSPACE:
                colspan *= 3
                width *= 5
                background = "red"
                padx = (0, 0)

            if char_index == len(chars) - 1:
                padx = (0, 100)

            font = self.key_font
            if char == "Й" or char == "Ё":
                font = self.key_font_umlaut

            button = tk.Button(self.master,
                               background=background,
                               text=char, width=width, relief="raised", height=1,
                               font=font,
                               command=partial(self.keyboard_click, char))
            self.keys[char] = button
            button.grid(column=column_index, row=row_index, columnspan=colspan, padx=padx, pady=2)
            column_index += colspan

    def on_video_finish(self):
        self.logger.info('on_video_finish...')
        #self.video_player_thread.join(0.1)
        self.video_player_thread = None
        self.text_widget.delete(1.0, tk.END)

    def on_text_click(self, event):
        self.logger.info("clicked")
        if self.video_player_thread is not None:
            self.video_player_thread.stop_playing()
            self.on_video_finish()
        else:
            s = self.text_widget.get(1.0, tk.END).strip("\n")
            self.play_request(s)

    def get_url_video_from_google_or_cached(self, request, position):
        browser = TBrowser()
        search_results = browser.all_requests.get(request)
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
        if len(words) < 2:
            self.logger.error("car and  video clip index must be specified")
            return False
        if not words[1].isdigit():
            self.logger.error("video clip index must be integer")
            return False
        car_brand = words[0].strip()
        if car_brand.lower() == 'усач':
            car_brand = 'ТРАМВАЙ'

        clip_index = int(words[1])
        add_query = ''
        add_sec = 0
        use_old_urls = False
        for i in range(2, len(words)):
            cmd = words[i]
            if cmd == 'Д':
                add_sec = 120
            elif cmd == 'ДД':
                add_sec = 240
            elif cmd == 'Т':
                add_query = "тест драйв от первого лица"
            elif cmd == 'К':
                add_query = "в кабине водителя"
            elif cmd == 'КРИК':
                add_query = "крик"
            elif cmd == 'З':
                add_query = "звук двигателя"
            elif cmd == 'ЗВУК':
                add_query = "звук"
            elif cmd == 'Э':
                add_query = "эксплуатация"
            elif cmd == 'П':
                use_old_urls = True
        duration =  None
        if use_old_urls:
            key = '{}{}'.format(car_brand, clip_index).lower()
            if key not in URLS:
                self.logger.error("no stored key {}".format(key))
                return False
            url, timeout = URLS[key]
            if self.args.max_play_seconds < timeout:
                timeout = self.args.max_play_seconds
            duration = timeout + add_sec
        else:
            search_obj = car_brand.lower()
            if search_obj not in CARS and search_obj not in BIRDS and search_obj not in COMPOSERS \
                and search_obj not in OTHER_SRC:
                self.logger.error("bad car brand")
                return False
            duration = 300 + add_sec
            #duration = 10 + add_sec
            request = "{} {}".format(car_brand, add_query)
            self.logger.info("req={}, dur={}, serp_index={}".format(request, duration, clip_index))
            url = self.get_url_video_from_google_or_cached(request, clip_index)
        self.play_youtube_video(url, duration)
        return True

    def get_text_str(self):
        return self.text_widget.get(1.0, tk.END).strip("\n")

    def backspace(self):
        s = self.get_text_str()
        if len(s) > 0:
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.insert(tk.END, s[:-1])

    def add_char(self, char):
        s = self.get_text_str()
        if len(s) > MAX_TEXT_LEN:
            return
        tags = 'green_tag' if char == ' ' else None
        self.text_widget.insert(tk.END, char, tags)

    def keyboard_click(self, char):
        if self.video_player_thread is not None:
            if char and char.upper() == 'Н':
                self.video_player_thread.next_track()
            if char and char.upper() == 'П':
                self.video_player_thread.prev_track()
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
        self.logger.info("text={}".format(self.text_widget.get(1.0, tk.END).strip("\n")))

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
    parser.add_argument("--row1", dest='row1', default='')
    parser.add_argument("--row2", dest='row2', default='МПАВЯЛОНЕ𝄞 ')
    parser.add_argument("--font-size", dest='font_size', default=90, type=int)
    parser.add_argument("--max-play-seconds", dest='max_play_seconds', default=540, type=int)
    return parser.parse_args()


if __name__ == "__main__":
    game = TZvuchki()
    game.main_loop()

# shift N


