import os
import sys
import argparse
import tkinter as tk
import threading
import time

from mingus.containers import Note, Bar
import pygame
import random
from mingus.midi import fluidsynth
sys.path.append(os.path.join(os.path.dirname(__file__), '../utils'))
from logging_wrapper import setup_logging
from tkinter.messagebox import askyesno


MAX_WORD_FAIL_COUNT = 2


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (228, 155, 0)

PIANO = 1
ORGAN = 20
SITAR = 105

START_OCTAVE = 2
KEY_2_NOTE = {
    'Й': ('C', START_OCTAVE + 0, ORGAN),
    'Ц': ('D', START_OCTAVE + 0, ORGAN),
    'У': ('E', START_OCTAVE + 0, ORGAN),
    'К': ('F', START_OCTAVE + 0, ORGAN),
    'Е': ('G', START_OCTAVE + 0, ORGAN),
    'Н': ('A', START_OCTAVE + 0, ORGAN),
    'Г': ('B', START_OCTAVE + 0, ORGAN),

    'Ш': ('C', START_OCTAVE + 1, ORGAN),
    'Щ': ('D', START_OCTAVE + 1, ORGAN),
    'З': ('E', START_OCTAVE + 1, ORGAN),
    'Х': ('F', START_OCTAVE + 1, ORGAN),
    'Ъ': ('G', START_OCTAVE + 1, ORGAN),
    'Ф': ('A', START_OCTAVE + 1, PIANO),
    'Ы': ('B', START_OCTAVE + 1, PIANO),

    'В': ('C', START_OCTAVE + 2, PIANO),
    'А': ('D', START_OCTAVE + 2, PIANO),
    'П': ('E', START_OCTAVE + 2, PIANO),
    'Р': ('F', START_OCTAVE + 2, PIANO),
    'О': ('G', START_OCTAVE + 2, PIANO),
    'Л': ('A', START_OCTAVE + 2, PIANO),
    'Д': ('B', START_OCTAVE + 2, PIANO),

    'Ж': ('C', START_OCTAVE + 3,  PIANO),
    'Э': ('D', START_OCTAVE + 3, PIANO),
    'Я': ('E', START_OCTAVE + 3, PIANO),
    'Ч': ('F', START_OCTAVE + 3, PIANO),
    'С': ('G', START_OCTAVE + 3, PIANO),
    'М': ('A', START_OCTAVE + 3, PIANO),
    'И': ('B', START_OCTAVE + 3, PIANO),

    'Т': ('C', START_OCTAVE + 4, PIANO),
    'Ь': ('D', START_OCTAVE + 4, PIANO),
    'Б': ('E', START_OCTAVE + 4, PIANO),
    'Ю': ('F', START_OCTAVE + 4, PIANO),

}

CORRECT_CHAR_INSTRUMENT = PIANO
ACCORD_INSTRUMENT = ORGAN
ERROR_CHAR_INSTRUMENT = SITAR


class TextCleaner (threading.Thread):
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.parent = parent

    def run(self):
        while self.parent.is_running:
            self.parent.check_word()
            time.sleep(1)


class TVanyaOffice(tk.Frame):
    def __init__(self, master=None):
        self.args = parse_args()
        self.logger = setup_logging("office.log")
        self.left_offset = 80
        self.is_running = True
        self.print_victory = False
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
        self.write_font = ("DejaVu Sans Mono", self.args.write_font_size)
        self.read_font = ("DejaVu Sans Mono", self.args.read_font_size)
        self.label_font = ("DejaVu Sans Mono", 100)
        self.goal_words = list()
        self.read_goal_words()

        self.create_widgets()
        self.new_game()
        self.last_word = ""
        self.fail_count = 0
        self.victory_count = 0
        self.master.bind('<KeyPress>', self.keyboard_click)
        fluidsynth.init('/usr/share/sounds/sf2/default-GM.sf2', 'alsa')
        fluidsynth.main_volume(1, 10000)
        self.last_char = None
        fluidsynth.set_instrument(1, 105)
        #note = Note("C-5")
        note = Note().from_hertz(460)
        fluidsynth.play_Note(note)
        self.text_cleaner_thread = TextCleaner(self)
        #self.play_file("word_fail.wav")

    def read_goal_words(self):
        path = self.args.word_file
        if path is None:
            path = os.path.join(os.path.dirname(__file__), "nouns6.txt")
        else:
            if not os.path.exists(path):
                path = os.path.join(os.path.dirname(__file__), path)
        #path = os.path.join(os.path.dirname(__file__), "goal_words.txt")
        #path = os.path.join(os.path.dirname(__file__), "nouns5.txt")
        #path = os.path.join(os.path.dirname(__file__), "english2.txt")
        with open(path) as inp:
            for i in inp:
                self.goal_words.append(i.strip())

    def create_widgets(self):
        frame1 = tk.Frame(self.master)
        frame1.pack(side=tk.TOP)

        self.goal_word_widget = tk.Text(
            frame1, width=15, font=self.read_font, height=1)
        self.goal_word_widget.pack(side=tk.LEFT)

        frame2 = tk.Frame(self.master)
        frame2.pack(side=tk.TOP)
        self.text_widget = tk.Text(frame2,
                                   width=15,
                                   height=1,
                                   font=self.write_font)
        self.text_widget.pack(side=tk.LEFT)
        self.text_widget.focus_set()

        frame3 = tk.Frame(self.master)
        frame3.pack(side=tk.TOP)
        self.victory_count_label = tk.Label(frame3, text="0", font=self.label_font,
                                            bg="misty rose")
        self.victory_count_label.pack(side=tk.LEFT)

        self.log_widget = tk.Text(frame3, width=100, height=3)
        self.log_widget.pack(side=tk.LEFT)

        self.fail_count_label = tk.Label(frame3, text="0", font=self.label_font, bg="light green")
        self.fail_count_label.pack(side=tk.LEFT)

    def is_arithmetic_task(self, task):
        return task.endswith(' = ')

    def get_goal_word(self):
        try:
            s =  self.goal_word_widget.get("1.0", tk.END).strip("\n")
            if self.is_arithmetic_task(s):
                return str(eval(s[:-3]))
            return s
        except Exception as exp:
            self.logger.error(exp)
            raise

    def new_game(self):
        last_goal = self.get_goal_word()
        words = list(self.goal_words)
        if last_goal in words:
            words.remove(last_goal)
        new_goal = random.choice(words)
        if random.random() > 1.0 - self.args.math_prob:
            a1 = random.randint(4, 30)
            a2 = random.randint(11, 19)
            new_goal = "{} + {} = ".format(a1, a2)
        #w = "ЖУК"
        self.goal_word_widget.delete("1.0", tk.END)
        self.goal_word_widget.insert("1.0", new_goal)

        self.fail_count = 0
        self.fail_count_label.config(text=str(self.fail_count))

    def print_to_log(self, m):
        self.log_widget.insert(tk.END, m)
        self.log_widget.see(tk.END)
        self.logger.info(m)

    def victory(self):
        goal_word = self.get_goal_word()
        self.text_widget.update()
        self.victory_count += 1
        self.victory_count_label.config(text=str(self.victory_count))
        self.print_to_log("victory count = {}\n".format(self.victory_count))
        # self.play_file("victory.wav")
        if goal_word.isdigit():
            self.play_file('fanfare.wav', 30)
            time.sleep(1)
        elif goal_word.isalpha() and goal_word.isascii():
            self.play_file('fanfare.wav', 30)
            time.sleep(1)
        else:
            b = Bar()
            notes = list()
            channel = 1
            for char in goal_word:
                if char in KEY_2_NOTE:
                    note, octave, instr = KEY_2_NOTE[char]
                    fluidsynth.set_instrument(channel, instr)
                    notes.append(Note(note, octave, channel=channel))
                    channel += 1
            b.place_notes(notes, 1)
            fluidsynth.stop_everything()
            fluidsynth.play_Bar(b)
            time.sleep(3)
        self.text_widget.delete('1.0', tk.END)
        if self.victory_count == self.args.victory_count:
            self.play_file('victory.wav', 50)
            self.master.grab_set()  # Prevent clicking root while messagebox is open
            ans = askyesno('', 'Выйти? Press Yes / No')
            if ans:
                self.quit()
            else:
                self.victory_count = 0
        self.new_game()


    def check_word(self):
        goal_word = self.get_goal_word()
        input_word = self.text_widget.get(1.0, tk.END).strip().upper()
        for i in range(len(goal_word)):
            if i < len(input_word) and goal_word[i] != input_word[i].upper():
                self.text_widget.delete('1.0', tk.END)
                self.text_widget.insert('1.0', goal_word[:i])
                break

    def wrong_key(self, event):
        self.fail_count += 1
        self.fail_count_label.config(text=str(self.fail_count))
        self.print_to_log("fail count = {}\n".format(self.fail_count))
        if self.fail_count > MAX_WORD_FAIL_COUNT:
            self.play_file("word_fail.wav")
            time.sleep(1)
            self.new_game()
        else:
            self.play_file("key_fail.wav")
            self.print_to_log("bad key event {}\n".format(event))

    def keyboard_click(self, event):
        if len(event.char) != 1:
            return
        if self.last_char == event.char:
            return
        if ord(event.char) <= 32:
            return
        new_word = self.text_widget.get(1.0, tk.END).strip().upper()
        goal_word = self.get_goal_word()
        if goal_word == new_word:
            self.victory()
        elif not goal_word.startswith(new_word):
            self.wrong_key(event)

    def play_file(self, file_path, volume=30):
        file_path = os.path.join(os.path.dirname(__file__), "sound", file_path)
        assert os.path.exists(file_path)
        if self.audioplayer is not None:
            self.audioplayer.stop()

        self.audioplayer = pygame.mixer.Sound(file_path)
        self.audioplayer.set_volume(volume)
        self.audioplayer.play()

    def main_loop(self):
        self.text_cleaner_thread.start()
        self.master.mainloop()
        self.is_running = False
        self.text_cleaner_thread.join(2)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--not-fullscreen", dest='fullscreen', default=True, action="store_false")
    parser.add_argument("--write-font-size", dest='write_font_size', default=200, type=int)
    parser.add_argument("--read-font-size", dest='read_font_size', default=200, type=int)
    parser.add_argument("--victory-count", default=20, type=int)
    parser.add_argument("--math-prob", default=0.2, type=float)
    parser.add_argument("--word-file")
    return parser.parse_args()


if __name__ == "__main__":
    pygame.mixer.init()
    game = TVanyaOffice()
    game.main_loop()

