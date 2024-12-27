import math        #import needed modules
import sys
import time

import pyaudio     #sudo apt-get install python-pyaudio
import tkinter as tk
import os
import numpy as np
from mingus.containers import Note, Bar, NoteContainer
import vlc
import random
from mingus.midi import pyfluidsynth, fluidsynth, midi_file_in
import mido
import fluidsynth
import threading
import queue

PIANO = 1
ORGAN = 20
SITAR = 105




class TMidiModifier:
    def __init__(self):
        os.system('xset r off')
        self.root = tk.Tk()
        self.frame = tk.Frame(self.root, width=300, height=300)
        self.frame.pack()
        self.frame.focus_set()

        self.frame.bind("<KeyPress>", self.keydown)
        self.frame.bind("<KeyRelease>", self.keyup)

        self.play_thread = None
        self.addit_midi_event_queue = queue.Queue()

        # fluidsynth.init(sound_font, 'alsa')
        #fluidsynth.set_instrument(ORGAN, 1)

        # self.synth = pyfluidsynth.Synth()
        # self.synth.sfload(sound_font)
        # self.synth.program_reset()
        # self.synth.start('alsa')
        path = '/home/sokirko/Downloads/AllAmericanGirl.mid'
        self.midi_path = '/home/sokirko/Downloads/youre_only_lonely.mid'
        self.pitch_bend = 0
        self.tempo = 500000
        self.mid_file = None
        self.fs_synth = None
        self.port_name =  self.load_fluidsynth()

        # (m, bpm) = m.MIDI_to_Composition(path)
        # m.play()
        # fluidsynth.set_instrument(ORGAN, 1)
        # bars = list()
        # for i in range(20):
        #     b = Bar()
        #     b.place_notes([Note("A", 4)])
        #     b.place_notes([Note("C", 4)])
        #     b.place_notes([Note("E",  4)])
        #     bars.append(b)
        # #self.note_container = NoteContainer(notes)
        # fluidsynth.play_Bars(bars, 1)

    def load_fluidsynth(self):
        sound_font = '/usr/share/sounds/sf2/default-GM.sf2'
        self.fs_synth = fluidsynth.Synth()
        sfid = self.fs_synth.sfload(sound_font)
        self.fs_synth.program_reset()
        self.fs_synth.start('alsa')

        self.fs_synth.noteon(1, 70, 127)
        time.sleep(3)
        self.fs_synth.noteoff(1, 70)

        #self.fs_synth.set_reverb_level(1.0)
        self.fs_synth.set_reverb(roomsize=1.0, damping=1.0, width=100, level=0.0)
        self.fs_synth.noteon(1, 70, 127)
        time.sleep(3)
        self.fs_synth.noteoff(1, 70)

        print(mido.get_output_names())
        for i in mido.get_output_names():
            if i.find('FLUID') != -1:
                return i

    def play_midi(self):
        with mido.open_output(self.port_name) as outp:
            for i in range(100):
                self.mid_file = mido.MidiFile(self.midi_path)
                for msg in self.mid_file.play():
                    if not self.addit_midi_event_queue.empty():
                        add_msg = self.addit_midi_event_queue.get()
                        outp.send(add_msg)
                    #print('msg.type={}', msg.type)

                    outp.send(msg)

    def run(self):
        self.play_thread = threading.Thread(target=self.play_midi)
        self.play_thread.start()
        self.root.mainloop( )

    def send_pitch_bend(self):
        print ('pitchwheel = {}'.format(self.pitch_bend))
        for channel in range(0, 15):
            msg = mido.Message('pitchwheel', pitch=self.pitch_bend, channel=channel)
            self.addit_midi_event_queue.put(msg)

    def send_tempo(self, direction):
        self.mid_file.ticks_per_beat += direction * 30
        if self.mid_file.ticks_per_beat < 20:
            self.mid_file.ticks_per_beat = 20
        print ('self.mid_file.ticks_per_beat = {}'.format(self.mid_file.ticks_per_beat))

    def send_reverb(self, direction):
        level = self.fs_synth.get_reverb_level()
        level += direction * 0.05
        level = max(0.0,  min(level, 1.0))
        self.fs_synth.set_reverb_level(level)
        print ('set_reverb_level = {}'.format(level))


    def keydown(self, e):
        print ('down {}'.format(e.keysym))
        if e.keysym == 'Up':
            self.pitch_bend += 100
            self.send_pitch_bend()
        if e.keysym == 'Down':
            self.pitch_bend -= 100
            self.send_pitch_bend()
        if e.keysym == 'Left':
            self.send_tempo(-1)
        if e.keysym == 'Right':
            self.send_tempo(+1)
        if e.keysym == 'q':
            self.send_reverb(+1)
        if e.keysym == 'a':
            self.send_reverb(-1)


    def keyup(self, e):
        print ('up {}'.format(e.keysym))

    def stop_all(self):
        print('stop_all, set self.enable_playin=False ')
        for i in self.play_freqs.values():
            i.stop_note()
        self.play_freqs.clear()



def main():
    synth =  TMidiModifier()
    synth.run()


if __name__ == '__main__':
    main()
