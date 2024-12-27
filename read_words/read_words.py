import os
import random
import sys
import argparse
import pygame
from pygame.math import Vector2
import math
import time
import vlc

sys.path.append(os.path.join(os.path.dirname(__file__), '../common'))
from logging_wrapper import setup_logging

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (228, 155, 0)

WORDS = {
    "ДЯТЕЛ": "dyatel.png",
    "ГОЛУБЬ": "golub.png",
    "КУКУШКА": "kukushka.png",
    "МУХОЛОВКА": 'muholovka.png',
    "ПЕНОЧКА": 'penochka.png',
    "РЯБИННИК": 'ryabinnik.png',
    "СИНИЦА": 'sinica.png',
    "СЛАВКА": 'slavka.png',
    "СОЛОВЕЙ": 'solovey.png',
    "ТРЯСОГУЗКА": 'tryasoguzka.png',
    "ВОРОБЕЙ": 'vorob.png',
    "ВОРОНА": 'vorona.png',
    "ЗАРЯНКА": 'zaryanka.png',
    "ЗЯБЛИК": 'zyablik.png'
}


def unit_vector(angle, coef):
    theta = math.radians(angle)
    return Vector2(round(coef * math.cos(theta)), round(coef * math.sin(theta)))


class TReadWordsGame:
    def __init__(self, args):
        self.args = args
        self.logger = setup_logging("read_words.log")
        self.left_offset = 80
        self.is_running = True
        self.print_victory = False
        self.font_size = args.font_size
        self.last_mouse_pos = (0,0)

        if args.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), flags=pygame.FULLSCREEN)
            pygame.display.toggle_fullscreen()
            pygame.init()
            self.main_wnd_left = self.left_offset
            self.main_wnd_top = 0
            self.main_wnd_width = pygame.display.get_window_size()[0] - self.left_offset
            self.main_wnd_height = pygame.display.get_window_size()[1] - 40
        else:
            self.main_wnd_left = 0
            self.main_wnd_top = 0
            self.main_wnd_width = 1000
            self.main_wnd_height = 800
            self.screen = pygame.display.set_mode((self.maze_width, self.maze_height))
            pygame.init()
        self.main_rect = pygame.Rect(self.main_wnd_left, self.main_wnd_top, self.main_wnd_width, self.main_wnd_height)
        pygame.mixer.set_num_channels(8)
        self.chan_2 = pygame.mixer.Channel(2)
        self.targets = dict()
        self.correct_target = None
        self.player = None

    def play_file(self, file_path):
        if self.player is not None:
            self.player.stop()
        self.player = vlc.MediaPlayer(file_path)
        self.player.play()
        time.sleep(1)
        while self.player.is_playing():
            time.sleep(1)

    def play_victory(self):
        self.screen.fill(WHITE, rect=self.main_rect)
        self.show_target_image()
        self.print_text((400, 0), self.correct_target, 200)
        pygame.display.flip()

        file_name, _ = os.path.splitext(WORDS.get(self.correct_target))
        path = os.path.join(os.path.dirname(__file__), '../sorter/audio/birds.{}.mp3'.format(file_name))
        assert  os.path.exists(path)
        self.play_file(path)

        self.start_game()

        #font = pygame.font.SysFont(None, 300)
        #screen_text = font.render('ПОБЕДА!', True, (0, 200, 0))
        #self.screen.blit(screen_text, (250, 280))

    def play_fail(self):
        path = os.path.join(os.path.dirname(__file__), '../sorter/audio/fail.mp3')
        self.play_file(path)

    def check_mouse_click(self, event):
        r: pygame.Rect
        pos = pygame.mouse.get_pos()
        if self.last_mouse_pos == pos:
            return
        self.last_mouse_pos = pos
        for k, r in list(self.targets.items()):
            if r.collidepoint(pos[0], pos[1]):
                self.logger.info("{}".format(event))
                if k == self.correct_target:
                    self.play_victory()
                else:
                    self.play_fail()

    def check_game_events(self, event):
        if event.type == pygame.QUIT:
            self.is_running = False
        elif event.type == pygame.MOUSEBUTTONUP:
            if pygame.mouse.get_focused():
                self.check_mouse_click(event)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.is_running = False
            elif event.key == pygame.K_r:
                self.start_game()

    def print_text(self, point, text, font_size=None):
        if font_size is None:
            font_size = self.args.font_size
        font = pygame.font.SysFont(None, font_size)
        screen_text = font.render(text, True, BLACK)
        self.screen.blit(screen_text, point)
        return screen_text.get_rect().move(point[0], point[1])

    def set_target(self, point, text):
        screen_text = self.print_text(point, text)
        screen_text = screen_text.inflate(40, 40)
        color = random.choice([RED, GREEN, BLUE, BLACK, YELLOW])
        pygame.draw.rect(self.screen, color=color,  rect=screen_text, width=10)
        self.targets[text] = screen_text

    def get_center(self):
        return Vector2(self.main_rect.center) - (250, 20)

    def show_target_image(self):
        path = os.path.join(os.path.dirname(__file__), '../sorter/birds', WORDS[self.correct_target])
        image = pygame.image.load(path)
        image_size = 500
        self.image = pygame.transform.scale(image, (image_size, image_size))
        self.screen.blit(self.image, self.get_center() - (image_size/6, image_size/3))

    def start_game(self):
        self.screen.fill(WHITE, rect=self.main_rect)
        keys = random.sample(list(WORDS.keys()), k=self.args.words_count)
        self.correct_target = random.choice(keys)
        center = self.get_center()

        pygame.draw.circle(self.screen, BLACK, center, 5)
        self.print_text((self.left_offset, 0), self.correct_target, 25)

        radius = (self.main_rect.height - 100) / 2.0
        for i in range(self.args.words_count):
            u = unit_vector(90 + i * 360 / self.args.words_count, radius)
            u = (u[0]*1.5, u[1]) #make elipse
            point = center - u
            self.set_target(point, keys[i])
        self.show_target_image()

    def main_loop(self):
        self.start_game()
        clock = pygame.time.Clock()
        while self.is_running:
            time_delta = clock.tick(120) / 1000.0
            for event in pygame.event.get():
                self.check_game_events(event)

            pygame.display.flip()
            clock.tick(25)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--not-fullscreen", dest='fullscreen', default=True, action="store_false")
    parser.add_argument("--words-count", dest='words_count', default=2, type=int, required=False)
    parser.add_argument("--use-joystick", dest='use_joystick', default=False, action="store_true")
    parser.add_argument("--font-size", dest='font_size', default=150, type=int)
    return parser.parse_args()


if __name__ == "__main__":
    game = TReadWordsGame(parse_args())
    game.main_loop()
    pygame.quit()
