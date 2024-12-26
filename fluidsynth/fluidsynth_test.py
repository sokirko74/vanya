import math        #import needed modules
import sys
import time

import tkinter as tk
import os
import numpy as np
from mingus.containers import Note, Bar
import vlc
import random
from mingus.midi import pyfluidsynth, fluidsynth



OCTAVE_CHUNK_COUNT = 5
START_FREQ = 16.35  #C0
MULTIPLIER = math.pow(2, 1/OCTAVE_CHUNK_COUNT)


def get_custom_note (octave_index, note_degree):
    start = START_FREQ * math.pow(2, octave_index)
    note = start * math.pow(MULTIPLIER, note_degree)
    return note


PIANO = 1
ORGAN = 20
SITAR = 105
MIDI_INSTRUMENT = 29


class BentNote:
    def __init__(self, synth, channel, freq):
        self.synth = synth
        self.note = Note().from_hertz(freq)
        self.channel = channel
        next_note = Note().from_hertz(freq)
        next_note.augment()
        bent_unit = 4096 / (next_note.to_hertz() - self.note.to_hertz())
        freq_diff = int(freq - self.note.to_hertz())
        self.bend =  int(freq_diff * bent_unit)
        print ('input_freq={} = {} ({} hz) + {} hz (bend={}, bu={})'.format(
            freq, self.note, self.note.to_hertz(),  freq_diff, self.bend, bent_unit))

    def play_note(self):
        self.synth.noteon(self.channel, int(self.note), 127)
        self.synth.pitch_bend(self.channel, self.bend)

    def stop_note(self):
        self.synth.noteoff(self.channel, int(self.note))


class TKeyboardSynth:
    def __init__(self):
        os.system('xset r off')
        self.root = tk.Tk()
        self.frame = tk.Frame(self.root, width=300, height=300)
        self.frame.pack()
        self.frame.focus_set()
        key2note = dict()
        for degree, ch in enumerate(['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', 'bracketleft', 'bracketright', 'backslash']):
            key2note[ch] = (3, degree)
        for degree, ch in enumerate(['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'semicolon', 'apostrophe']):
            key2note[ch] = (4, degree)
        for degree, ch in enumerate(['z', 'x', 'c', 'v', 'b', 'n', 'm', 'comma', 'period', 'slash']):
            key2note[ch] = (5, degree)
        self.key2note = dict()
        for i,v in key2note.items():
            self.key2note[i] = v
            if len(i) == 1:
                self.key2note[i.upper()] = v

        self.is_running = False
        self.play_freqs = dict()
        self.channels_count = 1
        self.frame.bind("<KeyPress>", self.keydown)
        self.frame.bind("<KeyRelease>", self.keyup)

        sound_font =  '/usr/share/sounds/sf2/default-GM.sf2'

        self.synth = pyfluidsynth.Synth()
        self.synth.sfload(sound_font)
        self.synth.program_reset()
        self.synth.start('alsa')
        #self.synth.noteon(1, 70, 64)
        self.synth.program_change(1, ORGAN)
        #self.synth.program_change(3, ORGAN)
        #synth.noteon(3, 60, 64)
        # self.synth.noteon(1, 70, 64)
        # for i in range(0, 4096, 100):
        #      print (i)
        #      self.synth.pitch_bend(1, i)
        #      #self.synth.noteon(1, 70, 64)
        #      time.sleep(0.3)
        #synth.noteoff(1, 70)
        #synth.noteoff(3, 60)

        pass
        #
        # #synth.p
        # pass

    def run(self):
        self.is_running = True
        self.root.mainloop( )
        self.is_running = False

    def keydown(self, e):
        global MIDI_INSTRUMENT
        print ('down {}'.format(e.keysym))
        if e.keysym == 'Escape':
            self.stop_all()
        if e.keysym == 'F1':
            MIDI_INSTRUMENT += 1
            if MIDI_INSTRUMENT == 128:
                MIDI_INSTRUMENT = 1
        if e.keysym in self.key2note:
            note = self.key2note[e.keysym]
            freq = get_custom_note(note[0], note[1])
            if freq not in self.play_freqs:
                free_channels = set(range(1, 10))
                for i in self.play_freqs.values():
                    free_channels.remove(i.channel)
                free_channel = list(free_channels)[0]
                self.synth.program_change(free_channel, MIDI_INSTRUMENT)
                bn = BentNote(self.synth, free_channel, freq)
                self.play_freqs[freq] = bn
                bn.play_note()

    def keyup(self, e):
        print ('up {}'.format(e.keysym))
        if e.keysym in self.key2note:
            note = self.key2note[e.keysym]
            freq = get_custom_note(note[0], note[1])
            if freq in self.play_freqs:
                self.play_freqs[freq].stop_note()
                del self.play_freqs[freq]

    def stop_all(self):
        print('stop_all, set self.enable_playin=False ')
        for i in self.play_freqs.values():
            i.stop_note()
        self.play_freqs.clear()


def main():
    #gen_waves()
    synth =  TKeyboardSynth()
    synth.run()


if __name__ == '__main__':
    main()
