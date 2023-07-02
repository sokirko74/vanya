import logging

import pydub.effects

from python.rivers.engine_sound import TEngineSound
from python.utils.logging_wrapper import setup_logging

import argparse
import pygame
import time
import logging

import numpy as np
import sys
import librosa
import soundfile as sf
import os
from pydub import AudioSegment
import  simpleaudio

def pitch_shift(sound, n_steps):
    y = np.frombuffer(sound._data, dtype=np.int16).astype(np.float32)/2**15
    y_harmonic, y_percussive = librosa.effects.hpss(y)
    a = AudioSegment(np.array(y_harmonic * (1 << 15), dtype=np.int16).tobytes(), frame_rate=sound.frame_rate,
                     sample_width=2, channels=1)
    #y = librosa.effects.pitch_shift(y, sr=sound.frame_rate, n_steps=n_steps)
    #a  = AudioSegment(np.array(y * (1<<15), dtype=np.int16).tobytes(), frame_rate = sound.frame_rate, sample_width=2, channels = 1)
    return a

def create_plot(y):
    import matplotlib.pyplot as plt
    import scipy
    a = librosa.lpc(y, order=2)
    b = np.hstack([[0], -1 * a[1:]])
    y_hat = scipy.signal.lfilter(b, [1], y)
    fig, ax = plt.subplots()
    ax.plot(y)
    ax.plot(y_hat, linestyle='--')
    ax.legend(['y'])
    ax.set_title('harmonic')
    plt.show()

def multiply_first_interval(y, sr, n_times):
    _, beat_frames = librosa.beat.beat_track(y=y, sr=sr,
                                             hop_length=128)
    beat_samples = librosa.frames_to_samples(beat_frames)
    intervals = list(librosa.util.frame(beat_samples, frame_length=2,
                                   hop_length=1).T)[:1]
    intervals *= n_times
    sub = librosa.effects.remix(y, intervals)
    return sub

def try_to_equalize_pitch_librosa_archive(path):
    y, sr = librosa.load(path)
    start = 30000
    end = start + 2 * sr
    part = y[start:end]
    #sub = multiply_first_interval(part, sr, 10)
    # _, beat_frames = librosa.beat.beat_track(y=y, sr=sr,
    #                                          hop_length=512)
    # beat_samples = librosa.frames_to_samples(beat_frames)
    # intervals = librosa.util.frame(beat_samples, frame_length=2,
    #                                hop_length=1).T
    #
    # samples = librosa.frames_to_samples(y)
    # section_count = len(y)
    # duration = librosa.get_duration(y=y, sr=sr)
    # start = 30000
    # len_ms = 100
    # end = start + int(len_ms/1000 * sr)
    #
    # sub = y[start:end]
    # #intervals = [[start, end] for i in range(1)]
    # sub = librosa.effects.remix(y, intervals)

    # border_len = 200
    # for i in range(border_len):
    #     m = len(sub) - border_len + i
    #     #v = (sub[i] + sub[m]) / 2
    #     v = 0
    #     sub[m] = v

    # min_diff = 10000
    # best_end = end
    # for i in range(end, end+200):
    #     diff = abs(y[start] - y[i])
    #     if min_diff > diff:
    #         min_diff = diff
    #         best_end = i

    #sub = y[start:best_end]
    #sub = np.tile(sub, 10)

    sf.write('tmp_subseg.wav', sub, sr, format='wav', subtype='PCM_24')


    # tempo, beats = librosa.beat.beat_track(y=b, sr=sr, hop_length=512)
    # beat_times = librosa.frames_to_time(beats, sr=sr, hop_length=512)
    # cqt = np.abs(librosa.cqt(b, sr=sr, hop_length=512))
    # subseg = librosa.segment.subsegment(cqt, beats, n_segments=2)
    # subseg_t = librosa.frames_to_time(subseg, sr=sr, hop_length=512)
    #freqs, times, mags = librosa.reassigned_spectrogram(b, sr=sr)
    #y_pitch_tuning =  librosa.pitch_tuning(freqs)

    #y_harmonic, y_percussive = librosa.effects.hpss(b)
    #sf.write('tmp.wav', b, sr, format='wav', subtype='PCM_24')
    #sf.write('tmp_pitch_tuning.wav', y_pitch_tuning, sr, format='wav', subtype='PCM_24')
    #samples = sound.get_array_of_samples()
    #a = librosa.piptrack(y=b, sr=sr)
    #y = np.array(samples).astype(np.float32)
    #y = np.frombuffer(sound._data, dtype=np.int16).astype(np.float32)/2**15
    # freqs, times, mags = librosa.reassigned_spectrogram(y, sr=sound.frame_rate,
    #                                                     fill_nan=True)
    # freqs = freqs[mags > np.median(mags)]
    #y_harmonic, y_percussive = librosa.effects.hpss(y)
    #a = librosa.piptrack(y=y, sr=sound.frame_rate)
    #b =  librosa.pitch_tuning(freqs)
    #sound.export("tmp_orig.wav", format='wav')
    #sf.write('tmp.wav', y, sound.frame_rate, subtype='PCM_24')
    sys.exit()


def find_similar_end_librosa(arr):
    min_diff = 1000
    best_end = len(arr)
    for i in range(len(arr)-500, len(arr) - 1):
        if (arr[0] < arr[1]) == (arr[i] < arr[i + 1]):
            diff = abs(arr[i] - arr[0])
            if min_diff > diff:
                min_diff = diff
                best_end = i
    return arr[:best_end]

def make_similar_end_librosa(arr):
    fuzzy_len = 5
    for start_i in range(fuzzy_len):
        end_i = len(arr) - fuzzy_len + start_i
        arr[end_i] = ((fuzzy_len - start_i)*arr[end_i]  + (start_i * arr[start_i])) / fuzzy_len


def try_to_equalize_pitch_3(path):
    y, sr = librosa.load(path)
    start = 30000
    end = 34000
    sub_len = end - start
    sub = y[start:end]
    # for i in range(100):
    #     sub[1000 + i] = 0
    #sub = find_similar_end_librosa(sub)
    #make_similar_end_librosa(sub)
    border_len = 100
    # for i in range(border_len):
    #     sub[i] = 0
    nums = 10
    sub = np.tile(sub, nums)
    for i in range(1, nums):
        for k in range(-400, +400):
            sub[sub_len * i - k] = 0
    sf.write('tmp_subseg.wav', sub, sr, format='wav', subtype='PCM_24')
    sys.exit()

def find_similar_end_pydub(a):
    min_diff = 1000
    arr = np.array(a.get_array_of_samples(), dtype=np.int16)
    best_end = len(arr)
    start_mean = np.mean(arr[:10])
    for i in range(len(arr)-100, len(arr)):
        avr = np.mean(arr[i:i+10])
        diff = abs(start_mean - avr)
        if min_diff > diff:
            min_diff = diff
            best_end = i
    return  best_end / (len(arr) / len(a))

def try_to_equalize_pitch_pydub(path):
    segm = AudioSegment.from_file(path, format="wav")
    #sub = segm[2000:2400].fade_in(10).fade_out(10)
    start = 3988
    len = 100
    sub = segm[3000:3800]
    # best_end = find_similar_end_pydub(sub)
    # sub = sub[:best_end]
    # print ("duration  sum = {}".format(sub.duration_seconds))
    #sub = sub.fade_in(1).fade_out(1)
    do_it_over = sub * 20

    # subN = segm[2000:2200]
    # for i in range(100):
    #     subN.append(sub, crossfade=10)
    print ("duration = {}".format(do_it_over.duration_seconds))
    do_it_over.export('tmp_subseg.wav', format="wav")

def play_simple_audio(sound):
    return  simpleaudio.play_buffer(
        sound.raw_data,
        num_channels=sound.channels,
        bytes_per_sample=sound.sample_width,
        sample_rate=sound.frame_rate
    )

def try_to_equalize_pitch_max(path):
    segm = AudioSegment.from_file(path, format="wav")
    start = 6000
    best_start = start
    for i in range(20):
        if segm[start + i].max > segm[start].max:
            best_start = start + i
    start = best_start
    len = 400
    end = start + len
    for i in range(20):
        if segm[start + len - i].max > segm[end].max:
            end = start + len - i
    inc = segm[start:end].append(segm[start:end].reverse(), crossfade=1)
    #inc = segm[start:end]
    inc = pydub.effects.normalize(inc)

    #dec = inc.reverse()
    #sub = inc+dec
    sub = inc
    sub = sub.set_channels(1)
    do_it_over = sub
    for i in range(200):
        do_it_over = do_it_over.append(sub, crossfade=1)

    print ("duration = {}".format(do_it_over.duration_seconds))
    do_it_over.export('tmp_subseg.wav', format="wav")
    play_obj = play_simple_audio(do_it_over)
    play_obj.wait_done()

def cut_amplitude(y):
    start_len  = int(len(y) / 10)
    start = y[0:start_len]
    start_max = start.max()
    start_min = start.min()
    for i in range(len(y)):
        if y[i] > start_max:
            y[i] = start_max
        if y[i] < start_min:
            y[i] = start_min

def equalize_amplitude(y):
    parts_count = 10
    chunk_len = len(y) / parts_count
    chunk_max = 0
    for i in range(0, len(y), chunk_len):
        period = y[i:i+chunk_len]
        subchunk_len = len(period) / parts_count
        for k in range(0, len(subchunk_len), chunk_len):
            sub_period = y[i:i + chunk_len]
            chunk_max = np.mean()

def make_symmetric(y):
    orig = y
    for i in range(len(y)):
        y[i] = (orig[i] + orig[-i]) / 2

def show_stft(y):

    import matplotlib.pyplot as plt
    S = librosa.stft(y, center=False)
    fig, ax = plt.subplots()
    img = librosa.display.specshow(librosa.amplitude_to_db(S,
                                                           ref=np.max),
                                   y_axis='log', x_axis='time', ax=ax)
    ax.set_title('Power spectrogram')
    fig.colorbar(img, ax=ax, format="%+2.0f dB")
    fig.show()

def show_mel(y, sr):
    S = librosa.feature.melspectrogram(y=y, sr=sr)
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    S_dB = librosa.power_to_db(S, ref=np.max)
    img = librosa.display.specshow(S_dB, x_axis='time',
                             y_axis='mel', sr=sr,
                             fmax=8000, ax=ax)
    fig.colorbar(img, ax=ax, format='%+2.0f dB')
    ax.set(title='Mel-frequency spectrogram')
    fig.show()

def show_wave(y, sr):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(nrows=3, sharex=True)
    librosa.display.waveshow(y, sr=sr, ax=ax[0])
    ax[0].set(title='Envelope view, mono')
    ax[0].label_outer()
    fig.show()

def show_constant_q(y, sr):
    import matplotlib.pyplot as plt
    y, sr = librosa.load(librosa.ex('trumpet'))
    C = np.abs(librosa.cqt(y, sr=sr))
    fig, ax = plt.subplots()
    img = librosa.display.specshow(librosa.amplitude_to_db(C, ref=np.max),
                                   sr=sr, x_axis='time', y_axis='cqt_note', ax=ax)
    ax.set_title('Constant-Q power spectrum')
    fig.colorbar(img, ax=ax, format="%+2.0f dB")
    fig.show()
def try_to_with_librosa_4(path):
    y, sr = librosa.load(path)
    start = 40000
    best_start = start
    for i in range(200):
        if y[start + i] > y[best_start]:
            best_start = start + i
    start = best_start

    len = 2000
    end = start + len

    for i in range(200):
        if y[start + len - i] > y[end]:
            end = start + len - i

    nums = 10
    inc = y[start:end]
    #show_stft(inc)
    #show_wave(inc, sr)
    #show_mel(inc, sr)
    show_constant_q(inc, sr)

    cut_amplitude(inc)
    show_wave(inc, sr)
    forward_backward = np.concatenate((inc, np.flip(inc)))
    for i in range(10):
        make_symmetric(forward_backward)
    sub = np.concatenate( [forward_backward] * nums)
    #sub = np.concatenate([inc] * nums)
    #sub[-1] = 0.99
    #sub = np.tile(sub, nums)
    sf.write('tmp_subseg.wav', sub, sr, format='wav', subtype='PCM_24')
    #segm = AudioSegment.from_file('tmp_subseg.wav', format="wav")
    #play_obj = play_simple_audio(segm)
    #play_obj.wait_done()
    sys.exit()

def _test_engine(engine: TEngineSound):
    engine.start_engine_thread()
    pygame.display.init()
    screen = pygame.display.set_mode((800, 600))
    i = 0
    while True:
        if i % 3 == 0:
            engine.log.debug('Speed = {} State = {} Offset = {}'.format(
                engine.get_current_speed(),
                engine.get_state(),
                engine._get_milliseconds_from_start()))
        i += 1

        keys = pygame.key.get_pressed()
        key_pressed = sum(1 for k in keys if k)
        if not key_pressed:
            engine.stable_speed()
        elif keys[pygame.K_UP]:
            engine.increase_speed()
        elif keys[pygame.K_DOWN]:
            engine.decrease_speed()
        if keys[pygame.K_ESCAPE]:
            print("got escape key")
            engine.stop = True
            engine.join(2)
            break
        time.sleep(0.2)
        pygame.event.pump()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine-folder", dest='engine_folder', default='../assets/sounds/bus')
    parser.add_argument("--limit-speed-count", dest='limit_speed', default=5, type=int)
    return parser.parse_args()


def main():
    args = parse_args()
    log = setup_logging("test_engine", console_level=logging.DEBUG)

    # sound = TEngineSound(log, engine_folder=args.engine_folder, limit_speed=args.limit_speed)
    # _test_engine(sound)
    file_path = os.path.join(args.engine_folder, "engine_increase.wav")
    try_to_with_librosa_4(file_path)


if __name__ == '__main__':
    main()