import os
import sys
import argparse
import tkinter as tk
import tkinter.font as tkFont
import time
import vlc
from functools import partial
sys.path.append(os.path.join(os.path.dirname(__file__), '../common'))
from logging_wrapper import setup_logging

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (228, 155, 0)



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
        self.player = None
        self.editor_font = ("DejaVu Sans Mono", self.args.font_size+20)
        self.key_font =  tkFont.Font(family="DejaVu Sans Mono", size=self.args.font_size)
        self.text_widget = tk.Text(self.master,
                                   width=100,
                                   height=1,
                                   font=self.editor_font)
        self.text_widget.pack(side=tk.TOP)

        self.keys = dict()
        self.last_char = None
        self.last_char_timestamp = time.time()
        if len(self.args.row2) > 0:
            self.add_keyboard_row(self.args.row2 + "𝄞")
        if len(self.args.row1) > 0:
            self.add_keyboard_row(self.args.row1)

    def add_keyboard_row(self, chars):
        char_list = list(c for c in chars)
        key_width = 1
        keyboard_row = tk.PanedWindow(self.master)
        self.last_char_timestamp = time.time()
        for c in char_list:
            button = tk.Button(keyboard_row,
                               #background="black",
                               text=c, width=key_width, relief="raised", height=1,
                               font=self.key_font,
                               command=partial(self.keyboard_click, c))
            self.keys[c] = button
            button.pack(side=tk.BOTTOM, expand=False)
            keyboard_row.add(button)

        keyboard_row.pack(fill=tk.BOTH, side=tk.BOTTOM, expand=False)

    def play_word(self, w):
        if w.lower() == "камаз":
            self.play_file("kamaz01.mp3")

    def keyboard_click(self, char):
        if char == '𝄞':
            s = self.text_widget.get(1.0, tk.END).strip("\n")
            self.play_word(s)
        elif char == ' ':  #backspace
            s = self.text_widget.get(1.0, tk.END).strip("\n")
            if len(s) > 0:
                #self.text_widget.delete(float(len(s)), tk.END)
                self.text_widget.delete(1.0, tk.END)
                self.text_widget.insert(tk.END, s[:-1])
                s1 = self.text_widget.get(1.0, tk.END).strip("\n")
            self.play_file("key_sound.wav")
        else:
            ts = time.time()
            if ts - self.last_char_timestamp < 1 and char == self.last_char:
                return
            self.last_char_timestamp = ts
            self.last_char = char
            self.text_widget.insert(tk.END, char)
            self.play_file("key_sound.wav")

    def play_file(self, file_path):
        file_path = os.path.join(os.path.dirname(__file__), "sound", file_path)
        if self.player is not None:
            self.player.stop()
        self.player = vlc.MediaPlayer(file_path)
        self.player.play()

    def main_loop(self):
        self.master.mainloop()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--not-fullscreen", dest='fullscreen', default=True, action="store_false")
    parser.add_argument("--row1", dest='row1', default='')
    parser.add_argument("--row2", dest='row2', default='МПАВЯЛОНЕ𝄞 ')
    parser.add_argument("--font-size", dest='font_size', default=40, type=int)
    return parser.parse_args()


if __name__ == "__main__":
    game = TVanyaOffice()
    game.main_loop()
