import pygame
import time
import random
import argparse
from evdev import list_devices, InputDevice, ecodes
import os
import math
import logging

ASSETS_DIR = "assets"
SPRITES_DIR = os.path.join(ASSETS_DIR, 'sprites')
SOUNDS_DIR = os.path.join(ASSETS_DIR, 'sounds')


def setup_logging():
    logger_name = "gonki"
    log_file_name = "gonki.log"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # create file handler which logs even debug messages
    if log_file_name is not None:
        if os.path.exists(log_file_name):
            os.remove(log_file_name)
        fh = logging.FileHandler(log_file_name, encoding="utf8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)

    return logger


class TColors:
    gray = (119, 118, 110)
    white = (255, 255, 255)
    black = (0, 0, 0)
    red = (200, 0, 0)
    green = (0, 200, 0)
    bright_red = (255, 0, 0)
    bright_green = (0, 255, 0)


class TSprite:
    def __init__(self, gd, image_file_name, top, left, width, height, hitbox_padding=0):
        self.gd = gd
        self.top = top
        self.left = left
        self.width = width
        self.height = height
        self.hitbox_padding = hitbox_padding
        self.angle = 0
        self.image = pygame.transform.scale(pygame.image.load(image_file_name), (width, height))

    def draw(self):
        self.gd.blit(pygame.transform.rotate(self.image, self.angle), (self.left, self.top))

    def hitbox_left(self):
        return self.left + self.hitbox_padding

    def hitbox_top(self):
        return self.top + self.hitbox_padding

    def hitbox_right(self):
        return self.left + self.width - self.hitbox_padding

    def right(self):
        return self.left + self.width

    def hitbox_bottom(self):
        return self.top + self.height - self.hitbox_padding

    def bottom(self):
        return self.top + self.height

    def intersect(self, other):
        return self.hitbox_left() <= other.hitbox_right() and \
          other.hitbox_left() <= self.hitbox_right() and \
          self.hitbox_top() <= other.hitbox_bottom() and \
          other.hitbox_top() <= self.hitbox_bottom()
    
    def rotate(self, angle):
        self.angle = angle


class TRacingWheel:
    left_button = 295
    right_button = 294
    left_pedal =  10
    right_pedal = 9

    def __init__(self, center):
        self.raw_angle = None
        self.center = center
        self.pressed_buttons = set()
        joysticks = list_devices()
        if len(joysticks) > 0:
            self.device = InputDevice(joysticks[0])
            self.read_events()
        else:
            print ("no racing wheel found")
            self.device = None

    def save_wheel_center(self):
        if self.raw_angle is not None:
            print("set wheel center to {}".format(self.raw_angle))
            self.center = self.raw_angle

    def forget_buttons(self):
        self.pressed_buttons.clear()

    def read_events(self):
        if self.device is None:
            return
        event = self.device.read_one()
        while event is not None:
            if event.code == ecodes.ABS_WHEEL:
                self.raw_angle = event.value
                print("abs_wheel value={}, center={}".format(self.raw_angle, self.center))
            if event.code == TRacingWheel.left_button:
                print ("left_button")
                self.pressed_buttons.add(TRacingWheel.left_button)
            elif event.code == TRacingWheel.right_button:
                print ("right_button")
                self.pressed_buttons.add(TRacingWheel.right_button)
            elif event.code == TRacingWheel.left_pedal:
                if event.value > 120:
                    self.pressed_buttons.add(TRacingWheel.left_pedal)
                else:
                    if TRacingWheel.left_pedal in self.pressed_buttons:
                        self.pressed_buttons.remove(TRacingWheel.left_pedal)
                print("left_pedal value={} {}".format(event.value, self.pressed_buttons))
            elif event.code == TRacingWheel.right_pedal:
                print("right_pedal")
                if event.value > 120:
                    self.pressed_buttons.add(TRacingWheel.right_pedal)
                else:
                    if TRacingWheel.right_pedal in self.pressed_buttons:
                        self.pressed_buttons.remove(TRacingWheel.right_pedal)


            event = self.device.read_one()

    def is_left_pedal_pressed(self):
        return TRacingWheel.left_pedal in self.pressed_buttons

    def is_right_pedal_pressed(self):
        return TRacingWheel.right_pedal in self.pressed_buttons

    def get_angle(self):
        self.read_events()
        if self.raw_angle is not None:
            return int((self.raw_angle - self.center) / 50)


def load_sound(file_path, volume):
    sound = pygame.mixer.Sound(file_path)
    sound.set_volume(volume)
    return sound


class TMovingObstacle:
    def __init__(self):
        self.image = None
        self.speed_modifier = 1.0

    def change_spite_position(self, speed):
        self.image.top += self.speed_modifier * speed


class TCar(TMovingObstacle):
    def __init__(self):
        super().__init__()
        self.retreat_after_crash = False
        self.sound = None
        self.width = 0
        self.height = 0
        self.sound_volume = 0
        self.spawn_weight = 0


class TSimpleCar(TCar):
    def __init__(self, gd, top=0, left=0):
        super().__init__()
        self.width = 160
        self.height = 160
        self.image = TSprite(gd, os.path.join(SPRITES_DIR, 'passenger_car.png'), top, left, self.width, self.height)
        self.sound = TSounds.normal_driving
        self.accident_sound = TSounds.accident
        self.speed_modifier = 1.3
        self.spawn_weight = 2


class TTruckCar(TCar):
    def __init__(self, gd, top=0, left=0):
        super().__init__()
        self.width = 160
        self.height = 260
        self.image = TSprite(gd, os.path.join(SPRITES_DIR, 'truck.png'), top, left, self.width, self.height)
        self.sound = TSounds.truck
        self.accident_sound = TSounds.accident
        self.speed_modifier = 1.9
        self.spawn_weight = 1.5


class TractorCar(TCar):
    def __init__(self, gd, top=0, left=0):
        super().__init__()
        self.width = 160
        self.height = 260
        self.image = TSprite(gd, os.path.join(SPRITES_DIR, 'tractor.png'), top, left, self.width,
                             self.height, hitbox_padding=50)
        self.sound = TSounds.tractor
        self.accident_sound = TSounds.accident
        self.speed_modifier = 1
        self.spawn_weight = 1
        self.ampl = 300
        self.freq = 0.003
        self.sin_start_point = random.randrange(0, 1000)
        self.path_start_x = left
        self.path_started = False

    def change_spite_position(self, speed):
        super().change_spite_position(speed)
        if not self.path_started:
            self.path_start_x = self.image.left
            self.path_started = True
        self.image.left = self.path_start_x + self.ampl * math.sin(self.freq * self.image.top + self.sin_start_point)
        self.image.rotate(math.atan(self.freq * self.ampl * math.cos(self.freq * self.image.top + self.sin_start_point)) * 180 / math.pi)


class TSpider(TCar):
    def __init__(self, gd, top=0, left=0):
        super().__init__()
        self.retreat_after_crash = True
        self.width = 160
        self.height = 160
        self.image = TSprite(gd, os.path.join(SPRITES_DIR, 'spider.png'), top, left, self.width, self.height)
        self.sound = TSounds.spider
        self.accident_sound = TSounds.spider_accident
        self.speed_modifier = 1.3
        self.spawn_weight = 1


class TMosquito(TCar):
    def __init__(self, gd, top=0, left=0):
        super().__init__()
        self.retreat_after_crash = True
        self.width = 160
        self.height = 160
        self.image = TSprite(gd, os.path.join(SPRITES_DIR, 'mosquito.png'), top, left, self.width, self.height)
        self.sound = TSounds.mosquito
        self.accident_sound = TSounds.mosquito_accident
        self.speed_modifier = 1.3
        self.spawn_weight = 1


class TPuddle(TMovingObstacle):
    def __init__(self, gd, top=0, left=0):
        super().__init__()
        self.width = 160
        self.height = 160
        self.image = TSprite(gd, os.path.join(SPRITES_DIR, 'puddle.png'), top, left,
                             self.width, self.height, hitbox_padding=50)
        self.collision_sound = TSounds.puddle_accident
        self.collided = False


class TRepairPoint(TMovingObstacle):
    def __init__(self, gd, top=0, left=0):
        super().__init__()
        self.width = 140
        self.height = 140
        self.image = TSprite(gd, os.path.join(SPRITES_DIR, 'repair.png'), top, left,
                             self.width, self.height, hitbox_padding=20)


class TSounds:
    roadside = 1
    normal_driving = 2
    accident = 3
    victory = 4
    truck = 5
    tractor = 6
    spider = 7
    spider_accident = 8
    mosquito = 9
    mosquito_accident = 10
    car_honk_left = 11
    car_honk_right = 12
    puddle_accident = 13
    broken_driving = 14
    repair_car = 15

    def __init__(self, enable_sounds):
        self.enable_sounds = enable_sounds
        self.sounds = dict()
        if self.enable_sounds:
            pygame.mixer.init()
            self.sounds = {
                self.roadside: load_sound(os.path.join(SOUNDS_DIR, "roadside.wav"), 0.4),
                self.normal_driving: load_sound(os.path.join(SOUNDS_DIR, "normal_driving.wav"), 0.3),
                self.accident: load_sound(os.path.join(SOUNDS_DIR, "accident.wav"), 1),
                self.victory: load_sound(os.path.join(SOUNDS_DIR, "victory.wav"), 1),
                self.truck: load_sound(os.path.join(SOUNDS_DIR, "truck.wav"), 0.6),
                self.tractor: load_sound(os.path.join(SOUNDS_DIR, "tractor.wav"), 1),
                self.spider: load_sound(os.path.join(SOUNDS_DIR, "spider.wav"), 0.2),
                self.spider_accident: load_sound(os.path.join(SOUNDS_DIR, "spider_accident.wav"), 1),
                self.mosquito: load_sound(os.path.join(SOUNDS_DIR, "mosquito.wav"), 0.2),
                self.mosquito_accident: load_sound(os.path.join(SOUNDS_DIR, "mosquito_accident.wav"), 0.2),
                self.car_honk_left: load_sound(os.path.join(SOUNDS_DIR, "car_honk_left.wav"), 0.3),
                self.car_honk_right: load_sound(os.path.join(SOUNDS_DIR, "car_honk_right.wav"), 0.3),
                self.puddle_accident: load_sound(os.path.join(SOUNDS_DIR, "puddle.wav"), 0.3),
                self.broken_driving: load_sound(os.path.join(SOUNDS_DIR, "broken_driving.wav"), 0.3),
                self.repair_car: load_sound(os.path.join(SOUNDS_DIR, "repair_car.wav"), 0.3),
            }

    def stop_sounds(self):
        if self.enable_sounds:
            for k in  self.sounds.values():
                k.stop()

    def switch_music(self, sound_type, loops=1000):
        if self.enable_sounds:
            self.stop_sounds()
            self.sounds[sound_type].play(loops=loops)

    def play_sound(self, sound_type):
        self.sounds[sound_type].play()


class TRacesGame:
    def __init__(self, args):
        self.args = args
        self.logger = setup_logging()
        #assert self.args.mode in {"normal_mode", "gangster_mode"}
        pygame.display.init()
        pygame.font.init()
        if args.full_screen:
            self.gd = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            pygame.display.toggle_fullscreen()
            self.width = pygame.display.get_window_size()[0]
            self.height = pygame.display.get_window_size()[1]
        else:
            self.width = 1600
            self.height = 1000
            self.gd = pygame.display.set_mode((self.width, self.height))

        self.roadside_width = 200
        self.car_width = 160
        self.my_car = TSprite(self.gd, os.path.join(SPRITES_DIR, 'my_car.png'), 0, 0, self.car_width, 160)

        self.enemy_car_types = [TSimpleCar, TTruckCar, TractorCar, TSpider, TMosquito]
        enemy_cars = []
        for car in self.enemy_car_types:
            enemy_cars.append(car(self.gd))
        self.enemy_cars_weights = [car.spawn_weight for car in enemy_cars]
        del enemy_cars

        self.other_car = None
        self.game_over = False
        self.score = 0
        self.finish_top = 250
        self.start_time_on_the_road_side = None
        self.other_car_sound = None
        self.other_car_spawn_x = 0
        self.sounds = TSounds(not args.silent)
        self.paused = False

        self.game_speed = 10
        self.my_car_horizontal_speed = 10
        self.my_car_horizontal_speed_increase_with_get_speed = True
        self.racing_wheel = TRacingWheel(args.wheel_center)
        self.font = pygame.font.SysFont(None, 30)
        self.puddle = None
        self.broken = False
        self.repair_point = None

    def message(self, mess, colour, size, x, y):
        font = pygame.font.SysFont(None, size)
        screen_text = font.render(mess, True, colour)
        self.gd.blit(screen_text, (x, y))
        pygame.display.update()

    def button(self, x, y, w, h, mess, mess_color, actc, noc, size, tx, ty, func):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        if x + w > mouse[0] > x and y + h > mouse[1] > y:
            pygame.draw.rect(self.gd, actc, [x, y, w, h])
            self.message(mess, mess_color, size, tx, ty)
            pygame.display.update()
            if click == (1, 0, 0):
                func()
        else:
            pygame.draw.rect(self.gd, noc, [x, y, w, h])
            self.message(mess, mess_color, size, tx, ty)
            pygame.display.update()
        pygame.display.update()

    def quit(self):
        pygame.quit()
        exit()

    def draw_background(self):
        blue_strip = pygame.image.load(os.path.join(SPRITES_DIR, 'border.jpg'))

        img = pygame.transform.scale(blue_strip, (self.roadside_width, self.height))
        self.gd.blit(img, (0, 0))
        self.gd.blit(img, (self.width - self.roadside_width, 0))
        pygame.draw.line(self.gd, TColors.white, (self.roadside_width, self.finish_top), (self.width-self.roadside_width, self.finish_top))

    def check_finish(self):
        win = self.finish_top > self.my_car.top
        loose = self.my_car.top > self.height - 100
        if win or loose:
            font = pygame.font.SysFont(None, 100)
            if win:
                screen_text = font.render('Победа!', True, TColors.green)
                self.sounds.switch_music(TSounds.victory, loops=0)
            else:
                screen_text = font.render('Проигрыш!', True, TColors.white)
            self.gd.blit(screen_text, (250, 280))
            pygame.display.update()
            time.sleep(3)
            self.game_intro()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
            pygame.display.update()

    def redraw(self):
        self.gd.fill(TColors.gray)
        self.draw_background()
        if self.puddle is not None:
            self.puddle.image.draw()
        if self.repair_point is not None:
            self.repair_point.image.draw()
        self.my_car.draw()
        self.other_car.image.draw()

    def puddle_collision(self):
        if self.puddle is None:
            return
        if not self.my_car.intersect(self.puddle.image):
            return
        if not self.puddle.collided:
            self.logger.debug("puddle collision")
            self.sounds.switch_music(self.puddle.collision_sound, loops=0)
            time.sleep(1)
            self.puddle.collided = True
            self.puddle_collision_count += 1
            self.broken = True
            self.switch_music()

    def repair_collision(self):
        if self.repair_point is None:
            return
        if not self.my_car.intersect(self.repair_point.image):
            return
        if self.broken:
            self.logger.debug("repair collision")
            self.sounds.switch_music(TSounds.repair_car, loops=0)
            time.sleep(3)
            self.broken = False
            self.switch_music()

    def car_crash(self):
        self.logger.debug("car_crash")
        self.sounds.switch_music(self.other_car.accident_sound, loops=0)
        if self.other_car.retreat_after_crash:
            for x in range(20):
                self.other_car.image.top -= 30
                self.other_car.image.left += random.randint(1, 30) - 15
                self.redraw()
                pygame.display.update()
                time.sleep(0.1)
        else:
            self.message('Авария', TColors.red, 100, 250, 280)
            time.sleep(3)

        if self.args.mode == "normal_mode":
            if isinstance(self.other_car, TSpider) or isinstance(self.other_car, TMosquito):
                self.my_car.top -= 20
            else:
                self.my_car.top += 20
        elif self.args.mode == "gangster_mode":
            if isinstance(self.other_car, TTruckCar):
                self.my_car.top -= 40
            else:
                self.my_car.top -= 20
            self.score += 1
        self.init_new_other_car()
        pygame.display.update()

    def is_on_the_roadside(self):
        return self.my_car.left < self.roadside_width or self.my_car.right() > self.width - self.roadside_width

    def print_text(self, text, x, y):
        screen_text = self.font.render(text, True, TColors.white)
        self.gd.blit(screen_text, (x, y))

    def draw_params(self):
        font = pygame.font.SysFont(None, 30)
        self.print_text('score: {}'.format(self.score), 30, 0)
        self.print_text('speed: {}'.format(self.game_speed), 30, 40)
        self.print_text('position: {}'.format(self.my_car.top), 30, 80)
        self.print_text('broken: {}'.format(self.is_broken_driving()), 30, 120)
        self.print_text('puddles: {}'.format(self.puddle_collision_count), 30, 160)

        if self.paused:
            self.print_text("pause (press spacebar to play)", self.width/2, self.height/2)

        pygame.display.update()

    def game_intro(self):
        def draw_button(x, y, message, color,  func):
            self.button(x, y, 70, 30, message, TColors.white, color, TColors.red, 25, x + 6,
                        y + 6, func)

        self.sounds.stop_sounds()
        v = pygame.transform.scale(pygame.image.load(os.path.join(SPRITES_DIR, 'background1.jpg')), (self.width, self.height))
        self.gd.blit(v, (0, 0))
        pygame.display.update()
        game_intro = False
        while not game_intro:
            self.racing_wheel.forget_buttons()
            self.racing_wheel.read_events()
            if TRacingWheel.left_button in self.racing_wheel.pressed_buttons:
                self.game_loop()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_intro = True
                    self.game_over = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F1:
                        self.racing_wheel.save_wheel_center()
                    if event.key == pygame.K_ESCAPE:
                        self.quit()

            self.message('MAIN MENU', TColors.green, 100, (self.width / 2 - 220), 100)
            button_y = 300
            draw_button(200, button_y, 'GO!', TColors.bright_red, self.game_loop)
            draw_button(self.width - 200, button_y, 'QUIT', TColors.bright_green, self.quit)
            pygame.display.update()

        pygame.display.update()

    def set_other_car_random_position(self, sprite: TSprite, padding):
        sprite.top = 0
        sprite.left = random.randrange(self.roadside_width + padding, self.width - self.roadside_width - self.car_width - padding)

    def is_broken_driving(self):
        return self.broken

    def init_new_other_car(self):
        self.logger.debug("init_new_other_car")
        other_car_type = random.choices(population=self.enemy_car_types, weights=self.enemy_cars_weights, k=1)[0]
        self.other_car = other_car_type(self.gd)
        padding = 0
        if other_car_type == TractorCar:
            padding += self.other_car.ampl
        self.set_other_car_random_position(self.other_car.image, padding)
        self.switch_music()

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
        return sprite.top > min(self.height - 100, self.my_car.bottom() + 200)

    def change_obstacle_positions(self):
        self.other_car.change_spite_position(self.get_speed())
        if self.puddle is not None:
            self.puddle.change_spite_position(self.get_speed())
            if self.is_obstacle_finish(self.puddle.image):
                self.puddle = None

        if self.repair_point is not None:
            self.repair_point.change_spite_position(self.get_speed())
            if self.is_obstacle_finish(self.repair_point.image):
                self.repair_point = None

        if self.is_obstacle_finish(self.other_car.image):
            if not self.is_on_the_roadside():
                if self.args.mode == "normal_mode":
                    self.score += 1
            if self.args.mode == "normal_mode":
                if isinstance(self.other_car, TSpider) or isinstance(self.other_car, TMosquito):
                    self.my_car.top += 10
                else:
                    self.my_car.top -= 20
            self.init_new_other_car()

    def init_puddle(self):
        if self.puddle is not None or self.paused:
            return
        if random.random() > 0.9:
            return
        self.logger.debug("init_puddle")
        self.puddle = TPuddle(self.gd)
        self.set_other_car_random_position(self.puddle.image, 0)

    def init_repair_point(self):
        if self.repair_point is not None or self.paused:
            return
        if random.random() > 0.9:
            return

        self.logger.debug("init_repair_point")
        self.repair_point = TRepairPoint(self.gd)
        self.repair_point.top = 0
        if random.random() > 0.5:
            self.repair_point.image.left = 0
        else:
            self.repair_point.image.left = self.width - self.roadside_width

    def process_keyboard_and_wheel_events(self, x_change):
        wheel_angle = self.racing_wheel.get_angle()
        if wheel_angle is not None:
            x_change = wheel_angle

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game_over = True
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
                        self.game_intro()
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_F1:
                    self.save_wheel_center()

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    x_change = 0
        if self.my_car_horizontal_speed_increase_with_get_speed:
            x_change += 0.01 * x_change * math.sqrt(self.get_speed())

        self.my_car.left += x_change
        if self.my_car.left < 0:
            self.my_car.left = 0
        if self.my_car.left > self.width - 50:
            self.my_car.left = self.width - 50
        return x_change

    def process_wheel_pedals(self):
        if self.paused:
            return
        if self.racing_wheel.is_left_pedal_pressed():
            self.sounds.play_sound(TSounds.car_honk_left)
            if isinstance(self.other_car, TMosquito):
                time.sleep(1)
                self.car_crash()

        if self.racing_wheel.is_right_pedal_pressed():
            self.sounds.play_sound(TSounds.car_honk_right)
            if isinstance(self.other_car, TSpider):
                time.sleep(1)
                self.car_crash()

    def switch_music(self):
        self.logger.debug("switch_music")
        if self.is_on_the_roadside():
            self.logger.debug("switch_music TSounds.roadside")
            self.sounds.switch_music(TSounds.roadside)
        else:
            self.logger.debug("switch_music other_car.sound")
            self.sounds.switch_music(self.other_car.sound)
            if self.is_broken_driving():
                self.logger.debug("add  music broken driving")
                self.sounds.play_sound(self.sounds.broken_driving)

    def game_loop(self):
        self.my_car.left = self.width / 2
        self.my_car.top = self.height - 250
        self.game_over = False
        self.score = 0
        self.puddle_collision_count = 0
        self.init_new_other_car()
        save_is_on_road_side = False
        self.sounds.switch_music(self.other_car.sound)
        x_change = 0
        self.broken = False
        while not self.game_over:
            self.init_puddle()
            self.init_repair_point()
            self.process_wheel_pedals()
            x_change = self.process_keyboard_and_wheel_events(x_change)
            if not self.paused:
                self.change_obstacle_positions()
            self.redraw()
            self.check_finish()
            if self.my_car.intersect(self.other_car.image):
                self.car_crash()
            self.puddle_collision()
            self.repair_collision()
            self.draw_params()
            if save_is_on_road_side != self.is_on_the_roadside():
                save_is_on_road_side = self.is_on_the_roadside()
                if self.is_on_the_roadside():
                    self.start_time_on_the_road_side = time.time()
                else:
                    self.start_time_on_the_road_side = None
                self.switch_music()

            clock.tick(30)
            if self.my_car.top + 30 > self.height:
                self.my_car.top = self.height - 30
            pygame.display.update()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--silent", dest='silent', default=False, action="store_true")
    parser.add_argument("--wheel-center", dest='wheel_center', default=300, type=int)
    parser.add_argument("--full-screen", dest='full_screen', default=False, action="store_true")
    parser.add_argument("--mode", dest='mode', default="normal_mode", required=False, help="can be normal_mode,gangster_mode")
    return parser.parse_args()


if __name__ == "__main__":
    clock = pygame.time.Clock()
    args = parse_args()
    game = TRacesGame(args)
    game.game_intro()
    game.quit()
