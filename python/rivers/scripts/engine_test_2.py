import logging

import librosa

from python.rivers.engine_sound_from_stable import TEngineSound
from python.utils.logging_wrapper import setup_logging

import argparse
import pygame
import time
import logging
import pyaudio
import os


def _test_engine_gui(engine: TEngineSound):

    pygame.display.init()
    screen = pygame.display.set_mode((800, 600))

    i = 0
    while True:
        keys = pygame.key.get_pressed()
        key_pressed = sum(1 for k in keys if k)
        if not key_pressed:
            engine.stabilize_speed()
        elif keys[pygame.K_UP]:
            engine.increase_speed()
        elif keys[pygame.K_DOWN]:
            engine.decrease_speed()
        if keys[pygame.K_ESCAPE]:
            print("got escape key")
            break
        time.sleep(0.2)
        pygame.event.pump()


def play_raw_frames(y, sr):
    p = pyaudio.PyAudio()
    stream =  p.open(
        format=pyaudio.paFloat32,
        channels=1,
        rate=sr,
        output=True,
    )
    duration = librosa.get_duration(y=y)
    stream.write(y, num_frames=len(y))
    stream.close()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine-folder", dest='engine_folder', default='../assets/sounds/uaz')
    parser.add_argument("--limit-speed-count", dest='limit_speed', default=5, type=int)
    return parser.parse_args()


def main():
    args = parse_args()
    log = setup_logging("test_engine", console_level=logging.DEBUG)
    engine = TEngineSound(log, args.engine_folder, 5)
    engine.start_play_stream()
    _test_engine_gui(engine)
    #play_raw_frames(engine._engine_sound, engine.sr)
    #play_raw_frames(engine._increasing_engine_sound, engine.sr)
    #ngine.start_engine_thread()
    #_test_engine_gui(sound)
    #for i in range(10):
    #    engine.increase_speed()
    #    time.sleep(1)



if __name__ == '__main__':
    main()