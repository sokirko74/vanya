from utils.logging_wrapper import setup_logging
from utils.racing_wheel import TRacingWheel
from utils.colors import TColors
from utils.game_sounds import TSounds
from utils.game_intro import TGameIntro
from engine_sound import TEngineSound
import pygame
import time
import argparse
import os
import math
import random

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


class TRiver(TSprite):
    def __init__(self, parent, top=0, left=0):
        super().__init__(parent,
                              'river.png',
                              pygame.Rect(0, top, parent.get_width(), 160))
        self.used = False


class TBridge(TSprite):
    def __init__(self, parent, top=0, left=0, width=300):
        super().__init__(parent,
                              'bridge.png',
                              pygame.Rect(0, top, width, 200))
        self.used = False


class TGameRegisters:
    def __init__(self, screen):
        self.screen = screen
        self.score = 0
        self.game_over = False
        self.river_accident_count = 0
        self.bridge_passing_count = 0
        self.paused = False
        self.font = pygame.font.SysFont(None, 30)

    def print_text(self, text, x, y):
        screen_text = self.font.render(text, True, TColors.white)
        self.screen.blit(screen_text, (x, y))

    def get_score(self):
        return self.bridge_passing_count - self.river_accident_count

    def draw_params(self, my_car_top, game_speed):
        self.print_text('score: {}'.format(self.get_score()), 30, 0)
        self.print_text('speed: {}'.format(game_speed), 30, 40)
        self.print_text('position: {}'.format(my_car_top), 30, 80)
        self.print_text('rivers: {}'.format(self.river_accident_count), 30, 120)
        self.print_text('bridges: {}'.format(self.bridge_passing_count), 30, 160)
        if self.paused:
            s = pygame.display.get_surface()
            self.print_text("pause (press spacebar to play)", s.get_width()/2, s.get_height()/2)


class TRiverGame:
    def __init__(self, args):
        self.args = args
        self.logger = setup_logging("rivers")
        self.finish_top = 250
        self.start_time_on_the_road_side = None
        self.sounds = TSounds(SOUNDS_DIR, not args.silent)
        self.racing_wheel = TRacingWheel(self.logger, args.wheel_center)
        self.max_game_speed = 10
        self.engine_sound = TEngineSound(self.max_game_speed, self.args.engine_audio_folder)
        self.engine_sound.start_engine()

        self.river_sprites = pygame.sprite.Group()
        self.bridge_sprites = pygame.sprite.Group()
        self.my_car_sprites = pygame.sprite.Group()
        if args.full_screen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            pygame.display.toggle_fullscreen()
            self.width = pygame.display.get_window_size()[0]
            self.height = pygame.display.get_window_size()[1]
        else:
            self.width = self.args.width
            self.height = self.args.height
            self.screen = pygame.display.set_mode((self.width, self.height))
        self.stats = TGameRegisters(self.screen)
        self.game_intro = TGameIntro(self.screen, os.path.join(SPRITES_DIR, 'background1.jpg'),  self.racing_wheel)

        self.car_width = 160
        self.my_car = TSprite(self.screen, 'my_car.png', pygame.Rect(0, 0, self.car_width, 160))
        self.my_car_horizontal_speed = 10
        self.my_car_horizontal_speed_increase_with_get_speed = True
        self.my_car_sprites.add(self.my_car)

        self.bridge_width = self.args.bridge_width

        self.river = None
        self.bridge = None

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
        pygame.draw.line(self.screen, TColors.white, (0, self.finish_top),
                         (self.width, self.finish_top))

    def check_river_collision(self, river_sprite):
        if not river_sprite.alive() or river_sprite.used:
            return
        self.logger.info("river collision")
        self.sounds.play_sound("river_accident", loops=0)
        self.engine_sound.stop_engine()
        river_sprite.used = True
        self.stats.river_accident_count += 1

    def get_speed(self):
        return self.engine_sound.get_current_speed()

    def check_bridge_collision(self,  bridge_sprite):
        if not bridge_sprite.alive() or bridge_sprite.used:
            return
        self.logger.info("bridge collision")
        self.stats.bridge_passing_count += 1
        bridge_sprite.used = True
        self.sounds.play_sound("bridge_passing", loops=0)

    def draw_game_intro(self, prev_score=None):
        self.sounds.stop_sounds()
        self.game_intro.get_next_action(prev_score)
        if self.game_intro.action == TGameIntro.exit_game_action:
            self.quit()
        elif self.game_intro.action == TGameIntro.start_game_action:
            self.game_loop()
        else:
            raise Exception("unknown action")

    def is_broken_driving(self):
        return self.stats.broken

    def init_new_river(self):
        self.logger.debug("init_new_river")
        if self.river is not None:
            self.river.kill()
            self.river = None

        self.river = TRiver(self.screen)
        self.bridge = TBridge(self.screen, width=self.bridge_width)
        self.bridge.rect.top = 0
        self.bridge.rect.left = random.randrange(0, self.width - self.bridge_width )
        self.river_sprites.add(self.river)
        self.bridge_sprites.add(self.bridge)

    def is_obstacle_finish(self, sprite: TSprite):
        return sprite.rect.top > min(self.height - 100, self.my_car.rect.bottom + 200)

    def change_obstacle_positions(self):
        if self.river is not None:
            self.river.change_spite_position(self.get_speed())
            self.bridge.change_spite_position(self.get_speed())
            if self.is_obstacle_finish(self.river):
                self.river.kill()
                self.river = None
                self.bridge.kill()
                self.bridge = None
                self.init_new_river()

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
                    self.engine_sound.increase_speed()
                elif event.key == pygame.K_DOWN:
                    self.engine_sound.decrease_speed()
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

        if self.racing_wheel.is_right_pedal_pressed():
            self.sounds.play_sound("car_honk_right")

    def redraw_all(self):
        self.redraw_background()
        self.stats.draw_params(self.my_car.rect.top, self.get_speed())
        #pygame.draw.rect(self.screen, TColors.black, self.other_car.rect, width=1)
        #pygame.draw.rect(self.screen, TColors.black, self.my_car.rect, width=1)
        self.river_sprites.draw(self.screen)
        self.bridge_sprites.draw(self.screen)
        self.my_car_sprites.draw(self.screen)
        pygame.display.flip()

    def check_all_collisions(self):
        bridge = pygame.sprite.spritecollideany(self.my_car, self.bridge_sprites, collided=pygame.sprite.collide_mask)
        river = pygame.sprite.spritecollideany(self.my_car, self.river_sprites, collided=pygame.sprite.collide_mask)
        if bridge is not None:
            self.check_bridge_collision(bridge)
        elif river is not None:
            self.check_river_collision(river)

    def game_loop(self):
        self.river_sprites.empty()
        self.bridge_sprites.empty()
        self.my_car.rect.left = self.width / 2
        self.my_car.rect.top = self.height - 250
        #self.my_car.rect.top = self.height - 650
        self.stats = TGameRegisters(self.screen)
        self.redraw_background()
        x_change = 0
        self.init_new_river()
        while not self.stats.game_over:
            self.process_wheel_pedals()
            x_change = self.process_keyboard_and_wheel_events(x_change)
            if not self.stats.paused:
                self.change_obstacle_positions()
            self.check_finish()
            self.check_all_collisions()
            self.redraw_all()
            clock.tick(30)
            if self.my_car.rect.top + 30 > self.height:
                self.my_car.rect.top = self.height - 30


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--silent", dest='silent', default=False, action="store_true")
    parser.add_argument("--wheel-center", dest='wheel_center', default=300, type=int)
    parser.add_argument("--great-victory-level", dest='great_victory_level', default=15, type=int)
    parser.add_argument("--full-screen", dest='full_screen', default=False, action="store_true")
    parser.add_argument("--width", dest='width', default=1600, type=int)
    parser.add_argument("--height", dest='height', default=1000, type=int)
    parser.add_argument("--bridge-width", dest='bridge_width', default=300, type=int)
    parser.add_argument("--engine-audio-folder", dest='engine_audio_folder',
                        default= os.path.join(os.path.dirname(__file__), 'assets/sounds/ford'))
    return parser.parse_args()


if __name__ == "__main__":
    clock = pygame.time.Clock()
    args = parse_args()
    pygame.display.init()
    pygame.font.init()
    game = TRiverGame(args)
    game.draw_game_intro()
    game.quit()
