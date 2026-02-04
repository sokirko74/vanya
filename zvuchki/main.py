from utils.logging_wrapper import setup_logging
from browser_wrapper import TBrowser
from yandex_mus import TYandexMusic
from request_process import TReqProcessor
from zvuchki.config import TConfig
from zvuchki.video_player import VideoPlayer

import selenium
import os
import argparse
import tkinter as tk
import tkinter.font as tkFont
import time
import vlc
from functools import partial
import unidecode
import wmctrl



MAX_TEXT_LEN = 25


class TChars:
    BACKSPACE = '⌫'
    PLAY = '𝄞'
    SPACE = ' '


def transliterate(s):
    return unidecode.unidecode(s)


class TZvuchki(tk.Frame):
    def __init__(self, master=None):
        self.args = parse_args()
        self.config = TConfig()

        log_path = os.path.join(os.path.dirname(__file__), "zvuchki.log")
        self.logger = setup_logging(log_file_name=log_path, append_mode=True)
        self.browser:TBrowser  = TBrowser(self.logger, self.args.use_cache)

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
        self.master.geometry("1600x200")
        self.master.attributes("-topmost", True)


        self.audioplayer = None
        self.music_player_pid = None
        self.editor_coef_height = 0.28
        editor_font_size = int(self.args.font_size * (1.0 + self.editor_coef_height))
        self.editor_font = tkFont.Font(family="DejaVu Sans Mono", size=editor_font_size)
        self.entry_text = tk.StringVar()
        self.text_widget = tk.Entry(self.master,
                                   width=10,
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
        self.master.bind_all('<KeyPress>', self.report_key_press)
        self.text_widget.place(relx=0, rely=0, relwidth=1,
                               relheight=1)
        self.master.update()

        self.video_player_thread = None

    def report_key_press(self, e):
        ch = e.char.upper()
        if (ch  == "П" or ch  == "G") and self.get_playing_source():
            self.logger.debug("toggle_full")
            self.on_toggle_full(e)
            return

        if ch == '*':
            return

        if self.args.audio_keys:
            if ch == '\x08':
                self.play_audio('backspace.wav', 50)
            #print ('press '+ ch)
            if ch == ' ':
                ch = 'space'
            filename = 'char.' + ch + '.mp3'
            path = os.path.join(os.path.dirname(__file__), 'sound', filename)
            if os.path.exists(path):
                self.play_audio(filename)


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

    def get_url_video_from_google_or_cached(self, request, position, use_cache, use_youtube):
        if use_cache and self.browser.use_cache:
            search_results = self.browser.get_cached_request(request)
        else:
            search_results = None

        if search_results is None:
            if not use_youtube:
                search_results = self.browser.send_search_request(request)
            else:
                search_results = self.browser.collect_youtube_clips(request)
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
        return w in self.config.simple_queries

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
        req = TReqProcessor(self.logger, self.config, request)
        if not req.process_req():
            return False

        if req.request_command == "ПАМ":
            if self.browser.last_channel_id:
                self.config.save_channel_alias(
                    self.browser.last_channel_name,
                    self.browser.last_channel_id,
                    req.query)
                self.play_audio("saved.wav", 20)
                self.entry_text.set("")
            else:
                self.logger.error("no channel name")
            return False

        query = req.query
        if req.use_old_urls:
            key = '{}{}'.format(req.query, req.clip_index).lower()
            if key not in self.config.saved_urls:
                self.logger.error("no stored key {}".format(key))
                return False
            url, timeout = self.config.saved_urls[key]
            if self.args.max_play_seconds < timeout:
                timeout = self.args.max_play_seconds
            duration = timeout + req.add_sec
        else:
            if req.use_yandex_music:
                search_obj = query.lower()
                pid = self.yandex_music_client.play_track(search_obj, req.clip_index)
                if pid is not None:
                    self.entry_text.set("")
                    self.set_focus_to_text()
                    return True
                else:
                    self.logger.error("bad artist")
                    return False
            else:
                duration = 300 + req.add_sec
                if self.args.transliterate:
                    query = transliterate(query)
                self.logger.info("req={}, dur={}, serp_index={}".format(query, duration, req.clip_index))
                url = self.get_url_video_from_google_or_cached(
                    query,
                    req.clip_index,
                    req.use_cache,
                    req.channel_id is not None
                )
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

    def play_audio(self, file_path, volume=100):
        file_path = os.path.join(os.path.dirname(__file__), "sound", file_path)
        if self.audioplayer is not None:
            self.audioplayer.stop()
        self.audioplayer = vlc.MediaPlayer(file_path)
        self.audioplayer.audio_set_volume(volume)
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
    parser.add_argument("--disable-ya-music", dest='enable_ya_music', default=True, action="store_false")
    parser.add_argument("--attach-browser-address", help="run before google-chrome --remote-debugging-port=8888")
    parser.add_argument("--disable-cache", action="store_false", dest='use_cache', default=True)
    return parser.parse_args()


if __name__ == "__main__":
    game = TZvuchki()
    game.main_loop()


