from utils.logging_wrapper import setup_logging
from utils.racing_wheel import TRacingWheel
from utils.colors import TColors
from utils.game_sounds import TSounds
from utils.game_intro import TGameIntro

import pygame
import time
import random
import argparse
import os
import math

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
SPRITES_DIR = os.path.join(ASSETS_DIR, 'sprites')
SOUNDS_DIR = os.path.join(ASSETS_DIR, 'sounds')


class TSprite(pygame.sprite.Sprite):
    def __init__(self, parent, image_file_name, rect):
        super().__init__()
        self.parent = parent
        self.rect = rect
        img = pygame.image.load(os.path.join(SPRITES_DIR, image_file_name))
        self.image = pygame.transform.scale(img, (rect.width, rect.height))

        self.angle = 0
        self.speed_modifier = 1.0

        self.retreat_after_crash = False
        self.sound = None
        self.sound_volume = 0

    def change_spite_position(self, speed):
        self.rect.top += self.speed_modifier * speed


class TSimpleCar(TSprite):
    def __init__(self, parent, top=0, left=0):
        super().__init__(parent,
                              'passenger_car.png',
                              pygame.Rect(left, top, 160, 160))
        self.sound = "normal_driving"
        self.accident_sound = "accident"
        self.speed_modifier = 1.3


class TTruckCar(TSprite):
    def __init__(self, parent, top=0, left=0):
        super().__init__(parent,
                             'truck.png',
                             pygame.Rect(left, top, 160, 260))
        self.sound = "truck"
        self.accident_sound = "accident"
        self.speed_modifier = 1.9


class TractorCar(TSprite):
    def __init__(self, parent, top=0, left=0):
        super().__init__(parent,
                             'tractor.png',
                             pygame.Rect(left, top, 160, 260))
        self.sound = "tractor"
        self.accident_sound = "accident"
        self.speed_modifier = 1
        self.ampl = 300
        self.freq = 0.003
        self.sin_start_point = random.randrange(0, 1000)
        self.path_start_x = left
        self.path_started = False
        self.orig_image = self.image.copy()

    def change_spite_position(self, speed):
        super().change_spite_position(speed)
        if not self.path_started:
            self.path_start_x = self.rect.left
            self.path_started = True
        self.rect.left = self.path_start_x + self.ampl * math.sin(self.freq * self.rect.top + self.sin_start_point)
        angle = math.atan(self.freq * self.ampl * math.cos(self.freq * self.rect.top + self.sin_start_point)) * 180 / math.pi
        self.image = pygame.transform.rotate(self.orig_image, angle)


class TSpider(TSprite):
    def __init__(self, parent, top=0, left=0):
        super().__init__(parent, 'spider.png', pygame.Rect(left, top, 160, 160))
        self.retreat_after_crash = True
        self.sound = "spider"
        self.accident_sound = "spider_accident"
        self.speed_modifier = 1.3


class TMosquito(TSprite):
    def __init__(self, parent, top=0, left=0):
        super().__init__(parent, 'mosquito.png', pygame.Rect(left, top, 160, 160))
        self.retreat_after_crash = True
        self.sound = "mosquito"
        self.accident_sound = "mosquito_accident"
        self.speed_modifier = 1.3


class TPuddle(TSprite):
    def __init__(self, parent, top=0, left=0):
        super().__init__(parent, 'puddle.png', pygame.Rect(left, top, 140, 140))
        self.collided_time = None

    def save_collision(self):
        self.collided_time = time.time()

    def is_new(self):
        return self.collided_time is None or time.time() - self.collided_time > 2


class TRepairPoint(TSprite):
    def __init__(self, parent, top=0, left=0):
        super().__init__(parent, 'repair.png', pygame.Rect(left, top, 140, 140))


class TGameRegisters:
    def __init__(self, screen):
        self.screen = screen
        self.score = 0
        self.game_over = False
        self.missed_count = 0
        self.check_puddle_collision_count = 0
        self.broken = False
        self.paused = False
        self.font = pygame.font.SysFont(None, 30)

    def print_text(self, text, x, y):
        screen_text = self.font.render(text, True, TColors.white)
        self.screen.blit(screen_text, (x, y))

    def draw_params(self, my_car_top, game_speed):
        self.print_text('score: {}'.format(self.score), 30, 0)
        self.print_text('speed: {}'.format(game_speed), 30, 40)
        self.print_text('position: {}'.format(my_car_top), 30, 80)
        self.print_text('broken: {}'.format(self.broken), 30, 120)
        self.print_text('puddles: {}'.format(self.check_puddle_collision_count), 30, 160)
        self.print_text('missed: {}'.format(self.missed_count), 30, 200)
        if self.paused:
            s = pygame.display.get_surface()
            self.print_text("pause (press spacebar to play)", s.get_width()/2, s.get_height()/2)


class TRacesGame:
    def __init__(self, args):
        self.args = args
        self.logger = setup_logging("gonki")
        self.finish_top = 250
        self.start_time_on_the_road_side = None
        self.sounds = TSounds(SOUNDS_DIR, not args.silent)
        self.racing_wheel = TRacingWheel(self.logger, args.wheel_center)
        self.game_speed = args.speed
        self.obstacle_sprites = pygame.sprite.Group()
        self.my_car_sprites = pygame.sprite.Group()
        #assert self.args.mode in {"normal_mode", "gangster_mode"}
        if args.full_screen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            pygame.display.toggle_fullscreen()
            self.width = pygame.display.get_window_size()[0]
            self.height = pygame.display.get_window_size()[1]
        else:
            self.width = 1600
            self.height = 1000
            self.screen = pygame.display.set_mode((self.width, self.height))
        self.stats = TGameRegisters(self.screen)
        self.game_intro = TGameIntro(self.screen, os.path.join(SPRITES_DIR, 'background1.jpg'),  self.racing_wheel)

        self.roadside_width = 200
        blue_strip = pygame.image.load(os.path.join(SPRITES_DIR, 'border.jpg'))
        self.border_img = pygame.transform.scale(blue_strip, (self.roadside_width, self.height))


        self.car_width = 160
        self.my_car = TSprite(self.screen, 'my_car.png', pygame.Rect(0, 0, self.car_width, 160))
        self.my_car_horizontal_speed = 10
        self.my_car_horizontal_speed_increase_with_get_speed = True
        self.my_car_sprites.add(self.my_car)

        #moving obstacles
        self.other_car: TSprite
        self.other_car = None
        self.puddle: TPuddle
        self.puddle = None
        self.repair_point: TRepairPoint
        self.repair_point = None

    def message(self, mess, colour, size, x, y):
        font = pygame.font.SysFont(None, size)
        screen_text = font.render(mess, True, colour)
        self.screen.blit(screen_text, (x, y))
        pygame.display.update()

    def quit(self):
        pygame.quit()
        exit()

    def check_finish(self):
        win = self.finish_top > self.my_car.rect.top
        loose = self.my_car.rect.top > self.height - 100
        if win or loose:
            font = pygame.font.SysFont(None, 100)
            if win:
                if self.stats.score < self.args.great_victory_level:
                    font = pygame.font.SysFont(None, 50)
                    screen_text = font.render('Победа! Очки: {}'.format(self.stats.score), True, TColors.white)
                else:
                    font = pygame.font.SysFont(None, 150)
                    screen_text = font.render('Победа! Очки: {}'.format(self.stats.score), True, TColors.green)
                self.sounds.stop_all_and_play("victory", loops=0)
            else:
                screen_text = font.render('Проигрыш!', True, TColors.white)
            self.screen.blit(screen_text, (250, 280))
            pygame.display.update()
            time.sleep(5)
            self.draw_game_intro(self.stats.score)

    def redraw_background(self):
        self.screen.fill(TColors.gray)
        self.screen.blit(self.border_img, (0, 0))
        self.screen.blit(self.border_img, (self.width - self.roadside_width, 0))
        pygame.draw.line(self.screen, TColors.white, (self.roadside_width, self.finish_top),
                         (self.width - self.roadside_width, self.finish_top))

    def check_puddle_collision(self):
        if self.puddle is None or not self.puddle.alive() or  not self.puddle.is_new():
            return
        self.logger.debug("puddle collision")
        self.sounds.stop_all_and_play("puddle_accident", loops=0)
        time.sleep(1)
        self.puddle.save_collision()
        self.stats.check_puddle_collision_count += 1
        self.stats.score -= 1
        self.stats.broken = True
        self.update_music()

    def check_repair_collision(self):
        if not self.stats.broken or self.repair_point is None or not self.repair_point.alive():
            return
        self.logger.debug("repair collision")
        self.sounds.stop_all_and_play("repair_car", loops=0)
        time.sleep(3)
        self.stats.broken = False
        self.update_music()

    def car_crash(self):
        self.logger.debug("car_crash")
        self.sounds.stop_all_and_play(self.other_car.accident_sound, loops=0)
        if self.other_car.retreat_after_crash:
            while self.other_car.rect.top > 0:
                self.other_car.rect.top -= 30
                self.other_car.rect.left += random.randint(1, 30) - 15
                self.redraw_all()
                time.sleep(0.1)
        else:
            self.message('Авария', TColors.red, 100, 250, 280)
            time.sleep(3)

        if self.args.mode == "normal_mode":
            if isinstance(self.other_car, TSpider) or isinstance(self.other_car, TMosquito):
                self.my_car.rect.top -= 20
            else:
                self.my_car.rect.top += 20
        elif self.args.mode == "gangster_mode":
            if isinstance(self.other_car, TTruckCar):
                self.my_car.rect.top -= 40
            else:
                self.my_car.rect.top -= 20
            if not self.is_broken_driving():
                self.stats.score += 1
        self.init_new_other_car()
        pygame.display.update()

    def is_on_the_roadside(self):
        return self.my_car.rect.left < self.roadside_width or self.my_car.rect.right > self.width - self.roadside_width

    def draw_game_intro(self, prev_score=None):
        self.sounds.stop_sounds()
        self.game_intro.get_next_action(prev_score)
        if self.game_intro.action == TGameIntro.exit_game_action:
            self.quit()
        elif self.game_intro.action == TGameIntro.start_game_action:
            self.game_loop()
        else:
            raise Exception("unknown action")

    def set_other_car_random_position(self, sprite: TSprite, padding):
        sprite.rect.top = 0
        sprite.rect.left = random.randrange(self.roadside_width + padding, self.width - self.roadside_width - self.car_width - padding)

    def is_broken_driving(self):
        return self.stats.broken

    def init_new_other_car(self):
        self.logger.debug("init_new_other_car")
        if self.other_car is not None:
            self.other_car.kill()
            self.other_car = None

        enemy_car_types = [TSimpleCar, TTruckCar, TractorCar, TSpider, TMosquito]
        enemy_cars_weights = [2,           1.5,     1,           1,     1]
        #enemy_cars_weights = [0, 0, 1, 0, 0]
        other_car_type = random.choices(population=enemy_car_types, weights=enemy_cars_weights, k=1)[0]
        self.other_car = other_car_type(self.screen)
        padding = 0
        if other_car_type == TractorCar:
            padding += self.other_car.ampl
        self.set_other_car_random_position(self.other_car, padding)
        self.obstacle_sprites.add(self.other_car)
        self.update_music()

    def get_speed(self):
        if self.is_on_the_roadside():
            if self.start_time_on_the_road_side is None:
                self.start_time_on_the_road_side = time.time()
            time_on_the_road_side = time.time() - self.start_time_on_the_road_side
            if time_on_the_road_side < 3:
                return max(int(self.game_speed / 2), 1)
            elif time_on_the_road_side < 5:
                return 1
            else:
                return 0
        else:
            return self.game_speed

    def is_obstacle_finish(self, sprite: TSprite):
        return sprite.rect.top > min(self.height - 100, self.my_car.rect.bottom + 200)

    def change_obstacle_positions(self):
        if self.puddle is not None:
            self.puddle.change_spite_position(self.get_speed())
            if self.is_obstacle_finish(self.puddle):
                self.puddle.kill()
                self.puddle = None

        if self.repair_point is not None:
            self.repair_point.change_spite_position(self.get_speed())
            if self.is_obstacle_finish(self.repair_point):
                self.repair_point.kill()
                self.repair_point = None

        self.other_car.change_spite_position(self.get_speed())
        if self.is_obstacle_finish(self.other_car):
            if not self.is_on_the_roadside():
                if self.args.mode == "normal_mode":
                    self.stats.score += 1
            if self.args.mode == "normal_mode":
                if isinstance(self.other_car, TSpider) or isinstance(self.other_car, TMosquito):
                    self.my_car.rect.top += 10
                else:
                    self.my_car.rect.top -= 20
            if self.args.mode == "gangster_mode":
                self.stats.missed_count += 1
                self.stats.score -= 1
            self.init_new_other_car()

    def init_puddle(self):
        if self.puddle is not None or self.stats.paused:
            return
        if random.random() > 0.9:
            return
        self.logger.debug("init_puddle")
        self.puddle = TPuddle(self.screen)
        self.set_other_car_random_position(self.puddle, 0)
        self.obstacle_sprites.add(self.puddle)

    def init_repair_point(self):
        if self.repair_point is not None or self.stats.paused:
            return
        if random.random() > 0.9:
            return

        self.logger.debug("init_repair_point")
        self.repair_point = TRepairPoint(self.screen)
        self.repair_point.top = 0
        if random.random() > 0.5:
            self.repair_point.rect.left = 0
        else:
            self.repair_point.rect.left = self.width - self.roadside_width
        self.obstacle_sprites.add(self.repair_point)

    def process_keyboard_and_wheel_events(self, x_change):
        wheel_angle = self.racing_wheel.get_angle()
        if wheel_angle is not None:
            x_change = wheel_angle

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.stats.game_over = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    x_change = -self.my_car_horizontal_speed
                elif event.key == pygame.K_RIGHT:
                    x_change = +self.my_car_horizontal_speed
                elif event.key == pygame.K_UP:
                    self.game_speed += 1
                elif event.key == pygame.K_DOWN:
                    self.game_speed = max(self.game_speed - 1, 1)
                elif event.key == pygame.K_ESCAPE:
                    self.draw_game_intro()
                elif event.key == pygame.K_SPACE:
                    self.stats.paused = not self.stats.paused
                elif event.key == pygame.K_F1:
                    self.racing_wheel.save_wheel_center()

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    x_change = 0
        if self.my_car_horizontal_speed_increase_with_get_speed:
            x_change += 0.01 * x_change * math.sqrt(self.get_speed())

        self.my_car.rect.left += x_change
        if self.my_car.rect.left < 0:
            self.my_car.rect.left = 0
        if self.my_car.rect.left > self.width - 50:
            self.my_car.rect.left = self.width - 50
        return x_change

    def process_wheel_pedals(self):
        if self.stats.paused:
            return
        if self.racing_wheel.is_left_pedal_pressed():
            self.sounds.play_sound("car_honk_left")
            if isinstance(self.other_car, TMosquito):
                time.sleep(1)
                self.car_crash()

        if self.racing_wheel.is_right_pedal_pressed():
            self.sounds.play_sound("car_honk_right")
            if isinstance(self.other_car, TSpider):
                time.sleep(1)
                self.car_crash()

    def update_music(self):
        self.logger.debug("update_music")
        if self.is_on_the_roadside():
            self.sounds.stop_all_and_play("roadside")
        else:
            self.logger.debug("stop_all_and_play other_car.sound")
            self.sounds.stop_all_and_play(self.other_car.sound)
            if self.is_broken_driving():
                self.logger.debug("add  music broken driving")
                self.sounds.play_sound("broken_driving")

    def redraw_all(self):
        self.redraw_background()
        self.stats.draw_params(self.my_car.rect.top, self.game_speed)
        #pygame.draw.rect(self.screen, TColors.black, self.other_car.rect, width=1)
        #pygame.draw.rect(self.screen, TColors.black, self.my_car.rect, width=1)
        self.obstacle_sprites.draw(self.screen)
        self.my_car_sprites.draw(self.screen)
        pygame.display.flip()

    def check_all_collisions(self):
        c = pygame.sprite.spritecollideany(self.my_car, self.obstacle_sprites,
                                                  collided=pygame.sprite.collide_mask)
        if c == self.other_car:
            self.car_crash()
        elif c == self.puddle:
            self.check_puddle_collision()
        elif c == self.repair_point:
            self.check_repair_collision()

    def game_loop(self):
        self.obstacle_sprites.empty()
        self.my_car.rect.left = self.width / 2
        self.my_car.rect.top = self.height - 250
        #self.my_car.rect.top = self.height - 650
        self.stats = TGameRegisters(self.screen)
        self.redraw_background()
        self.init_new_other_car()
        save_is_on_road_side = False
        self.sounds.stop_all_and_play(self.other_car.sound)
        x_change = 0
        while not self.stats.game_over:
            assert len(self.obstacle_sprites) <= 3
            self.init_puddle()
            self.init_repair_point()
            self.process_wheel_pedals()
            x_change = self.process_keyboard_and_wheel_events(x_change)
            if not self.stats.paused:
                self.change_obstacle_positions()
            self.check_finish()
            self.check_all_collisions()
            if save_is_on_road_side != self.is_on_the_roadside():
                save_is_on_road_side = self.is_on_the_roadside()
                if self.is_on_the_roadside():
                    self.start_time_on_the_road_side = time.time()
                else:
                    self.start_time_on_the_road_side = None
                self.update_music()

            self.redraw_all()

            clock.tick(30)

            if self.my_car.rect.top + 30 > self.height:
                self.my_car.rect.top = self.height - 30


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--silent", dest='silent', default=False, action="store_true")
    parser.add_argument("--wheel-center", dest='wheel_center', default=300, type=int)
    parser.add_argument("--speed", dest='speed', default=6, type=int)
    parser.add_argument("--great-victory-level", dest='great_victory_level', default=15, type=int)
    parser.add_argument("--full-screen", dest='full_screen', default=False, action="store_true")
    parser.add_argument("--mode", dest='mode', default="normal_mode", required=False, help="can be normal_mode,gangster_mode")
    return parser.parse_args()


if __name__ == "__main__":
    clock = pygame.time.Clock()
    args = parse_args()
    pygame.display.init()
    pygame.font.init()
    game = TRacesGame(args)
    game.draw_game_intro()
    game.quit()
