from utils.logging_wrapper import setup_logging
from utils.racing_wheel import TRacingWheel
from utils.colors import TColors
from utils.game_sounds import TSounds
from utils.game_intro import TGameIntro
from engine_sound import TEngineSound
from river_sprites import TSprite, TMyCar, TMapPart, TGrannySprite
from river_registers import TGameRegisters

import pygame
import time
import argparse
import os
import math
import random

SOUNDS_DIR = os.path.join(os.path.dirname(__file__), "assets", 'sounds')


class TRiverGame:
    def __init__(self, args):
        self.args = args
        self.logger = setup_logging("rivers")
        self.finish_top = 300
        self.road_width = 30
        self.start_time_on_the_road_side = None
        self.sounds = TSounds(SOUNDS_DIR, not args.silent)
        self.racing_wheel = TRacingWheel(self.logger, args.wheel_center)
        self.max_game_speed = args.speed_count
        self.engine_sound = TEngineSound(self.max_game_speed, self.args.engine_audio_folder, max_volume=self.args.engine_volume)
        self.engine_sound.start_engine()

        self.river_sprites = pygame.sprite.Group()
        self.bridge_sprites = pygame.sprite.Group()
        self.my_car_sprites = pygame.sprite.Group()
        self.road_sprites = pygame.sprite.Group()
        self.town_sprites = pygame.sprite.Group()
        self.granny_sprites = pygame.sprite.Group()
        self.grannies_in_car = pygame.sprite.Group()
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
        self.game_intro = TGameIntro(self.screen, os.path.join(TSprite.SPRITES_DIR, 'background1.jpg'),  self.racing_wheel)

        self.my_car = TMyCar(self.screen, self.args.my_sprite)
        self.my_car_sprites.add(self.my_car)
        self.map_part = None
        self.map_part_next = None
        self.granny_in_car = None

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
            self.engine_sound.stop_engine()
            font = pygame.font.SysFont(None, 100)
            if win:
                if self.stats.get_score() < self.args.great_victory_level:
                    font = pygame.font.SysFont(None, 50)
                    screen_text = font.render('Победа! Очки: {}'.format(self.stats.get_score()), True, TColors.white)
                    loops = 0
                else:
                    font = pygame.font.SysFont(None, 150)
                    screen_text = font.render('Победа! Очки: {}'.format(self.stats.get_score()), True, TColors.green)
                    loops = 1
                self.sounds.stop_all_and_play("victory", loops=loops)
            else:
                screen_text = font.render('Проигрыш!', True, TColors.white)
            self.screen.blit(screen_text, (250, 280))
            pygame.display.update()
            time.sleep(5)
            self.draw_game_intro(self.stats.get_score())

    def redraw_background(self):
        self.screen.fill(TSprite.BACKGROUND_COLOR)

    def check_river_collision(self, river_sprite):
        if not river_sprite.alive() or river_sprite.collided:
            return
        self.logger.info("river collision")
        self.sounds.play_sound("river_accident", loops=0)
        self.engine_sound.stop_engine()
        river_sprite.collided = True
        self.stats.river_accident_count += 1
        if self.granny_in_car is not None:
            self.granny_in_car.river_fall_count += 1
            if self.granny_in_car.river_fall_count >= 3:
                self.granny_leaves_car("granny_sea_voyage")

    def get_speed(self):
        return self.engine_sound.get_current_speed()

    def check_bridge_collision(self,  bridge_sprite):
        if not bridge_sprite.alive() or bridge_sprite.used:
            return
        #self.logger.info("bridge collision")
        #self.stats.bridge_passing_count += 1
        #bridge_sprite.used = True
        #self.sounds.play_sound("bridge_passing", loops=0)

    def draw_game_intro(self, prev_score=None):
        self.sounds.stop_sounds()
        self.game_intro.get_next_action(prev_score)
        if self.game_intro.action == TGameIntro.exit_game_action:
            self.quit()
        elif self.game_intro.action == TGameIntro.start_game_action:
            self.game_loop()
        else:
            raise Exception("unknown action")

    def car_bridge_success_event(self):
        self.my_car.rect.top -= 20
        self.stats.bridge_passing_count += 1
        self.sounds.play_sound("bridge_passing", loops=0)

    def get_granny_in_car_color(self):
        if self.granny_in_car is None:
            return None
        return self.granny_in_car.color.color

    def init_new_river(self):
        self.logger.debug("init_new_river")
        if self.map_part is not None:
            if not self.map_part.river.collided:
                self.car_bridge_success_event()
            self.map_part.destroy_sprites()
            self.map_part = self.map_part_next
        else:
            #first time
            dummy_rct = pygame.Rect(self.my_car.rect.center[0] - self.args.bridge_width/2,
                                    self.my_car.rect.top, self.args.bridge_width, 10)
            self.map_part = TMapPart(self.screen, 0, self.args.bridge_width, self.road_width, dummy_rct, True)
            #self.logger.info("prev rect {}".format(dummy_rct))
            #self.logger.info("car rect {}".format(self.my_car.rect))
            pygame.draw.rect(self.screen, TColors.white, dummy_rct)
        gen_granny = self.get_granny_in_car_color() is None and random.random() > 0.5
        self.map_part_next = TMapPart(self.screen, -self.height, self.args.bridge_width, self.road_width,
                                            self.map_part.bridge.rect, gen_granny)
        self.river_sprites.add(self.map_part.river)
        self.bridge_sprites.add(self.map_part.bridge)
        self.road_sprites.add(self.map_part.road, self.map_part_next.road)
        self.town_sprites.add(self.map_part.town, self.map_part_next.town)
        self.map_part.add_grannies_to_group(self.granny_sprites)
        self.map_part_next.add_grannies_to_group(self.granny_sprites)
        self.logger.info(self.map_part.get_descr())

    def is_obstacle_finish(self, sprite: TSprite):
        return sprite.rect.top > min(self.height - 100, self.my_car.rect.bottom + 200)

    def change_obstacle_positions(self):
        if self.map_part is not None:
            speed = self.get_speed()
            if speed > 0:
                self.map_part.change_spite_position(speed)
                self.map_part_next.change_spite_position(speed)
                #self.logger.info("next_bridge.top={}, next_river.top={}".format(
                #    self.map_part_next.bridge.rect.top, self.map_part_next.river.rect.top))
            if self.is_obstacle_finish(self.map_part.river):
                self.init_new_river()

    def use_brakes(self):
        self.logger.info("use brakes")
        self.sounds.play_sound("brakes", loops=0)
        self.engine_sound.stop_engine()

    def init_granny_in_car(self, color):
        self.grannies_in_car.empty()
        g = TGrannySprite(self.screen,
                          self.width - TGrannySprite.GRANNY_WIDTH,
                          self.height - TGrannySprite.GRANNY_WIDTH, color=color)
        self.granny_in_car = g
        self.grannies_in_car.add(g)

    def granny_leaves_car(self, sound_name):
        self.granny_in_car.kill()
        self.granny_in_car = None
        self.sounds.play_sound(sound_name, loops=0)
        time.sleep(1)

    def open_door(self):
        if self.get_speed() == 1:
            self.use_brakes()
            time.sleep(2)

        if self.get_speed() == 0:
            town = pygame.sprite.spritecollideany(self.my_car, self.town_sprites, collided=pygame.sprite.collide_mask)
            granny = pygame.sprite.spritecollideany(self.my_car, self.granny_sprites,
                                                    collided=pygame.sprite.collide_mask)
            if town or granny:
                self.logger.info("open door")
                left_granny_color = None
                if self.granny_in_car is not None :
                    if self.map_part.town.color.color == self.get_granny_in_car_color():
                        self.logger.info("granny leaves the car")
                        self.sounds.play_sound("door_open", loops=0)
                        time.sleep(2)
                        left_granny_color = self.granny_in_car.color.color
                        self.granny_leaves_car("thank")
                        self.stats.transfered_grannies_count += 1
                    else:
                        self.logger.info("granny refuses to leave the car")
                        self.sounds.play_sound("door_open", loops=0)
                        time.sleep(2)
                        self.sounds.play_sound("wrong_stop", loops=0)
                        time.sleep(1)
                else:
                    self.logger.info("no granny on board")

                if self.get_granny_in_car_color() is None and self.map_part.has_grannies():
                    self.logger.info("granny comes to the car")
                    self.sounds.play_sound("door_open", loops=0)
                    time.sleep(1)
                    self.init_granny_in_car(self.map_part.grannies[0].color.color)
                    self.map_part.kill_grannies()
                    self.map_part_next.kill_grannies()
                if left_granny_color is not None:
                    self.map_part.generate_granny(left_granny_color)
                    self.map_part.add_grannies_to_group(self.granny_sprites)

    def process_keyboard_and_wheel_events(self, x_change):
        wheel_angle = self.racing_wheel.get_angle()
        if wheel_angle is not None:
            x_change = wheel_angle

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.stats.game_over = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    x_change = -self.my_car.horizontal_speed
                elif event.key == pygame.K_RIGHT:
                    x_change = +self.my_car.horizontal_speed
                elif event.key == pygame.K_UP:
                    self.engine_sound.increase_speed()
                elif event.key == pygame.K_DOWN:
                    self.use_brakes()
                elif event.key == pygame.K_ESCAPE:
                    self.draw_game_intro()
                elif event.key == pygame.K_SPACE:
                    self.stats.paused = not self.stats.paused
                elif event.key == pygame.K_o:
                    self.open_door()
                elif event.key == pygame.K_F1:
                    self.racing_wheel.save_wheel_center()

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    x_change = 0
                if event.key == pygame.K_UP:
                    self.engine_sound.decrease_speed()
        if TRacingWheel.left_hat_button in self.racing_wheel.pressed_buttons:
            self.open_door()
            self.racing_wheel.pressed_buttons.remove(TRacingWheel.left_hat_button)
        if self.my_car.horizontal_speed_increase_with_get_speed:
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
        if not self.racing_wheel.is_attached():
            return
        if self.racing_wheel.is_left_pedal_pressed():
            #self.logger.info("left pedal is on")
            self.engine_sound.increase_speed()
        else:
            #self.logger.info("left pedal is off    ")
            self.engine_sound.decrease_speed()

        if self.racing_wheel.is_right_pedal_pressed():
            #self.logger.info("right pedal is on")
            self.use_brakes()

    def redraw_all(self):
        self.redraw_background()
        self.river_sprites.draw(self.screen)
        self.bridge_sprites.draw(self.screen)
        self.road_sprites.draw(self.screen)
        self.town_sprites.draw(self.screen)
        self.granny_sprites.draw(self.screen)
        self.grannies_in_car.draw(self.screen)
        pygame.draw.line(self.screen, TColors.white, (0, self.finish_top),
                         (self.width, self.finish_top))

        self.stats.draw_params(self.my_car.rect.top, self.get_speed())
        #pygame.draw.rect(self.screen, TColors.black, self.other_car.rect, width=1)
        #pygame.draw.rect(self.screen, TColors.black, self.my_car.rect, width=1)
        self.my_car_sprites.draw(self.screen)
        pygame.display.flip()

    def check_all_collisions(self):
        bridge = pygame.sprite.spritecollideany(self.my_car, self.bridge_sprites, collided=pygame.sprite.collide_mask)
        river = pygame.sprite.spritecollideany(self.my_car, self.river_sprites, collided=pygame.sprite.collide_mask)
        if bridge is not None:
            self.check_bridge_collision(bridge)
        elif river is not None:
            self.check_river_collision(river)
        #elif town or granny:


    def init_game_loop(self):
        self.river_sprites.empty()
        self.bridge_sprites.empty()
        self.road_sprites.empty()
        self.town_sprites.empty()
        self.granny_sprites.empty()
        self.granny_in_car_color = None
        self.my_car.rect.left = self.width / 2
        self.my_car.rect.top = self.height - 250
        if self.map_part is not None:
            self.map_part.destroy_sprites()
            self.map_part = None
        #self.my_car.rect.top = self.height - 650
        self.stats = TGameRegisters(self.screen)
        self.redraw_background()
        self.init_new_river()

    def game_loop(self):
        self.init_game_loop()
        x_change = 0
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
    parser.add_argument("--speed-count", dest='speed_count', default=10, type=int)
    parser.add_argument("--bridge-width", dest='bridge_width', default=300, type=int)
    parser.add_argument("--car-sprite", dest='my_sprite', default='my_car.png')
    parser.add_argument("--engine-volume", dest='engine_volume', type=float)
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

#  открывание дверей(звук), посадка бабкт
#  отрисовка бабки в автобусе
#  картинка автобуса
# работа с рулем (девайсом)