#we have to create separate files since pygame.mixer.music.set_pos  does not work on our wav files
# ppygame.error: set_pos unsupported for this codec
#snd = pygame.mixer.music.load('assets/sounds/engine_increase.wav')
        #pygame.mixer.music.play()
#pygame.mixer.music.set_pos(10)

#Use this script:
#rm -rf assets/sounds/ford
#python3 engine_sound.py --action prepare  --input assets/sounds/engine_increase.wav --segment-folder assets/sounds/ford/
#python3 engine_sound.py --action test  --segment-folder assets/sounds/ford/


import os
import time
import pygame
import threading
from pydub import AudioSegment
import argparse



def main():
    pygame.mixer.init()
    file_path = os.path.join(os.path.dirname(__file__), '../assets/sounds/bus/engine_increase.ogg')
    snd = pygame.mixer.Sound(file_path)
    l = snd.get_length()
    snd.play(start=10.5)
    # pygame.mixer.music.load(file_path)
    # pygame.mixer.music.play()
    # time.sleep(2)
    # pygame.mixer.music.pause()
    # pygame.mixer.music.set_pos(20.0)
    # pygame.mixer.music.play(start=10.5`)
    time.sleep(5)


if __name__ == '__main__':
    main()