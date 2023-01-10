import os
import sys
import argparse
import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk
import time
import vlc
import random
from functools import partial
sys.path.append(os.path.join(os.path.dirname(__file__), '../utils'))
from logging_wrapper import setup_logging

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (228, 155, 0)

GOAL_WORDS = [
    "МАМА",
    "ПАПА",
    "ВАНЯ"
]

class TVanyaOffice(tk.Frame):
    def __init__(self, master=None):
        self.args = parse_args()
        self.logger = setup_logging("office.log")
        self.left_offset = 80
        self.is_running = True
        self.print_victory = False
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
            self.main_wnd_width = 1200
            self.main_wnd_height = 800
            self.master.geometry("{}x{}".format(self.main_wnd_width, self.main_wnd_height))
        self.audioplayer = None
        self.editor_font = ("DejaVu Sans Mono", self.args.font_size+20)
        self.goal_word = tk.StringVar()
        self.goal_words_combobox = tk.ttk.Combobox(
            self.master, width=10, textvariable=self.goal_word, font=self.editor_font)
        self.goal_words_combobox['values'] = tuple(GOAL_WORDS)
        self.new_game()
        self.last_word = ""
        self.fail_count = 0
        self.victory_count = 0
        self.goal_words_combobox.pack(side=tk.TOP)
        self.text_widget = tk.Text(self.master,
                                   width=20,
                                   height=1,
                                   font=self.editor_font)
        self.text_widget.pack(side=tk.TOP)
        self.text_widget.focus_set()

        self.log_widget = tk.Text(self.master , width=100, height=3)
        self.log_widget.pack(side=tk.BOTTOM)
        self.master.bind('<KeyPress>', self.keyboard_click)

    def new_game(self):
        last_goal = self.goal_word.get()
        words = list(GOAL_WORDS)
        if last_goal in words:
            words.remove(last_goal)
        w = random.choice(words)
        self.goal_words_combobox.set(w)
        self.goal_word.set(w)
        self.goal_words_combobox.update()

        self.fail_count = 0

    def print_to_log(self, m):
        self.log_widget.insert(tk.END, m)
        self.log_widget.see(tk.END)
        self.logger.info(m)

    def keyboard_click(self, event):
        ch = event.char.upper()
        new_word = self.text_widget.get(1.0, tk.END).strip().upper()
        if event.char == '\r':
            self.play_file("delete_all.wav")
            self.text_widget.delete('1.0', tk.END)
            self.fail_count = 0
            return
        
        if self.last_word == new_word:
            return
        self.last_word = new_word
        if new_word == "":
            return
        goal_word = self.goal_word.get()
        if goal_word == new_word:
            self.text_widget.update()
            self.victory_count += 1
            self.print_to_log("victory count = {}\n".format(self.victory_count))
            self.play_file("victory.wav")
            time.sleep(5)
            self.text_widget.delete('1.0', tk.END)
            self.new_game()
        elif goal_word.startswith(new_word):
            #self.text_widget.insert('end', ch)
            self.play_file("key_sound.wav")
        else:
            if len(ch) == 1 and ord(ch) >= 32:
                self.fail_count += 1
                self.play_file("key_fail.wav")
                self.print_to_log("fail count = {}\n".format(self.fail_count))

    def play_file(self, file_path):
        file_path = os.path.join(os.path.dirname(__file__), "sound", file_path)
        if self.audioplayer is not None:
            self.audioplayer.stop()
        self.audioplayer = vlc.MediaPlayer(file_path)
        self.audioplayer.play()

    def main_loop(self):
        self.master.mainloop()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--not-fullscreen", dest='fullscreen', default=True, action="store_false")
    parser.add_argument("--font-size", dest='font_size', default=100, type=int)
    return parser.parse_args()


if __name__ == "__main__":
    game = TVanyaOffice()
    game.main_loop()
