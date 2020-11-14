import pygame
import time
import random
from pygame.locals import *


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
    def __init__(self):
        self.width = 800
        self.height = 600
        self.border_width = 100
        self.gd = pygame.display.set_mode((self.width, self.height))
        self.my_car = TSprite(self.gd, 'my_car.png', 0, 0, 80, 100)
        self.other_car = TSprite(self.gd, 'other_car.png', 0, 0, 80, 100)
        self.game_over = False
        self.finish_top = 150

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
            self.message( mess, mess_color, size, tx, ty)
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

        img = pygame.transform.scale(blue_strip, (self.border_width, self.height))
        self.gd.blit(img, (0, 0))
        self.gd.blit(img, (self.width - self.border_width, 0))

    def check_finish(self):
        if self.finish_top > self.my_car.top or self.my_car.top > 650:
            font = pygame.font.SysFont(None, 100)
            screen_text = font.render('game_over', True, TColors.white)
            self.gd.blit(screen_text, (250, 280))
            pygame.display.update()
            time.sleep(1)
            self.game_intro()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
            pygame.display.update()

    def car_crash(self):
        if self.my_car.intersect(self.other_car):
            self.message('CRASHED!', TColors.red, 100, 250, 280)
            time.sleep(3)
            self.my_car.top += 20
            self.init_new_other_car()
            pygame.display.update()

    def is_on_the_border(self):
        return self.my_car.left < self.border_width or self.my_car.right() > self.width - self.border_width

    def score(self, count):
        font = pygame.font.SysFont(None, 30)
        screen_text = font.render('score :' + str(count), True, TColors.white)
        self.gd.blit(screen_text, (0, 0))
        pygame.display.update()

    def game_intro(self):
        v = pygame.image.load('background1.jpg')
        self.gd.blit(v, (0, 0))
        pygame.display.update()
        game_intro = False
        while not game_intro:

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_intro = True
                    self.game_over = True

            self.message('MAIN MENU', TColors.green, 100, (self.width / 2 - 220), 100)
            self.button(100, 400, 70, 30, 'GO!', TColors.white, TColors.bright_red, TColors.red, 25, 106, 406, self.game_loop)
            self.button(600, 400, 70, 30, 'QUIT', TColors.white, TColors.bright_green, TColors.green, 25, 606, 406, self.quit)

            pygame.display.update()

        pygame.display.update()

    def init_new_other_car(self):
        self.other_car.left = random.randrange(100, 600)
        self.other_car.top = 0

    def game_loop(self):
        self.my_car.left = 300
        self.my_car.top = 400
        x_change = 0
        self.game_over = False
        success_count = 0
        self.init_new_other_car()
        while not self.game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_over = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        x_change = -10
                    elif event.key == pygame.K_RIGHT:
                        x_change = +10
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                        x_change = 0

            self.my_car.left += x_change
            self.gd.fill(TColors.gray)
            self.draw_background()
            self.my_car.draw()
            if self.other_car.top > 600:
                self.init_new_other_car()
                success_count += 1
                self.my_car.top -= 20
            else:
                self.other_car.top += 5 if self.is_on_the_border() else 10  

            self.other_car.draw()
            self.check_finish()
            self.car_crash()
            self.score(success_count)

            clock.tick(30)
            pygame.display.update()


if __name__ == "__main__":
    pygame.init()

    clock = pygame.time.Clock()
    game = TRacesGame()
    game.game_intro()
    game.quit()
