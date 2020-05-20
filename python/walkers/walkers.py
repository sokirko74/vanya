# -*- coding: utf-8 -*-
import os
import sys
import logging
import tkinter as tk
import argparse
import bluetooth

from bluetooth_switches import TBluetoohSwitchesThread
MAIN_APPLICATION = None
BLUETOOTH_KOLESO = None
TK_ROOT = tk.Tk()


def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh = logging.FileHandler("koleso.log",  mode='a')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    root.addHandler(fh)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    root.addHandler(ch)
    return root

def search_bluetooth_devices():
    devices = bluetooth.discover_devices(duration=20, lookup_names = True)
    return devices

def myquit():
    global BLUETOOTH_KOLESO
    BLUETOOTH_KOLESO.killed = True
    TK_ROOT.destroy()
    os.system("pkill ffplay")
    sys.exit(0)


class Application(tk.Frame):
    def __init__(self, logger, master=None):
        super().__init__(master)
        self.master = master
        self.logger = logger
        self.pack()
        self.folders = [x for x in os.listdir() if os.path.isdir(x)]
        self.songs = []
        self.logger.debug(self.folders)
        self.roll_over_folders = tk.IntVar()
        self.listbox = tk.Listbox(self.master)
        self.pack_widgets(self.folders)
        if len(self.folders) > 0:
            self.switch_folder_inner(0)
        self.set_to_last_song()
        self.current_folder_no = 0
        self.roll_over_folders = tk.IntVar()
        self.current_song = 0

    @staticmethod
    def shutup_command(self):
        os.system("pkill ffplay")

    def pack_widgets(self, folders):
        tk.Button(self, text=u"Заткнись", command=self.shutup_command).pack(side="left")
        tk.Button(self, text="QUIT", fg="red", command=myquit).pack(side="left")
        tk.Checkbutton(self.master, text="Roll over folders", variable=self.roll_over_folders).pack(side="top").select()
        self.listbox.pack()
        for folder in folders:
            self.listbox.insert(tk.END, folder)
        self.listbox.bind("<Double-Button-1>", self.switch_folder)
        self.listbox.bind('<<ListboxSelect>>', self.switch_folder)

    @staticmethod
    def play_file(self, filename):
        os.system("pkill ffplay")
        os.system('ffplay -hide_banner -loglevel panic -autoexit -nodisp {} &'.format(filename))

    def set_to_first_song(self):
        if len(self.songs) == 0:
            self.current_song = -1
        else:        
            self.current_song = 0

    def set_to_last_song(self):
        if len(self.songs) == 0:
            self.current_song = -1
        else:        
            self.current_song = len(self.songs) - 1

    def switch_song (self, is_forward):
        if is_forward:
            self.logger.debug("forward")
            self.current_song += 1
            if self.current_song >= len(self.songs):
                self.logger.debug("self.RollOverFolders=" + str(self.roll_over_folders))
                if self.roll_over_folders != 0:
                    if self.current_folder_no + 1 < len(self.folders):
                        self.switch_folder_inner(self.current_folder_no + 1)
                    else:
                        self.switch_folder_inner(0)
                self.set_to_first_song()

        else:
            self.logger.debug("backward")
            self.current_song -= 1
            if self.current_song < 0:
                if self.roll_over_folders != 0:
                    if self.current_folder_no > 0:
                        self.switch_folder_inner(self.current_folder_no - 1)
                    else:
                        self.switch_folder_inner(len(self.folders) - 1)
                self.set_to_last_song()

        self.logger.debug("set audio N {}".format(self.current_song))
        if self.current_song != -1:
            self.play_file(self.songs[self.current_song])
        else:
            self.logger.debug("no songs in folder " + self.folders[self.current_folder_no])

    def switch_folder_inner(self, folder_index):
        selg.logger.debug("switch to folder no {}".format(folder_index))
        self.current_folder_no = folder_index
        folder = self.folders[folder_index]
        self.logger.debug("read files from {}".format(folder))
        logging.debug(os.listdir(folder))
        self.songs = []
        for x in os.listdir(folder):
            f = os.path.join(folder, x)
            if f.endswith('mp3'):
                self.songs.append(f)
        self.logger.debug(self.songs)
        self.logger.debug("Number of Songs: " + str(len(self.songs)))
        self.listbox.selection_clear(0, tk.END)
        self.listbox.select_set(self.current_folder_no)
        
    def switch_folder(self, dummy):
        items = self.listbox.curselection()
        if len(items) == 0:
            return
        self.switch_folder_inner(items[0])


def switch_song_action(is_forward):
    global MAIN_APPLICATION
    MAIN_APPLICATION.switch_song(is_forward)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-devices", dest='list_devices', default=False, action="store_true")
    parser.add_argument("--mac-address", dest='mac_address', default='20:18:12:03:27:38')
    return parser.parse_args()


if __name__ == "__main__":
    logger = setup_logging()
    args = parse_args()
    if args.list_devices:
        print (search_bluetooth_devices())
        sys.exit(0)

    BLUETOOTH_KOLESO = TBluetoohSwitchesThread(logger, args.mac_address, switch_song_action)
    MAIN_APPLICATION = Application(logger, master=TK_ROOT)
    TK_ROOT.wm_protocol("WM_DELETE_WINDOW", myquit)
    MAIN_APPLICATION.play_file("intro.mp3")
    BLUETOOTH_KOLESO.start()

    try:
        MAIN_APPLICATION.mainloop()
    except Exception as e:
        print(str(e))
        myquit()
