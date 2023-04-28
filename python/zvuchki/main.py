import sys

import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains, ActionBuilder
from car_brands import CARS, URLS

import os
import argparse
import tkinter as tk
import tkinter.font as tkFont
import time
import vlc
from functools import partial
import json


sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logging_wrapper import setup_logging


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


class TBrowser:
    def __init__(self):
        self.browser = None
        self.cache_path = "search_request_cache.txt"
        self.all_requests = dict()
        if os.path.exists(self.cache_path):
            with open(self.cache_path) as inp:
                s = inp.read()
                if len(s) > 0:
                    self.all_requests = json.loads(s)

    def init_chrome(self):
        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        options.add_argument("enable-automation")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-browser-side-navigation")
        options.add_argument("--disable-gpu")
        self.browser = webdriver.Chrome(options=options)
        self.browser.set_page_load_timeout(10)
        self.browser.set_script_timeout(30)
        self.browser.set_page_load_timeout(60)
        self.browser.set_script_timeout(30)
        self.browser.set_window_position(0, 0)

    def init_firefox(self):
        opts =  webdriver.FirefoxOptions()
        #opts.log.level = "trace"
        self.browser = webdriver.Firefox(
                options=opts,
                executable_path='/snap/bin/geckodriver',
                #service_log_path=os.path.join(os.path.dirname(__file__), 'geckodriver.log')
                    service_log_path=None
                )

    def start_browser(self):
        #self.init_firefox()
        self.init_chrome()

    def close_browser(self):
        self.browser.close()
        time.sleep(1)
        self.browser.quit()

    def mouse_click(self, x, y):
        self.browser.execute_script('el = document.elementFromPoint({}, {}); el.click();'.format(x, y))

    def send_ctrl_end(self):
        ActionChains(self.browser) \
            .key_down(Keys.CONTROL) \
            .key_down(Keys.END) \
            .perform()

    def send_ctrl_home(self):
        ActionChains(self.browser) \
            .key_down(Keys.CONTROL) \
            .key_down(Keys.HOME) \
            .perform()

    def navigate(self, url):
        try:
            self.browser.get(url)
        except selenium.common.exceptions.TimeoutException as e:
            print(e)
            time.sleep(2)

    def play_youtube(self, url, max_duration):
        try:
            time.sleep(1)
            print("play {}".format(url))
            self.navigate(url)

            print ("sleep 3 sec")
            time.sleep(3)

            #self.send_ctrl_end()
            #time.sleep(1)

            #self.send_ctrl_home()
            #time.sleep(1)

            element = self.browser.switch_to.active_element
            time.sleep(1)

            #print("send Tab")
            #element.send_keys(Keys.TAB)
            #time.sleep(1)

            #self.browser.execute_script("window.scrollTo(0, 100)")
            #time.sleep(1)

            #element = self.browser.switch_to.active_element
            #time.sleep(1)
            #element = self.browser.find_elements('body')

            print ("send к")
            element.send_keys("k")
            time.sleep(1)

            time.sleep(0.5)
            print ("send f")
            element.send_keys("f")

            #time.sleep(0.5)
            #print ("send p")
            #element.send_keys("p")

            print("max_duration = {}".format(max_duration))
            time.sleep(max_duration)
            return True
        except WebDriverException as exp:
            print("exception: {}".format(exp))
            return False

    def _parse_serp(self):
        search_results = []
        self.send_ctrl_end()
        time.sleep(1)
        self.send_ctrl_home()
        time.sleep(1)
        for element in self.browser.find_elements(By.TAG_NAME, "a"):
            url = element.get_attribute("href")
            if url is not None and url != '#' and url.startswith('http'):
                if "youtube" in url:
                    if url not in search_results:
                        search_results.append(url)
        return search_results

    def send_request(self, search_engine_request):
        self.browser.get("https://www.google.ru/videohp?hl=ru")
        time.sleep(3)
        element = self.browser.switch_to.active_element
        element.send_keys(search_engine_request)
        time.sleep(1)
        element.send_keys(Keys.RETURN)
        time.sleep(3)
        search_results = self._parse_serp()
        self.all_requests[search_engine_request] = search_results
        if search_results:
            with open(self.cache_path, "w") as outp:
                json.dump(self.all_requests, outp, ensure_ascii=False, indent=4)
        return search_results


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
        self.key_font_umlaut = tkFont.Font(family="DejaVu Sans Mono", size=self.args.font_size - 20)
        self.master.grid_columnconfigure((0, 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12 ), weight=1)
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_rowconfigure((1, 2, 3), weight=2)

        self.text_widget = tk.Text(self.master,
                                   width=100,
                                   height=1,
                                   font=self.editor_font)
        self.text_widget.grid(column=0,  columnspan=13)

        self.keys = dict()
        self.last_char = None
        self.last_char_timestamp =   time.time()
        self.keyboard_type = TKeyboardType.ABC
        #self.init_sample_abc_keyboard()
        self.init_all_abc_keyboard()
        self.left_queries = set(URLS.keys())

    def init_sample_abc_keyboard(self):
        #self.add_keyboard_row(1, "БЦХ123" + TChars.PLAY + TChars.BACKSPACE )
        self.add_keyboard_row(1, "БЦХ1234" + TChars.PLAY + TChars.BACKSPACE)
        self.add_keyboard_row(2, "ИКТЗГУРДСФЖ")
        self.add_keyboard_row(3, "МПАВЯЛОНЕШЬ")

    def init_all_abc_keyboard(self):
        self.add_keyboard_row(1, "123456780" + TChars.BACKSPACE)
        self.add_keyboard_row(2, "ЙЦУКЕНГШЩЗХ")
        self.add_keyboard_row(3, "ФЫВАПРОЛДЖЭ")
        self.add_keyboard_row(4, "ЯЧСМИТЬБЮ"+TChars.PLAY)

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
            if char == TChars.PLAY:
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

    def get_url_video_from_google(self, car, position, add_query):
        request = "{} {}".format(car, add_query)
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
        for try_index in range(2):
            browser = TBrowser()
            browser.start_browser()
            res = browser.play_youtube(url, seconds)
            browser.close_browser()
            if res:
                break

    def play_test_drive(self, car_and_pos, add_seconds):
        seconds = 300 + add_seconds
        #seconds = 10 + add_seconds
        add_query = None
        if car_and_pos[-1] == 'Т':
            add_query = "тест драйв от первого лица"
        elif car_and_pos[-1] == 'З':
            add_query = "звук двигателя"
        elif car_and_pos[-1] == 'Э':
            add_query = "эксплуатация"
        else:
            return False
        car_and_pos = car_and_pos[:-1]
        if len(car_and_pos) == 0 or not car_and_pos[-1].isdigit():
            return False
        position = int(car_and_pos[-1])
        car = car_and_pos[:-1]
        if car.lower() not in CARS:
            return False
        url = self.get_url_video_from_google(car, position, add_query)
        self.play_youtube_video(url, seconds)
        return True

    def play_request(self, request):
        add_sec = 0
        if len(request) > 2 and request[-2:].upper() == "ДД":
            add_sec = 240
            request = request[:-2]
        if len(request) > 1 and request[-1].upper() == "Д" and request[-2].isdigit():
            add_sec = 120
            request = request[:-1]
        if len(request) > 2 and request[-1].upper() == "Д" and (request[-2].upper()  in  'ТЗ') and request[-3].isdigit():
            add_sec = 120
            request = request[:-1]
        key = request.lower()
        if key not in URLS:
            return self.play_test_drive(request, add_sec)
        url, timeout = URLS[key]
        if self.args.max_play_seconds < timeout:
            timeout = self.args.max_play_seconds
        self.play_youtube_video(url, timeout + add_sec)
        if key in self.left_queries:
            self.left_queries.remove(key)
        self.print_tasks()
        return True

    def keyboard_click(self, char):
        if char == ' ':
            pass
        elif char == TChars.PLAY:
            s = self.text_widget.get(1.0, tk.END).strip("\n")
            if self.play_request(s):
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
        s = list(self.left_queries)
        s.sort()
        print(">>>> " + str(s))

    def main_loop(self):
        self.print_tasks()
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
    #b = TBrowser()
    #b.start_browser()
    #b.play_youtube('https://www.youtube.com/watch?v=NaiCfIcutbM', 10)




#победа и еще что-то, подумать о лайках и свободном поиске.
# музыкальный редактор, латинские буквы, диезы и бемоли, цифры обозначают октаву, длительность стрелками
# рисуем https://lilypond.org/doc/v2.23/Documentation/notation/direction-and-placement
#  для нее есть https://pypi.org/project/abjad/
# ваня вводит мелодию буквами, цифры и
# поиск в youtube