# -*- coding: utf-8 -*-
import os
import sys
import logging
import tkinter as tk
from functools import partial

from common.bluetooth_koleso import  TBluetoohKolesoThread
MAIN_APPLICATION = None
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


def myquit():
    READ_KOLESO_THREAD.killed = True
    TK_ROOT.destroy()
    os.system("pkill ffplay")
    sys.exit(0)

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.Folders = [x for x in os.listdir() if os.path.isdir(x)]
        self.Songs = []
        logging.debug (self.Folders)
        self.create_widgets(self.Folders)

        if len(self.Folders) > 0:
            self.switch_folder_inner(0)
        self.set_to_last_song()
        self.current_folder_no

    def shutup_command(self):
        os.system("pkill ffplay")
        
    def create_widgets(self, folders):

        self.shutup  = tk.Button(self, text=u"Заткнись", command=self.shutup_command)
        self.shutup.pack(side="left")
       
        self.quit = tk.Button(self, text="QUIT", fg="red",  command=myquit)
        self.quit.pack(side="left")

        self.RollOverFolders = tk.IntVar()
        btn = tk.Checkbutton(self.master, text="Roll over folders", variable=self.RollOverFolders)
        btn.pack(side="top")
        btn.select()

        self.listbox = tk.Listbox(self.master)
        self.listbox.pack()
        for folder in folders:
            self.listbox.insert(tk.END, folder)
        self.listbox.bind("<Double-Button-1>", self.switch_folder)
        self.listbox.bind('<<ListboxSelect>>', self.switch_folder)


    def play_file(self, filename):
        os.system("pkill ffplay")
        os.system('ffplay -hide_banner -loglevel panic -autoexit -nodisp {} &'.format(filename))

    def set_to_first_song(self):
        if len(self.Songs) == 0:
            self.CurrentSong = -1
        else:        
             self.CurrentSong = 0

    def set_to_last_song(self):
        if len(self.Songs) == 0:
            self.CurrentSong = -1
        else:        
            self.CurrentSong = len(self.Songs) - 1

    def switch_song (self, is_forward):
        if is_forward:
            logging.debug ("forward")
            self.CurrentSong += 1
            if self.CurrentSong >= len(self.Songs):
                logging.debug("self.RollOverFolders=" + str(self.RollOverFolders))
                if self.RollOverFolders != 0: 
                    if self.current_folder_no + 1 < len(self.Folders):
                        self.switch_folder_inner(self.current_folder_no + 1)
                    else:
                        self.switch_folder_inner(0)
                self.set_to_first_song()

        else:
            logging.debug("backward")
            self.CurrentSong -= 1
            if self.CurrentSong < 0:
                if self.RollOverFolders != 0:
                    if self.current_folder_no > 0:
                        self.switch_folder_inner(self.current_folder_no - 1)
                    else:
                        self.switch_folder_inner(len(self.Folders) - 1)
                self.set_to_last_song()

        
        logging.debug("set audio N {}".format(self.CurrentSong))
        if  self.CurrentSong != -1:
            self.play_file(self.Songs[self.CurrentSong])
        else:
            logging.debug("no songs in folder " + self.Folders[self.current_folder_no])

    def switch_folder_inner(self, folderNo):
        logging.debug("switch to folder no {}".format(folderNo))
        self.current_folder_no = folderNo
        folder = self.Folders[folderNo]
        logging.debug("read files from " +  folder)
        logging.debug(os.listdir(folder))
        self.Songs = []
        for x in os.listdir(folder):
            f = os.path.join(folder, x)
            if f.endswith('mp3'):
                self.Songs.append(f)
        logging.debug(self.Songs)
        logging.debug("Number of Songs: " + str(len(self.Songs)))
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


if __name__ == "__main__":
    setup_logging()
    READ_KOLESO_THREAD = TBluetoohKolesoThread(switch_song_action)
    MAIN_APPLICATION = Application(master=TK_ROOT)
    TK_ROOT.wm_protocol("WM_DELETE_WINDOW", myquit)
    MAIN_APPLICATION.play_file("intro.mp3")
    READ_KOLESO_THREAD.start()

    try:
        MAIN_APPLICATION.mainloop()
    except Exception as e:
        print (str(e))
        myquit()
