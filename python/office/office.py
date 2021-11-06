import os
import sys
import argparse
import tkinter as tk
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
        self.font = ("DejaVu Sans Mono", self.args.font_size)

        self.text_widget = tk.Text(self.master,
                                   width=100,
                                   height=1,
                                   font=self.font)
        self.text_widget.pack(side=tk.TOP)

        self.keyboard = tk.PanedWindow(self.master)
        self.keys = dict()
        self.chars = ['М', 'П', 'А', 'В', 'Я', 'Л', 'О', 'Н', 'Е', ' ']
        #key_width = int(self.main_wnd_width / len(self.chars))
        key_width = 1
        for c in self.chars:
            button = tk.Button(self.keyboard, text=c, width=key_width, relief="raised", height=1, font=self.font,
                               command=partial(self.keyboard_click, c))
            self.keys[c] = button
            button.pack(side=tk.BOTTOM, expand=False)
            self.keyboard.add(button)

        self.keyboard.pack(fill=tk.BOTH, side=tk.BOTTOM, expand=False)

    def keyboard_click(self, char):
        if char == ' ':
            s = self.text_widget.get(1.0, tk.END).strip("\n")
            if len(s) > 0:
                #self.text_widget.delete(float(len(s)), tk.END)
                self.text_widget.delete(1.0, tk.END)
                self.text_widget.insert(tk.END, s[:-1])
                s1 = self.text_widget.get(1.0, tk.END).strip("\n")
                pass
        else:
            self.text_widget.insert(tk.END, char)
        self.play_file(os.path.join(os.path.dirname(__file__), "key_sound.wav"))

    def play_file(self, file_path):
        if self.player is not None:
            self.player.stop()
        self.player = vlc.MediaPlayer(file_path)
        self.player.play()

    def main_loop(self):
        self.master.mainloop()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--not-fullscreen", dest='fullscreen', default=True, action="store_false")
    parser.add_argument("--font-size", dest='font_size', default=40, type=int)
    return parser.parse_args()


if __name__ == "__main__":
    game = TVanyaOffice()
    game.main_loop()
