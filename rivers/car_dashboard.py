from utils.colors import TColors

import pygame
import time


class TCarDashboard:
    def __init__(self, screen: pygame.Surface):
        self.screen: pygame.Surface = screen
        self.river_accident_count = 0
        self.gates_accident_count = 0
        self.bridge_passing_count = 0
        self.success_tasks_count = 0
        self.map_parts_count = 0
        self.font = pygame.font.SysFont(None, 30)
        self.red_lamp_font = pygame.font.SysFont(None, 230)
        self.is_on_alarm = True
        self.count_call = 0
        self.chase_bridge_count = 0


    def print_text(self, text, x, y):
        screen_text = self.font.render(text, True, TColors.white)
        self.screen.blit(screen_text, (x, y))

    def get_score(self):
        return self.bridge_passing_count - self.river_accident_count + self.success_tasks_count

    def too_many_rivers_accidents(self):
        return self.river_accident_count > 0 and (self.river_accident_count % 3 == 0)

    def draw_params(self, game_paused, my_car_top, game_speed, car_is_broken, broken_tires,
                    fuel_volume, fuel_red_lamp, engine, passengers):
        self.count_call +=1
        l = 10
        params = [
            ("score", self.get_score()),
            ("speed", round(game_speed, 2)),
            ("position", my_car_top),
            ("rivers", self.river_accident_count),
            ("bridges", self.bridge_passing_count),
            ("tasks", self.success_tasks_count),
            ("broken", car_is_broken),
            ("km", self.map_parts_count),
            ("volume", fuel_volume),
            ("alarm", self.is_on_alarm),
            ("engine", engine),
            ("tires", (not broken_tires)),
            ("passengers", passengers),
            ("gates", self.gates_accident_count)
        ]
        y = 0
        for title, value in params:
            self.print_text('{}: {}'.format(
                title, value), 10, y)
            y += 25

        if fuel_red_lamp:
            if int(time.time()) % 2 == 0:
                text = str(fuel_volume)
            else:
                text = ' '
            screen_text = self.red_lamp_font.render(text, True, TColors.red)
            self.screen.blit(screen_text, (self.screen.get_width() - 100, 0))

        if game_paused:
            s = pygame.display.get_surface()
            self.print_text("pause (press spacebar to play)", s.get_width()/2, s.get_height()/2)

