import pygame
import time
import random
import argparse
from pygame.locals import *
from evdev import list_devices, InputDevice, categorize, ecodes


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
        self.image = pygame.transform.scale(pygame.image.load(image_file_name), (width, height))

    def draw(self):
        self.gd.blit(self.image, (self.left, self.top))

    def right(self):
        return self.left + self.width

    def bottom(self):
        return self.top + self.height

    def intersect(self, other, possible_collision=10):
        return self.left + possible_collision <= other.right() and \
          other.left + possible_collision <= self.right() and \
          self.top + possible_collision <= other.bottom() and \
          other.top + possible_collision <= self.bottom()


class TRacesGame:
    def __init__(self, args):
        self.args = args
        self.enable_sounds = not args.silent
        self.wheel_center = args.wheel_center
        self.width = 800
        self.height = 1000
        self.roadside_width = 100
        self.gd = pygame.display.set_mode((self.width, self.height))
        self.my_car = TSprite(self.gd, 'my_car.png', 0, 0, 80, 100)
        self.other_car = TSprite(self.gd, 'other_car.png', 0, 0, 80, 100)
        self.game_over = False
        self.finish_top = 250
        self.start_time_on_the_road_side = None

        if self.enable_sounds:
            pygame.mixer.init()
            self.roadside_sound = pygame.mixer.Sound("roadside.wav")
            self.roadside_sound.set_volume(0.5)

            self.normal_driving = pygame.mixer.Sound("normal_driving.wav")
            self.normal_driving.set_volume(0.3)

            self.accident = pygame.mixer.Sound("accident.wav")
            self.accident.set_volume(1.0)
        self.speed = 10
        joysticks = list_devices()
        self.last_wheel_value = None
        if len(joysticks) > 0:
            self.racing_wheel = InputDevice(joysticks[0])
            self.read_last_wheel_value()
        else:
            print ("no racing wheel found")
            self.racing_wheel = None

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
        blue_strip = pygame.image.load('border.jpg')

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
            if self.enable_sounds:
                self.accident.play(loops=0)
            self.message('CRASHED!', TColors.red, 100, 250, 280)
            time.sleep(3)
            self.my_car.top += 20
            self.init_new_other_car()
            pygame.display.update()

    def is_on_the_roadside(self):
        return self.my_car.left < self.roadside_width or self.my_car.right() > self.width - self.roadside_width

    def score(self, count):
        font = pygame.font.SysFont(None, 30)
        screen_text = font.render('score :' + str(count), True, TColors.white)
        self.gd.blit(screen_text, (0, 0))
        pygame.display.update()

    def game_intro(self):
        self.stop_sounds()
        v = pygame.image.load('background1.jpg')
        self.gd.blit(v, (0, 0))
        pygame.display.update()
        game_intro = False
        while not game_intro:
            self.read_last_wheel_value()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_intro = True
                    self.game_over = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F1:
                        self.save_wheel_center()

            self.message('MAIN MENU', TColors.green, 100, (self.width / 2 - 220), 100)
            self.button(100, 400, 70, 30, 'GO!', TColors.white, TColors.bright_red, TColors.red, 25, 106, 406, self.game_loop)
            self.button(600, 400, 70, 30, 'QUIT', TColors.white, TColors.bright_green, TColors.green, 25, 606, 406, self.quit)

            pygame.display.update()

        pygame.display.update()

    def init_new_other_car(self):
        self.other_car.left = random.randrange(100, 600)
        self.other_car.top = 0

    def stop_sounds(self):
        if self.enable_sounds:
            self.normal_driving.stop()
            self.roadside_sound.stop()
            self.accident.stop()

    def switch_music(self):
        if self.enable_sounds:
            self.stop_sounds()
            if self.is_on_the_roadside():
                self.roadside_sound.play(loops=1000)
            else:
                self.normal_driving.play(loops=1000)

    def read_last_wheel_value(self):
        if self.racing_wheel is None:
            return
        wheel_event = self.racing_wheel.read_one()
        while wheel_event is not None:
            if wheel_event.code == ecodes.ABS_WHEEL:
                self.last_wheel_value = wheel_event.value
                print("abs_wheel value={}, center={}".format(self.last_wheel_value, self.wheel_center))
            wheel_event = self.racing_wheel.read_one()
        return self.last_wheel_value

    def save_wheel_center(self):
        if self.last_wheel_value is not None:
            print("set wheel center to {}".format(self.last_wheel_value))
            self.wheel_center = self.last_wheel_value

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

    def game_loop(self):
        self.my_car.left = self.width / 2
        self.my_car.top = self.height - 200
        self.game_over = False
        success_count = 0
        self.init_new_other_car()
        save_is_on_road_side = False
        x_change = 0
        self.switch_music()
        while not self.game_over:
            wheel_value = self.read_last_wheel_value()
            if wheel_value is not None:
                x_change = int( (wheel_value - self.wheel_center) / 50)

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
            if self.other_car.top > min(self.height - 100, self.my_car.bottom() + 200):
                self.init_new_other_car()
                if not self.is_on_the_roadside():
                    success_count += 1
                self.my_car.top -= 20
            else:
                self.other_car.top += self.get_speed()

            self.other_car.draw()
            self.check_finish()
            self.car_crash()
            self.score(success_count)
            if save_is_on_road_side != self.is_on_the_roadside():
                save_is_on_road_side = self.is_on_the_roadside()
                if self.is_on_the_roadside():
                    self.start_time_on_the_road_side = time.time()
                else:
                    self.start_time_on_the_road_side = None
                self.switch_music()

            clock.tick(30)
            pygame.display.update()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--silent", dest='silent', default=False, action="store_true")
    parser.add_argument("--wheel-center", dest='wheel_center', default=300, type=int)
    return parser.parse_args()


if __name__ == "__main__":
    pygame.display.init()
    pygame.font.init()
    clock = pygame.time.Clock()
    args = parse_args()
    game = TRacesGame(args)
    game.game_intro()
    game.quit()
