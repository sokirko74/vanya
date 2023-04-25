import os
import sys
import argparse
import tkinter as tk
import threading
from tkinter import ttk
import time

from mingus.containers import Note, Bar
import vlc
import random
from mingus.midi import fluidsynth
sys.path.append(os.path.join(os.path.dirname(__file__), '../utils'))
from logging_wrapper import setup_logging


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (228, 155, 0)

GOAL_WORDS = [
    "АИСТ",
    "АРФА",
    "БУКА",
    "БУРЯ",
    "ВАНЯ",
    "ВЕРА",
    "ГОРН",
    "ГРАЧ",
    "ГРОМ",
    "ГРУЗ",
    "ДВОР",
    "ДОМ",
    "ДРУГ",
    "ЕФИМ",
    "ЖУК",
    "ЗАЯЦ",
    "ЗИМА",
    "КАША",
    "КИТ",
    "КИЯ",
    "КОРА",
    "КОТ",
    "КРАЙ",
    "КУБ",
    "КУМА",
    "КУСТ",
    "ЛАДА",
    "ЛАМА",
    "ЛЕНА",
    "ЛИСТ",
    "ЛОБ",
    "ЛОДКА",
    "ЛУК",
    "ЛЮДА",
    "МАМА",
    "МАРТ",
    "МОРЕ",
    "МУКА",
    "МУХА",
    "МЫЛО",
    "НЕГР",
    "НЕТ",
    "НИВА",
    "НОГА",
    "НОС",
    "НОТА",
    "ПАПА",
    "ПИЛА",
    "ПОЛ",
    "ПУЗО",
    "ПУЛЯ",
    "ПЫЛЬ",
    "РОВ",
    "РОЗА",
    "РОК",
    "РОСТ",
    "РОТ",
    "САД",
    "САША",
    "СИЛА",
    "СЛОН",
    "СОК",
    "СОЛЬ",
    "СОН",
    "СЫН",
    "СЫР",
    "ТОК",
    "ТОРТ",
    "ТРЮК",
    "ТУЧА",
    "ТЮК",
    "УСЫ",
    "ФАРА",
    "ХЛЕБ",
    "ЦЕНА",
    "ЦИРК",
    "ЧАЩА",
    "ШИНА",
    "ШАРФ",
    "ШУТ",
    "ЩУКА",
    "ЩЕКА",
    "ЭТАЖ",
    "ЮБКА",
    "ЯХТА"

]
START_OCTAVE = 2
KEY_2_NOTE = {
    'Й': ('C', START_OCTAVE + 0),
    'Ц': ('D', START_OCTAVE + 0),
    'У': ('E', START_OCTAVE + 0 ),
    'К': ('F', START_OCTAVE + 0),
    'Е': ('G', START_OCTAVE + 0),
    'Н': ('A', START_OCTAVE + 0),
    'Г': ('B', START_OCTAVE + 0),

    'Ш': ('C', START_OCTAVE + 1),
    'Щ': ('D', START_OCTAVE + 1),
    'З': ('E', START_OCTAVE + 1),
    'Х': ('F', START_OCTAVE + 1),
    'Ъ': ('G', START_OCTAVE + 1),
    'Ф': ('A', START_OCTAVE + 1),
    'Ы': ('B', START_OCTAVE + 1),

    'В': ('C', START_OCTAVE + 2),
    'А': ('D', START_OCTAVE + 2),
    'П': ('E', START_OCTAVE + 2),
    'Р': ('F', START_OCTAVE + 2),
    'О': ('G', START_OCTAVE + 2),
    'Л': ('A', START_OCTAVE + 2),
    'Д': ('B', START_OCTAVE + 2),

    'Ж': ('C', START_OCTAVE + 3),
    'Э': ('D', START_OCTAVE + 3),
    'Я': ('E', START_OCTAVE + 3),
    'Ч': ('F', START_OCTAVE + 3),
    'С': ('G', START_OCTAVE + 3),
    'М': ('A', START_OCTAVE + 3),
    'И': ('B', START_OCTAVE + 3),

    'Т': ('C', START_OCTAVE + 4),
    'Ь': ('D', START_OCTAVE + 4),
    'Б': ('E', START_OCTAVE + 4),
    'Ю': ('F', START_OCTAVE + 4),

}
CORRECT_CHAR_INSTRUMENT = 1 #пианино
#CORRECT_CHAR_INSTRUMENT = 20 #ОРГАН
ACCORD_INSTRUMENT = 20

#CORRECT_CHAR_INSTRUMENT = 40
ERROR_CHAR_INSTRUMENT = 105


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
        self.label_font = ("DejaVu Sans Mono", 140)
        self.create_widgets()
        self.new_game()
        self.last_word = ""
        self.fail_count = 0
        self.victory_count = 0
        self.master.bind('<KeyPress>', self.keyboard_click)
        #self.piano = mingus.containers.Piano()
        #fluidsynth.init("soundfont.SF2")
        fluidsynth.init('/usr/share/sounds/sf2/default-GM.sf2', 'alsa')
        fluidsynth.main_volume(1, 10000)
        self.last_char = None
        fluidsynth.set_instrument(1, 105)
        fluidsynth.play_Note(Note("C-5"))
        #b = Bar()
        #b.place_notes(['C', 'E', 'G'], 1)
        #fluidsynth.play_Bar(b)
        #pass
        self.text_cleaner_thread = TextCleaner(self)

    def create_widgets(self):
        frame1 = tk.Frame(self.master)
        frame1.pack(side=tk.TOP)


        self.goal_word = tk.StringVar()
        self.goal_words_combobox = tk.ttk.Combobox(frame1, width=5,
                 textvariable=self.goal_word,font=self.read_font)
        self.goal_words_combobox['values'] = tuple(GOAL_WORDS)
        self.goal_words_combobox.pack(side=tk.LEFT)



        frame2 = tk.Frame(self.master)
        frame2.pack(side=tk.TOP)
        self.text_widget = tk.Text(frame2,
                                   width=20,
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
        self.fail_count_label.config(text=str(self.fail_count))

    def print_to_log(self, m):
        self.log_widget.insert(tk.END, m)
        self.log_widget.see(tk.END)
        self.logger.info(m)

    def victory(self):
        goal_word = self.goal_word.get()
        self.text_widget.update()
        self.victory_count += 1
        self.victory_count_label.config(text=str(self.victory_count))
        self.print_to_log("victory count = {}\n".format(self.victory_count))
        # self.play_file("victory.wav")
        b = Bar()
        notes = [Note(*KEY_2_NOTE[i]) for i in goal_word]
        b.place_notes(notes, 1)
        fluidsynth.set_instrument(1, ACCORD_INSTRUMENT)
        fluidsynth.stop_everything()
        fluidsynth.play_Bar(b)
        time.sleep(5)
        self.text_widget.delete('1.0', tk.END)
        self.new_game()

    def play_char(self, ch, instrument):
        fluidsynth.set_instrument(1, instrument)
        n, o = KEY_2_NOTE[ch]
        note = Note(n, o)
        fluidsynth.stop_everything()
        fluidsynth.play_Note(note)

    def check_word(self):
        goal_word = self.goal_word.get()
        input_word = self.text_widget.get(1.0, tk.END).strip().upper()
        for i in range(len(goal_word)):
            if i < len(input_word) and goal_word[i] != input_word[i].upper():
                self.text_widget.delete('1.0', tk.END)
                self.text_widget.insert('1.0', goal_word[:i])
                break

    def keyboard_click(self, event):
        if len(event.char) != 1:
            return
        if self.last_char == event.char:
            return
        self.last_char = event.char
        new_word = self.text_widget.get(1.0, tk.END).strip().upper()
        goal_word = self.goal_word.get()
        if goal_word == new_word:
            self.victory()
            return
        instrument = None
        if goal_word.startswith(new_word):
            instrument = CORRECT_CHAR_INSTRUMENT
        else:
            if ord(event.char) >= 32:
                instrument = ERROR_CHAR_INSTRUMENT
                self.fail_count += 1
                self.fail_count_label.config(text=str(self.fail_count))
                self.print_to_log("fail count = {}\n".format(self.fail_count))
                if self.fail_count > 18:
                    self.new_game()

        if len(event.char) == 1 and event.char.upper() in KEY_2_NOTE:
            self.play_char(event.char.upper(), instrument)
            self.text_widget.update()
        else:
            self.play_file("key_fail.wav")
            self.print_to_log("ignore event {}\n".format(event))

    def play_file(self, file_path):
        file_path = os.path.join(os.path.dirname(__file__), "sound", file_path)
        if self.audioplayer is not None:
            self.audioplayer.stop()
        self.audioplayer = vlc.MediaPlayer(file_path)
        self.audioplayer.audio_set_volume(30)
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
    return parser.parse_args()


if __name__ == "__main__":
    game = TVanyaOffice()
    game.main_loop()

# повторный буквы игнорировать
# удалять все неправильное?