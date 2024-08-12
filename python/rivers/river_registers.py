from utils.colors import TColors

import pygame




class TGameRegisters:
    def __init__(self, screen: pygame.Surface):
        self.screen: pygame.Surface = screen
        self.game_over = False
        self.river_accident_count = 0
        self.bridge_passing_count = 0
        self.success_tasks_count = 0
        self.paused = False
        self.map_parts_count = 0

        self.map_parts_count = 0
        self.font = pygame.font.SysFont(None, 30)
        self.red_lamp_font = pygame.font.SysFont(None, 230)
        self.is_on_alarm = True
        self.count_call = 0
        self.engine = False
        self.my_car = None

    def restart_stats(self):
        self.game_over = False
        self.river_accident_count = 0
        self.bridge_passing_count = 0
        self.success_tasks_count = 0
        self.paused = False
        self.map_parts_count = 0
        self.map_parts_count = 0
        self.is_on_alarm = True
        self.count_call = 0


    def set_my_car_ref(self, my_car):
        self.my_car = my_car

    def print_text(self, text, x, y):
        screen_text = self.font.render(text, True, TColors.white)
        self.screen.blit(screen_text, (x, y))

    def get_score(self):
        return self.bridge_passing_count - self.river_accident_count + self.success_tasks_count

    def increment_map_parts_count(self):
        self.map_parts_count += 1

        if (self.map_parts_count % 3) == 0:
            if not self.my_car.decrement_fuel():
                return False
        return True

    def draw_params(self, my_car_top, game_speed, car_is_broken, broken_tires):
        self.count_call +=1
        self.print_text('score: {}'.format(self.get_score()), 30, 0)
        self.print_text('speed: {}'.format(game_speed), 30, 30)
        self.print_text('position: {}'.format(my_car_top), 30, 60)
        self.print_text('rivers: {}'.format(self.river_accident_count), 30, 90)
        self.print_text('bridges: {}'.format(self.bridge_passing_count), 30, 120)
        self.print_text('success tasks: {}'.format(self.success_tasks_count), 30, 150)
        self.print_text('broken: {}'.format(car_is_broken), 30, 180)
        self.print_text('km: {}'.format(self.map_parts_count), 30, 210)
        self.print_text('fuel: {}'.format(self.my_car.get_fuel_volume()), 30, 240)
        self.print_text('alarm: {}'.format(self.is_on_alarm), 30, 270)
        self.print_text('engine: {}'.format(self.my_car.engine), 30, 300)
        self.print_text('tires: {}'.format(not broken_tires), 30, 330)
        if self.my_car.need_fuel():
            if self.count_call % 8 < 4:
                text = str(self.my_car.get_fuel_volume())
            else:
                text = ' '
            screen_text = self.red_lamp_font.render(text, True, TColors.red)
            self.screen.blit(screen_text, (self.screen.get_width() - 100, 0))

        if self.paused:
            s = pygame.display.get_surface()
            self.print_text("pause (press spacebar to play)", s.get_width()/2, s.get_height()/2)

