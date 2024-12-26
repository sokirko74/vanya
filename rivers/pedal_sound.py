import sys

# appending a path
sys.path.append('..')

from utils.logging_wrapper import setup_logging
from utils.racing_wheel import TRacingWheel
from utils.game_sounds import TSounds

import pygame
import time
import argparse
import os
import math
import random
import logging

SOUNDS_DIR = os.path.join(os.path.dirname(__file__), "assets", 'sounds')



def main():
    logger = setup_logging("pedal_sound", console_level=logging.DEBUG)
    racing_wheel = TRacingWheel(logger, 300, 30)
    sounds = TSounds(SOUNDS_DIR, True)
    left = None
    screen = pygame.display.set_mode((500, 500))
    stop = False
    left = pygame.mixer.Sound(os.path.join( os.path.dirname(__file__), 'assets/sounds/siren.wav'))
    right = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), 'assets/sounds/repair_car.wav'))
    channel_left = pygame.mixer.Channel(0)
    channel_left.set_volume(0.01, 0.01)
    channel_right = pygame.mixer.Channel(1)
    while not stop:
        if racing_wheel.is_attached():
            wheel_angle = racing_wheel.get_angle()
            print (wheel_angle)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop = True
                break
            if racing_wheel.is_attached():
                if racing_wheel.is_left_pedal_pressed():
                    channel_left.play(left)
                    logger.info('play left (wheel)(')
                else:
                    channel_left.stop()
                if racing_wheel.is_left_pedal_pressed():
                    channel_left.play(left)
                    logger.info('play right (wheel)')
                else:
                    channel_right.stop()
            else:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
                    channel_left.play(left)
                    logger.info('play left (key)')
                elif event.type == pygame.KEYUP and event.key == pygame.K_LEFT:
                    channel_left.stop()
                    logger.info('stop left (key)')
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
                    channel_right.play(right)
                    logger.info('play right (key)')
                elif event.type == pygame.KEYUP and event.key == pygame.K_RIGHT:
                    logger.info('stop right (key)')
                    channel_right.stop()
    logger.info("exit")


if __name__ == "__main__":
    main()

#=========
# Звук старта ( если есть)
# Макс. громкость

