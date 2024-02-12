from utils.colors import TColors

import pygame
import random


MAX_FUEL_VOLUME = 5
RED_LAMP_FUEL_MIN_LEVEL = 2


class TGameRegisters:
    def __init__(self, screen: pygame.Surface):
        self.screen: pygame.Surface = screen
        self.game_over = False
        self.river_accident_count = 0
        self.bridge_passing_count = 0
        self.success_tasks_count = 0
        self.paused = False
        self.map_parts_count = 0
        self.fuel_volume = MAX_FUEL_VOLUME
        self.map_parts_count = 0
        self.font = pygame.font.SysFont(None, 30)
        self.red_lamp_font = pygame.font.SysFont(None, 230)
        #self.font_fade_event = pygame.USEREVENT + 1
        #pygame.time.set_timer(self.font_fade_event, 200)
        self.count_call = 0

    def print_text(self, text, x, y):
        screen_text = self.font.render(text, True, TColors.white)
        self.screen.blit(screen_text, (x, y))

    def get_score(self):
        return self.bridge_passing_count - self.river_accident_count + self.success_tasks_count

    def refuel_car(self):
        self.fuel_volume = MAX_FUEL_VOLUME

    def is_full_tank(self):
        return self.fuel_volume == MAX_FUEL_VOLUME

    def should_generate_gas_station(self):
        #return self.fuel_volume <= RED_LAMP_FUEL_MIN_LEVEL #test
        return self.fuel_volume <= RED_LAMP_FUEL_MIN_LEVEL and random.random() > 1.5 * self.fuel_volume / MAX_FUEL_VOLUME #prod

    def increment_map_parts_count(self):
        self.map_parts_count += 1

        if (self.map_parts_count % 3) == 0:
            self.fuel_volume -= 1
            if self.fuel_volume <= 0:
                return False
        return True

    def draw_params(self, my_car_top, game_speed, car_is_broken):
        self.count_call +=1
        self.print_text('score: {}'.format(self.get_score()), 30, 0)
        self.print_text('speed: {}'.format(game_speed), 30, 30)
        self.print_text('position: {}'.format(my_car_top), 30, 60)
        self.print_text('rivers: {}'.format(self.river_accident_count), 30, 90)
        self.print_text('bridges: {}'.format(self.bridge_passing_count), 30, 120)
        self.print_text('success tasks: {}'.format(self.success_tasks_count), 30, 150)
        self.print_text('broken: {}'.format(car_is_broken), 30, 180)
        self.print_text('km: {}'.format(self.map_parts_count), 30, 210)
        self.print_text('fuel: {}'.format(self.fuel_volume), 30, 240)
        if self.fuel_volume <= RED_LAMP_FUEL_MIN_LEVEL:
            if self.count_call % 8 < 4:
                text = str(self.fuel_volume)
            else:
                text = ' '
            screen_text = self.red_lamp_font.render(text, True, TColors.red)
            self.screen.blit(screen_text, (self.screen.get_width() - 100, 0))

        if self.paused:
            s = pygame.display.get_surface()
            self.print_text("pause (press spacebar to play)", s.get_width()/2, s.get_height()/2)
