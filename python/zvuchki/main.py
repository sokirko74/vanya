from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException

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


class TKeyboardType:
    ABC = 1
    DIGITS = 2


class TChars:
    BACKSPACE = '⌫'
    PLAY = '𝄞'


URLS = {
    'зил1': ('https://www.youtube.com/watch?v=DyiqVFVJbYg', 70),
    'камаз1': ('https://www.youtube.com/watch?v=EJO5XRMUTgk', 70),
    'урал1': ('https://www.youtube.com/watch?v=INehuQl3LRo', 120),
    'газ1': ('https://www.youtube.com/watch?v=LBvGCU-eToc', 70),
    'даф1': ('https://www.youtube.com/watch?v=gN4wzPXleCY', 70),
    'скания1': ('https://www.youtube.com/watch?v=5FC-mepd7TI', 70),
    'нива1': ('https://www.youtube.com/watch?v=uDlqz42c9Ao', 44),
    'лиаз1': ('https://www.youtube.com/watch?v=Tvrtn_47bGA', 70),
    'ситроен1': ('https://www.youtube.com/watch?v=xrkoVUDsoBQ', 36),
    'пила1': ('https://www.youtube.com/watch?v=qHKfd-vRdOI', 70),
    'форд1': ('https://www.youtube.com/watch?v=Gt2VJEOuGKY', 100),
    'порш1': ('https://www.youtube.com/watch?v=_JaBoMgM4Y4', 80),
    'шевроле1': ('https://www.youtube.com/watch?v=6-GQFNC83DA', 130),
    'кот1': ('https://www.youtube.com/watch?v=TjmOWZ3y9gg', 60),
    'лада1': ('https://www.youtube.com/watch?v=sTDneAKEzQY', 53),
    'кия1': ('https://www.youtube.com/watch?v=U5eVplyAkto', 90),
    'танк1': ('https://www.youtube.com/watch?v=DyxdDR79a-0', 55),
    'танк2': ('https://www.youtube.com/watch?v=_CGLanOPwnw', 70),
    'буханка1': ('https://www.youtube.com/watch?v=5d8xdjQ8ma8', 90),
    'смарт1': ('https://www.youtube.com/watch?v=PxP2dq7nGwE', 90),
    'субару1': ('https://www.youtube.com/watch?v=EhQ0r9caVOM', 90),
    'баран1':('https://www.youtube.com/watch?v=vlvbkOhKFmw', 90),
    'петух1':('https://www.youtube.com/watch?v=CB7awpjMMkc', 90),
    "шум1": ('https://www.youtube.com/watch?v=ukZYP5Dy43E', 180),
    "шум2": ('https://www.youtube.com/watch?v=FgOg6aYqASY', 180),
    "форд2":('https://www.youtube.com/watch?v=yAYIZ2xMuFU', 120),
    'волга1':('https://www.youtube.com/watch?v=uvCxZ-Kv1q4', 31),
    'волга2':('https://www.youtube.com/watch?v=nw_BiXi4M8Y', 39),
    'утка1': ('https://www.youtube.com/watch?v=hw1sdm3M-CU',110),
    'слон1': ('https://www.youtube.com/watch?v=MW0l_3xhSXw', 120),
    'хонда1':('https://www.youtube.com/watch?v=eDjLovtcXW8', 120),
    'деу1': ('https://www.youtube.com/watch?v=cBBD74xuMKk', 60),
    'сааб1': ('https://www.youtube.com/watch?v=-AsOG3nYJ9A', 60),
    'волга21':('https://www.youtube.com/watch?v=WR8TovF4A4U', 120),
    'мазда1': ('https://www.youtube.com/watch?v=GmiKzouALk8', 120),
    'ауди1': ('https://www.youtube.com/watch?v=VoWb_lD_bIc', 120),
    'мерседес1': ('https://www.youtube.com/watch?v=ai-Gc2a8KWY', 50),
    'белаз1': ('https://www.youtube.com/watch?v=Tb2IwXdagHc', 180),
     'краз1': ('https://www.youtube.com/watch?v=-S6CdlFUJrU', 120),
    'икарус1':('https://www.youtube.com/watch?v=uOJVBAuqfLY', 45),
    'ман1': ('https://www.youtube.com/watch?v=7LGh8PAG4BI', 180),
    'студебекер1': ('https://www.youtube.com/watch?v=3A2QXiHcdQQ', 70),
    'паровоз1': ('https://www.youtube.com/watch?v=Sgkq1Kiz80I', 240),
    'рено1': ('https://www.youtube.com/watch?v=sBmpXCXjohI', 56),
    'рено2': ('https://www.youtube.com/watch?v=IU9WAUV5n3s',  57),
    'лексус1': ('https://www.youtube.com/watch?v=zkZSfGeD6ko', 120),
    'трактор1': ('https://www.youtube.com/watch?v=FQqKfhKNDSE', 180),
    'станок1':('https://www.youtube.com/watch?v=ewCaidVH4MA', 180),
    'форд3': ('https://www.youtube.com/watch?v=bQGBUaW88E4', 180),
    'шкода1': ('https://www.youtube.com/watch?v=MY6liZv6t2Y', 180),
    'фиат1':('https://www.youtube.com/watch?v=QBxSnSIqCaQ', 120),
    'татра1':('https://www.youtube.com/watch?v=Tget7hNlVTY',80),
    'супер1': ('https://www.youtube.com/watch?v=Rg6awBglzGU', 240),
    'таврия1': ('https://www.youtube.com/watch?v=6dUwQ3k7XRQ',130),
    'инфинити1': ('https://www.youtube.com/watch?v=0-kalBhe-qo',180),
    'скания2':('https://www.youtube.com/watch?v=6zLmMU1Gc0c', 120),
    'вертолет1':('https://www.youtube.com/watch?v=XHkNgZ5KAg0', 150),
    'телефон1':('https://www.youtube.com/watch?v=iHgJLSvpvp8', 300),
    'газ2':('https://www.youtube.com/watch?v=KmiA9_GQQt8', 59),
    'танк3':('https://www.youtube.com/watch?v=pYsQy3mHV10', 60),
    'туарег1':('https://www.youtube.com/watch?v=VO_6bVYur_w', 180),
    'девятка1':('https://www.youtube.com/watch?v=lRKPqIkOj1Q', 80),
    'гранта1': ('https://www.youtube.com/watch?v=p8mUKHigEbQ&t=19s', 150),
    'ларгус1': ('https://www.youtube.com/watch?v=n0LM6QaxDyg', 55),
    'ягуар1': ('https://www.youtube.com/watch?v=Vx0b5-R1U5U', 110),
    'лендровер1':('https://www.youtube.com/watch?v=0yxCr8LAEa4', 55),
    'тигуан1': ('https://www.youtube.com/watch?v=kcBVqet7yI8', 70),
   'лаз1': ('https://www.youtube.com/watch?v=bkqk9YvrmGc', 180),
  'рио1': ('https://www.youtube.com/watch?v=P7_n0Q1Xvu0&t=29s', 220),
  'урал2':('https://www.youtube.com/watch?v=rzgi1tl59Hg', 82),
  'гонка1': ('https://www.youtube.com/watch?v=hetIqjWHBu8',  200),
  'лодка1': ('https://www.youtube.com/watch?v=BmbSMZbgkOg', 180),
  'масами1': ('https://www.youtube.com/watch?v=-gzBqayDmJ8',  240),
    'пыхтелки1': ('https://www.youtube.com/watch?v=-BE476MvO_g', 240),
    'лодка2':('https://www.youtube.com/watch?v=HwF0HbG_wYE', 180),
    'лодка3': ('https://www.youtube.com/watch?v=wvr5ESGkYDo', 120),
    'мотособака1':('https://www.youtube.com/watch?v=zpPQKIveCXk',180),
   'миникупер1': ('https://www.youtube.com/watch?v=SLjw4jLf1Kg', 100),
  'бобкет1': ('https://www.youtube.com/watch?v=OJ27XkuW6uw', 180),
  'кировец1':('https://www.youtube.com/watch?v=7NY1c_RrlRE', 120),
  'метеор1': ('https://www.youtube.com/watch?v=7pmx-b336Ik',  60),

  'лада2': ('https://www.youtube.com/watch?v=l2rglKquGvw', 120),
  'лада3': ('https://www.youtube.com/watch?v=C5pgJqV-jI0', 100),
  'станок2':('https://www.youtube.com/watch?v=9AlIEDSG_6g',  180),
  'самолет1': ('https://www.youtube.com/watch?v=RXVJxX9gG7g', 120)  
}


class TZvuchki(tk.Frame):
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
            self.main_wnd_width = 1600
            self.main_wnd_height = 800
            self.master.geometry("{}x{}".format(self.main_wnd_width, self.main_wnd_height))
        self.player = None
        self.editor_font = ("DejaVu Sans Mono", self.args.font_size+20)
        self.key_font = tkFont.Font(family="DejaVu Sans Mono", size=self.args.font_size)
        self.master.grid_columnconfigure((0, 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12 ), weight=1)
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_rowconfigure((1, 2, 3), weight=2)

        self.text_widget = tk.Text(self.master,
                                   width=100,
                                   height=1,
                                   font=self.editor_font)
        self.text_widget.grid(column=0, columnspan=13)

        self.keys = dict()
        self.last_char = None
        self.last_char_timestamp =   time.time()
        self.keyboard_type = TKeyboardType.ABC
        self.init_abc_keyboard()
        self.left_queries = set(URLS.keys())

    def init_abc_keyboard(self):
        self.add_keyboard_row(1, "123БХЦ" + TChars.PLAY+ TChars.BACKSPACE )
        self.add_keyboard_row(2, "ИКТЗГУРДСФ")
        self.add_keyboard_row(3, "МПАВЯЛОНЕШ")

    def add_keyboard_row(self, row_index, chars):
        self.last_char_timestamp = time.time()
        column_index = 0
        for c in chars:
            colspan = 1
            width = 1
            background = None
            if c == TChars.PLAY:
                colspan *= 2
                width *= 2

            if c == TChars.BACKSPACE:
                colspan *= 3
                width *= 3
                background = "red"

            button = tk.Button(self.master,
                               background=background,
                               text=c, width=width, relief="raised", height=1,
                               font=self.key_font,
                               command=partial(self.keyboard_click, c))
            self.keys[c] = button
            button.grid(column=column_index, row=row_index, columnspan=colspan, padx=0, pady=2)
            column_index += colspan

    def play_youtube(self, url, max_duration):
        try:
            browser = webdriver.Chrome()
            browser.get(url)

            WebDriverWait(browser, 15).until(EC.element_to_be_clickable(
                (By.XPATH, "//button[@aria-label='Play']"))).click()
            browser.maximize_window()
            time.sleep(1)
            element = browser.switch_to.active_element
            element.send_keys("f")
            time.sleep(max_duration)
            browser.close()
            time.sleep(1)
            browser.quit()
        except WebDriverException as exp:
            pass

    def play_word(self, w):
        key = w.lower()
        u, t = URLS.get(key, (None, None))
        if u is not None:
            if  self.args.max_play_seconds < t:
                t = self.args.max_play_seconds
            self.play_youtube(u, t)
            if key in self.left_queries:
                self.left_queries.remove(key)
            self.print_tasks()
            return True
        return False

    def keyboard_click(self, char):
        if char == ' ':
            pass
        elif char == TChars.PLAY:
            s = self.text_widget.get(1.0, tk.END).strip("\n")
            if self.play_word(s):
                self.text_widget.delete(1.0, tk.END)
        elif char == TChars.BACKSPACE:  #backspace
            s = self.text_widget.get(1.0, tk.END).strip("\n")
            if len(s) > 0:
                #self.text_widget.delete(float(len(s)), tk.END)
                self.text_widget.delete(1.0, tk.END)
                self.text_widget.insert(tk.END, s[:-1])
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

    def print_tasks(self):
        print(">>>> " + str(self.left_queries))

    def main_loop(self):
        self.print_tasks()
        self.master.mainloop()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--not-fullscreen", dest='fullscreen', default=True, action="store_false")
    parser.add_argument("--row1", dest='row1', default='')
    parser.add_argument("--row2", dest='row2', default='МПАВЯЛОНЕ𝄞 ')
    parser.add_argument("--font-size", dest='font_size', default=40, type=int)
    parser.add_argument("--max-play-seconds", dest='max_play_seconds', default=120, type=int)
    return parser.parse_args()


if __name__ == "__main__":
    game = TZvuchki()
    game.main_loop()



#  максимизация экрана
# backspace  на 3 линию
#  не менять размер кнопок
#жигули, кия,лада
