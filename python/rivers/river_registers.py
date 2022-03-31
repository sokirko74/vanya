from utils.colors import TColors

import pygame


class TGameRegisters:
    def __init__(self, screen):
        self.screen = screen
        self.game_over = False
        self.river_accident_count = 0
        self.bridge_passing_count = 0
        self.transfered_grannies_count = 0
        self.paused = False
        self.font = pygame.font.SysFont(None, 30)

    def print_text(self, text, x, y):
        screen_text = self.font.render(text, True, TColors.white)
        self.screen.blit(screen_text, (x, y))

    def get_score(self):
        return self.bridge_passing_count - self.river_accident_count + self.transfered_grannies_count

    def draw_params(self, my_car_top, game_speed):
        self.print_text('score: {}'.format(self.get_score()), 30, 0)
        self.print_text('speed: {}'.format(game_speed), 30, 30)
        self.print_text('position: {}'.format(my_car_top), 30, 60)
        self.print_text('rivers: {}'.format(self.river_accident_count), 30, 90)
        self.print_text('bridges: {}'.format(self.bridge_passing_count), 30, 120)
        self.print_text('grannies: {}'.format(self.transfered_grannies_count), 30, 150)
        if self.paused:
            s = pygame.display.get_surface()
            self.print_text("pause (press spacebar to play)", s.get_width()/2, s.get_height()/2)
