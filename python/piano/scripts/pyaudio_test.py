import math        #import needed modules
import sys

import pyaudio     #sudo apt-get install python-pyaudio
import tkinter as tk
import os
import numpy as np
import matplotlib.pyplot as plt

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)

from matplotlib.animation import FuncAnimation

PyAudio = pyaudio.PyAudio  # initialize pyaudio


OCTAVE_CHUNK_COUNT = 8
START_FREQ = 16.35  #C0
MULTIPLIER = math.pow(2, 1/OCTAVE_CHUNK_COUNT)

def get_custom_note (octave_index, note_degree):
    start = START_FREQ * math.pow(2, octave_index)
    note = start * math.pow(MULTIPLIER, note_degree)
    return note




class TKeyboardSynth:
    def __init__(self):
        os.system('xset r off')
        self.root = tk.Tk()
        self.frame = tk.Frame(self.root, width=300, height=300)
        self.frame.pack()
        self.frame.focus_set()
        self.key2note = dict()
        for degree, ch in enumerate(['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', 'bracketleft', 'bracketright', 'backslash']):
            self.key2note[ch] = (3, degree)
        for degree, ch in enumerate(['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'semicolon', 'apostrophe']):
            self.key2note[ch] = (4, degree)
        for degree, ch in enumerate(['z', 'x', 'c', 'v', 'b', 'n', 'm', 'comma', 'period', 'slash']):
            self.key2note[ch] = (5, degree)
        self.is_running = False
        self.pyaudio = PyAudio()
        self.play_freqs = set()
        self.channels_count = 1
        self.stream = None
        self.play_thread = None
        self.wave_data = None
        self.wave_data_index = 0
        self.call_back_count = 0
        self.wave_data_flatten = None
        self.frame_rate = 16000

        self.window_width = 100

        self.plot_length = 50
        self.plot_data = np.zeros((self.plot_length, self.channels_count))
        fig, ax = plt.subplots()
        self.plot = ax.plot(self.plot_data)
        ax.axis((0, len(self.plot_data), -1, 1))
        ax.yaxis.grid(True)
        fig.tight_layout(pad=0)
        canvas = FigureCanvasTkAgg(fig, master=self.frame)  # A tk.DrawingArea.
        canvas.draw()
        self.plat_as_tk_widget = canvas.get_tk_widget()
        self.plat_as_tk_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.plat_as_tk_widget.bind("<KeyPress>", self.keydown)
        self.plat_as_tk_widget.bind("<KeyRelease>", self.keyup)

        self.stream = self.pyaudio.open(
                                      format=pyaudio.paFloat32,
                                      channels=self.channels_count,
                                      rate=self.frame_rate,
                                      output=True,
                                      stream_callback=self.audio_stream_callback)

    def run(self):
        self.is_running = True
        self.root.mainloop( )
        self.is_running = False

    def keydown(self, e):
        print ('down {}'.format(e.keysym))
        if e.keysym =='space':
            self.stop_all()
        if e.keysym in self.key2note:
            note = self.key2note[e.keysym]
            freq = get_custom_note(note[0], note[1])
            if freq not in self.play_freqs:
                self.play_freqs.add(freq)
                self.rebuild_audio_data()

    def keyup(self, e):
        print ('up {}'.format(e.keysym))
        if e.keysym in self.key2note:
            note = self.key2note[e.keysym]
            freq = get_custom_note(note[0], note[1])
            if freq in self.play_freqs:
                self.play_freqs.remove(freq)
                self.rebuild_audio_data()

    def audio_stream_callback(self, in_data, frame_count, time_info, status_flags):
        if self.wave_data is None:
            return np.zeros(frame_count * self.channels_count), pyaudio.paContinue
        self.call_back_count += 1
        start =  self.wave_data_index
        end = self.wave_data_index + frame_count * self.channels_count
        data = self.wave_data[start:end]
        self.wave_data_index = end
        if self.call_back_count % 150 == 0:
            print('. {} {}'.format(frame_count, len(data)))
            #self.update_plot(start, end)
        return data, pyaudio.paContinue


    def rebuild_audio_data(self):
        print ('=== play_audio === ')
        self.wave_data_index = 0
        self.call_back_count = 0
        if len(self.play_freqs) == 0:
            self.wave_data = None
            return
        duration = 100
        amplitude = 0.5
        channels = list()
        print (self.play_freqs)
        for freq in self.play_freqs:
            samples = amplitude / len(self.play_freqs) * (
                np.sin(2 * np.pi * np.arange(self.frame_rate * duration) * freq / self.frame_rate)).astype(np.float32)
            channels.append(samples)
        self.wave_data =  sum(channels)

    def update_plot(self, start, end):
        mapping = [c - 1 for c in range(self.channels_count)]
        data = input_data[::200, mapping]
        shift = len(data)
        self.plot_data = np.roll(self.plot_data, -shift, axis=0)
        self.plot_data[-shift:, :] = data
        for channel_index, line in range(self.channels_count):
            line.set_ydata(self.plot_data[self.wave_data[channel_index][start:end], channel_index+1])
        return self.plot

    def stop_all(self):
        if self.stream is not None:
            print('stop_all, set self.enable_playin=False ')
            #print('stop_all, set self.enable_playin=True ')
            self.wave_data  = None



def main():
    #gen_waves()
    synth =  TKeyboardSynth()
    synth.run()


if __name__ == '__main__':
    main()
