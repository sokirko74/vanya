import pygame
import time
import random
import argparse
from evdev import list_devices, InputDevice, categorize, ecodes
import os
import math

ASSETS_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'assets')
SPRITES_DIR = os.path.join(ASSETS_DIR, 'sprites')
SOUNDS_DIR = os.path.join(ASSETS_DIR, 'sounds')

class TColors:
    gray = (119, 118, 110)
    white = (255, 255, 255)
    black = (0, 0, 0)
    red = (200, 0, 0)
    green = (0, 200, 0)
    bright_red = (255, 0, 0)
    bright_green = (0, 255, 0)


class TSprite:
    def __init__(self, gd, image_file_name, top, left, width, height):
        self.gd = gd
        self.top = top
        self.left = left
        self.width = width
        self.height = height
        self.hitbox_size_decrease = 0
        self.angle = 0
        self.image = pygame.transform.scale(pygame.image.load(image_file_name), (width, height))

    def draw(self):
        self.gd.blit(pygame.transform.rotate(self.image, self.angle), (self.left, self.top))

    def right(self):
        return self.left + self.width

    def bottom(self):
        return self.top + self.height

    def intersect(self, other, possible_collision=10):
        return self.left + self.hitbox_size_decrease + possible_collision <= other.right() and \
          other.left + self.hitbox_size_decrease + possible_collision <= self.right() and \
          self.top + self.hitbox_size_decrease + possible_collision <= other.bottom() and \
          other.top + self.hitbox_size_decrease + possible_collision <= self.bottom()
    
    def rotate(self, angle):
        self.angle = angle



class TRacingWheel:
    left_button = 295
    right_button = 294
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
            event = self.device.read_one()

    def get_angle(self):
        self.read_events()
        if self.raw_angle is not None:
            return int((self.raw_angle - self.center) / 50)


def load_sound(file_path, volume):
    sound = pygame.mixer.Sound(file_path)
    sound.set_volume(volume)
    return sound


class TCar:
    def __init__(self, gd, image_path, width, height, sound_path, sound_volume):
        self.image = image_path
        self.image = TSprite(gd, image_path, 0, 0, width, height)
        self.sound = pygame.mixer.Sound(sound_path)
        self.sound.set_volume(sound_volume)


class TCarType:
    my_car = 0
    passenger_car = 1
    truck = 2
    tractor = 3


class TSounds:
    roadside = 1
    normal_driving = 2
    accident = 3
    victory = 4
    truck = 5
    tractor = 6

    def __init__(self, enable_sounds):
        self.enable_sounds = enable_sounds
        self.sounds  = dict()
        if self.enable_sounds:
            pygame.mixer.init()
            self.sounds = {
                self.roadside: load_sound(os.path.join(SOUNDS_DIR, "roadside.wav"), 0.4),
                self.normal_driving: load_sound(os.path.join(SOUNDS_DIR, "normal_driving.wav"), 0.3),
                self.accident: load_sound(os.path.join(SOUNDS_DIR, "accident.wav"), 1),
                self.victory: load_sound(os.path.join(SOUNDS_DIR, "victory.wav"), 1),
                self.truck: load_sound(os.path.join(SOUNDS_DIR, "truck.wav"), 0.6),
                self.tractor: load_sound(os.path.join(SOUNDS_DIR, "tractor.wav"), 1)
            }

    def stop_sounds(self):
        if self.enable_sounds:
            for k in  self.sounds.values():
                k.stop()

    def switch_music(self, type, loops=1000):
        if self.enable_sounds:
            self.stop_sounds()
            #print ("switch_music {}".format(type))
            self.sounds[type].play(loops=loops)


class TRacesGame:
    def __init__(self, args):
        self.args = args
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
        self.passenger_car = TSprite(self.gd, os.path.join(SPRITES_DIR, 'passenger_car.png'), 0, 0, self.car_width, 160)
        self.truck_car = TSprite(self.gd, os.path.join(SPRITES_DIR, 'truck.png'), 0, 0, self.car_width, 260)
        self.tractor_car = TSprite(self.gd, os.path.join(SPRITES_DIR, 'tractor.png'), 0, 0, self.car_width, 260)
        self.tractor_car.hitbox_size_decrease = 200

        self.other_car = None
        self.game_over = False
        self.score = 0
        self.finish_top = 250
        self.start_time_on_the_road_side = None
        self.other_car_sound = None
        self.other_car_spawn_x = 0
        self.sounds = TSounds(not args.silent)

        self.cars_to_sounds = {
            self.passenger_car : TSounds.normal_driving,
            self.truck_car : TSounds.truck,
            self.tractor_car : TSounds.tractor
        }
        self.cars_to_spawnchance = {
            self.passenger_car : 3,
            self.truck_car : 2,
            self.tractor_car : 1
        }
        self.cars_to_speeds = {
            self.passenger_car : 1.3,
            self.truck_car : 1.9,
            self.tractor_car : 0.7
        }
        self.weighted_choice_cars = []
        for car in self.cars_to_spawnchance:
            for i in range(self.cars_to_spawnchance[car]):
                self.weighted_choice_cars.append(car)
        
        self.speed = 10
        self.racing_wheel = TRacingWheel(args.wheel_center)

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

    def car_crash(self):
        if self.my_car.intersect(self.other_car):
            self.sounds.switch_music(TSounds.accident, loops=0)
            self.message('Авария', TColors.red, 100, 250, 280)
            time.sleep(3)
            if self.args.mode == "normal_mode":
                self.my_car.top += 20
            elif self.args.mode == "gangster_mode":
                if self.other_car == self.truck_car:
                    self.my_car.top -= 40
                else:
                    self.my_car.top -= 20
                self.score += 1
            self.init_new_other_car()
            pygame.display.update()

    def is_on_the_roadside(self):
        return self.my_car.left < self.roadside_width or self.my_car.right() > self.width - self.roadside_width

    def draw_params(self):
        font = pygame.font.SysFont(None, 30)
        screen_text = font.render('score: ' + str(self.score), True, TColors.white)
        self.gd.blit(screen_text, (70, 0))

        screen_text = font.render('speed: ' + str(self.speed), True, TColors.white)
        self.gd.blit(screen_text, (70, 40))

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

    def init_new_other_car(self):
        self.other_car = random.choice(self.weighted_choice_cars)
        self.other_car_sound = self.cars_to_sounds[self.other_car]
        self.other_car.left = random.randrange(self.roadside_width, self.width - self.roadside_width - self.car_width)
        self.other_car_spawn_x = self.other_car.left
        self.other_car.top = 0
        self.sounds.switch_music(self.other_car_sound)

    def get_speed(self):
        if self.is_on_the_roadside():
            if self.start_time_on_the_road_side is None:
                self.start_time_on_the_road_side = time.time()
            time_on_the_road_side = time.time() - self.start_time_on_the_road_side
            if time_on_the_road_side < 3:
                return max(int(self.speed / 2), 1)
            elif time_on_the_road_side < 5:
                return 1
            else:
                return 0
        else:
            return self.speed

    def other_car_update(self):
        self.other_car.top += self.cars_to_speeds[self.other_car] * self.get_speed()
        
        if (self.other_car == self.tractor_car):
            ampl = 300
            freq = 0.003
            self.other_car.left = self.other_car_spawn_x + ampl * math.sin(freq * self.other_car.top)
            self.other_car.rotate(math.atan(freq * ampl * math.cos(freq * self.other_car.top)) * 180 / math.pi)

        if self.other_car.top > min(self.height - 100, self.my_car.bottom() + 200):
            self.init_new_other_car()
            if not self.is_on_the_roadside():
                if self.args.mode == "normal_mode":
                    self.score += 1
            if self.args.mode == "normal_mode":
                self.my_car.top -= 20

    def game_loop(self):
        self.my_car.left = self.width / 2
        self.my_car.top = self.height - 250
        self.game_over = False
        self.score = 0
        self.init_new_other_car()
        save_is_on_road_side = False
        x_change = 0
        self.sounds.switch_music(self.other_car_sound)
        while not self.game_over:
            wheel_angle = self.racing_wheel.get_angle()
            if wheel_angle is not None:
                x_change = wheel_angle

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_over = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        x_change = -10
                    elif event.key == pygame.K_RIGHT:
                        x_change = +10
                    elif event.key == pygame.K_UP:
                        self.speed += 1
                    elif event.key == pygame.K_DOWN:
                        self.speed = max(self.speed - 1, 1)
                    elif event.key == pygame.K_ESCAPE:
                        self.game_intro()
                    elif event.key == pygame.K_F1:
                        self.save_wheel_center()

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                        x_change = 0

            self.my_car.left += x_change
            if self.my_car.left < 0:
                self.my_car.left = 0
            if self.my_car.left > self.width - 50:
                self.my_car.left = self.width - 50
            self.gd.fill(TColors.gray)
            self.draw_background()

            self.my_car.draw()                
            self.other_car_update()
            self.other_car.draw()
            self.check_finish()
            self.car_crash()
            self.draw_params()
            if save_is_on_road_side != self.is_on_the_roadside():
                save_is_on_road_side = self.is_on_the_roadside()
                if self.is_on_the_roadside():
                    self.start_time_on_the_road_side = time.time()
                    self.sounds.switch_music(TSounds.roadside)
                else:
                    self.start_time_on_the_road_side = None
                    self.sounds.switch_music(self.other_car_sound)

            clock.tick(30)
            pygame.display.update()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--silent", dest='silent', default=False, action="store_true")
    parser.add_argument("--wheel-center", dest='wheel_center', default=300, type=int)
    parser.add_argument("--full-screen", dest='full_screen', default=False, action="store_true")
    parser.add_argument("--mode", dest='mode', default="normal", required=False, help="can be normal_mode,gangster_mode")
    return parser.parse_args()


if __name__ == "__main__":
    clock = pygame.time.Clock()
    args = parse_args()
    game = TRacesGame(args)
    game.game_intro()
    game.quit()
