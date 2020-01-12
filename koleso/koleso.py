# -*- coding: utf-8 -*-
import os
import sys

#import pyglet
#pyglet.options['audio'] = ('pulse')
#pyglet.options['audio'] = ('openal', 'pulse', 'directsound', 'silent')
#pyglet.options['audio'] = ('openal', 'pulse')
#pyglet.options['audio'] = ('silent')
#pyglet.lib.load_library('avbin')
#from pyglet import media as pyglet_media
#from pygame import mixer
#import vlc

import socket

import tkinter as tk
from functools import partial
import bluetooth
from threading import Thread
full_path = os.path.realpath(__file__)
FILEPATH, _ = os.path.split(full_path)

serverMACAddress = '20:16:05:23:17:28'
PORT = 1
LAST_SWITCH = 3
MAIN_APPLICATION = None
READ_KOLESO_THREAD = None
TK_ROOT = tk.Tk()


#pygame

# pyglet
#def play_file(filename):
    # self.shutup_command()
    # self.Player = pyglet.media.Player()
    # song = pyglet.media.load(filename)
    # self.Player.queue(song)
    # self.Player.play()


class TReadKolesoThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.killed = False
        self.socket = None
        self.connect_bluetooth()
    def connect_bluetooth(self):
        self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.socket.connect((serverMACAddress, PORT))


    def run(self):
        command = ''
        self.socket.settimeout(1)
        while not self.killed:
            try:
                command += self.socket.recv(1024).decode('ascii').strip("'")
                if command.endswith('\n'):
                    print ("command=" + command)
                    command  = command.strip()
                    newSwitch = int(command[len('switch'):])
                    print ("newSwitch=" + str(newSwitch))
                    MAIN_APPLICATION.SwitchSong(newSwitch)
                    command =  ''
            except OSError as e:
                pass # timeout
            except ValueError:
                print ("unparsable command  from arduino: {}".format(command))
            

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
        print (self.Folders)
        self.CurrentSwitch = None
        self.CurrentSong = -1
        self.create_widgets(self.Folders)
        if len(self.Folders) > 0:
            self.SwitchFolderInner(0)
        #self.Player = None


    def shutup_command(self):
        #if self.Player is not None:
        #    self.Player.pause()
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
        self.listbox.bind("<Double-Button-1>", self.SwitchFolder)
        self.listbox.bind('<<ListboxSelect>>', self.SwitchFolder)

    def PlayFilePyglet(self, filename):
        self.shutup_command()
        self.Player = pyglet_media.Player()
        song = pyglet_media.load(filename)
        self.Player.queue(song)
        self.Player.play()

    def PlayFilePygame(self, filename):
        print("Play " + filename)
        mixer.init()
        mixer.music.load(filename)
        mixer.music.play()

    def Play_ffplay(self, filename):
        os.system("pkill ffplay")
        os.system('ffplay -hide_banner -loglevel panic -autoexit -nodisp {} &'.format(filename))

    def PlayFile(self, filename):
        #self.PlayFilePyglet(filename)
        #self.PlayFilePygame(filename)
        self.Play_ffplay(filename)

    def IsForward (self, newSwitch):
        if self.CurrentSwitch == None:
            return True
        return newSwitch > self.CurrentSwitch  or (newSwitch == 0  and self.CurrentSwitch == LAST_SWITCH)


    def SwitchSong (self, newSwitch):
        if self.CurrentSwitch == -1:
            self.CurrentSong = 0
        elif self.IsForward(newSwitch):
            print ("forward")
            self.CurrentSong += 1
            if self.CurrentSong >= len(self.Songs):
                self.CurrentSong = 0
                print ("self.RollOverFolders=" + str(self.RollOverFolders))
                if self.RollOverFolders != 0: 
                    if self.CurrentFolderNo + 1  < len(self.Folders):
                        self.SwitchFolderInner(self.CurrentFolderNo  + 1)
                    else:
                        self.SwitchFolderInner(0)
                    
        else:
            print ("backward")
            self.CurrentSong -= 1
            if self.CurrentSong < 0:
                if self.RollOverFolders != 0:
                    if self.CurrentFolderNo  > 0:
                        self.SwitchFolderInner(self.CurrentFolderNo  - 1)
                    else:
                        self.SwitchFolderInner(len(self.Folders)  - 1)
                self.CurrentSong = len(self.Songs)  - 1 

        self.CurrentSwitch = newSwitch
        print  ("Get reed N " + str(newSwitch) + "  set audio N "+ str(self.CurrentSong));
        if  self.CurrentSong < len(self.Songs) and self.CurrentSong >= 0:
            self.PlayFile(self.Songs[self.CurrentSong])
        else:
            print ("no songs in folder " + self.Folders[self.CurrentFolderNo])

    def SwitchFolderInner(self, folderNo):
        print("switch to folder no " +  str(folderNo))
        self.CurrentFolderNo = folderNo
        folder = self.Folders[folderNo]
        print("read files from " +  folder)
        print (os.listdir(folder))
        self.Songs = []
        for x in os.listdir(folder):
            f = os.path.join(folder, x)
            if f.endswith('mp3'):
                self.Songs.append(f)
        print(self.Songs)
        print ("Number of Songs: " + str(len(self.Songs)))
        if len(self.Songs) == 0:
            self.CurrentSong  = -1
        #self.listbox.selection_clear(first=None)
        #self.listbox.selection_set(first=folderNo)

    def SwitchFolder(self, dummy):
        items = self.listbox.curselection()
        if len(items) == 0:
            return
        self.SwitchFolderInner(items[0])



 
if __name__ == "__main__":

    READ_KOLESO_THREAD = TReadKolesoThread()

    MAIN_APPLICATION = Application(master=TK_ROOT)
    TK_ROOT.wm_protocol("WM_DELETE_WINDOW", myquit)



    #READ_KOLESO_THREAD.connect_bluetooth()

    MAIN_APPLICATION.PlayFile("intro.mp3")

    READ_KOLESO_THREAD.start()

    try:
        MAIN_APPLICATION.mainloop()
    except Exception as e:
        print (str(e))
        myquit()
