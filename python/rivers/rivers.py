
from utils.logging_wrapper import setup_logging
from utils.racing_wheel import TRacingWheel
from utils.colors import TColors
from utils.game_sounds import TSounds
from utils.game_intro import TGameIntro
from engine_sound import TEngineSound
from river_sprites import TSprite, TMyCar, TMapPart, TGrannySprite, TRepairStation, TGirlSprite,TGasStation
from river_registers import TGameRegisters

import pygame
import time
import argparse
import os
import math
import random
import logging


SOUNDS_DIR = os.path.join(os.path.dirname(__file__), "assets", 'sounds')

class TRiverGame:
    def __init__(self, args):
        self.args = args
        self.logger = setup_logging("rivers", console_level=logging.DEBUG if args.verbose else logging.INFO)
        self.finish_top = 300
        self.road_width = 30
        self.start_time_on_the_road_side = None
        self.sounds = TSounds(SOUNDS_DIR, not args.silent)
        self.racing_wheel = TRacingWheel(self.logger, args.wheel_center, angle_level_ratio=args.angle_level_ratio)
        self.engine_sound = None
        self.car_needs_repair = False
        self.init_engine_sound()

        self.river_sprites = pygame.sprite.Group()
        self.bridge_sprites = pygame.sprite.Group()
        self.my_car_sprites = pygame.sprite.Group()
        self.road_sprites = pygame.sprite.Group()
        self.town_sprites = pygame.sprite.Group()
        self.passengers_at_car_stop_sprites = pygame.sprite.Group()
        self.passengers_in_car_sprites = pygame.sprite.Group()
        self.last_pedal_event_time_stamp = 0
        self.river_collisions_1 = 0
        if args.full_screen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            pygame.display.toggle_fullscreen()
            self.width = pygame.display.get_window_size()[0]
            self.height = pygame.display.get_window_size()[1]
        else:
            self.width = self.args.width
            self.height = self.args.height
            self.screen: pygame.Surface = pygame.display.set_mode((self.width, self.height))
        self.stats: TGameRegisters = None
        self.game_intro = TGameIntro(self.screen, os.path.join(TSprite.SPRITES_DIR, 'background1.jpg'),  self.racing_wheel)

        self.my_car = TMyCar(self.screen, self.args.my_sprite_folder)
        self.my_car_sprites.add(self.my_car)
        self.map_part: TMapPart = None
        self.map_part_next = None
        self.passenger_in_car = None
        self.exit_game = False

    def init_engine_sound(self):
        if self.car_needs_repair:
            folder = os.path.join(os.path.dirname(__file__), 'assets/sounds/vaz_wo_muffler')
        else:
            folder = self.args.engine_audio_folder
        new_engine_sound = TEngineSound(self.logger, folder, self.args.max_car_speed_limit + 1)
        old_engine_sound  = self.engine_sound
        self.engine_sound = new_engine_sound
        self.engine_sound.start_play_stream()
        if old_engine_sound is not None:
            old_engine_sound.stop_engine()

    def quit(self):
        self.exit_game = True

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
            self.draw_game_intro("Очки: {}".format(self.stats.get_score()))

    def redraw_background(self):
        self.screen.fill(TSprite.BACKGROUND_COLOR)

    def check_river_collision(self, river_sprite):
        if not river_sprite.alive() or river_sprite.collided:
            return
        self.logger.info("river collision")
        self.sounds.play_sound("river_accident", loops=0)
        self.engine_sound.set_idling_state()
        river_sprite.collided = True
        self.stats.river_accident_count += 1
        self.river_collisions_1 += 1
        if self.car_has_granny():
            self.passenger_in_car.river_fall_count += 1
            if self.passenger_in_car.river_fall_count >= 3:
                self.passenger_goes_to_river("granny_sea_voyage")
        if self.river_collisions_1 == 2 and not self.car_needs_repair:
            self.car_needs_repair = True
            self.init_engine_sound()

    def get_car_speed(self):
        engine_speed = self.engine_sound.get_current_speed()
        #self.logger.debug('engine speed = {}'.format(engine_speed))
        return engine_speed - 1

    def check_bridge_collision(self,  bridge_sprite):
        if not bridge_sprite.alive() or bridge_sprite.used:
            return
        #self.logger.info("bridge collision")
        #self.stats.bridge_passing_count += 1
        #bridge_sprite.used = True
        #self.sounds.play_sound("bridge_passing", loops=0)

    def draw_game_intro(self, message_text=None):
        self.sounds.stop_sounds()
        self.engine_sound.stop_engine()
        self.game_intro.get_next_action(message_text)
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

    def car_has_passenger(self):
        return self.passenger_in_car is not None

    def car_has_granny(self):
        if self.passenger_in_car is None:
            return False
        return isinstance(self.passenger_in_car, TGrannySprite)

    def car_has_girl(self):
        if self.passenger_in_car is None:
            return False
        return isinstance(self.passenger_in_car, TGirlSprite)

    def get_granny_in_car_color(self):
        if not self.car_has_granny():
            return None
        return self.passenger_in_car.color.color

    def init_new_map_part(self):
        self.logger.debug("init_new_map_part")
        if not self.stats.increment_map_parts_count():
            self.draw_game_intro("Нет бензина!")
            return
        if self.map_part is not None:
            if not self.map_part.river.collided:
                self.car_bridge_success_event()
            self.map_part.destroy_sprites()
            self.map_part = self.map_part_next
        else:
            #first time
            dummy_rct = pygame.Rect(self.my_car.rect.center[0] - self.args.bridge_width/2,
                                    self.my_car.rect.top, self.args.bridge_width, 10)
            self.map_part = TMapPart(self.screen, 0, self.args.bridge_width, self.road_width, dummy_rct)
            self.map_part.generate_town(True)
            #self.logger.info("prev rect {}".format(dummy_rct))
            #self.logger.info("car rect {}".format(self.my_car.rect))
            pygame.draw.rect(self.screen, TColors.white, dummy_rct)
        self.map_part_next = TMapPart(self.screen, -self.height, self.args.bridge_width, self.road_width,
                                            self.map_part.bridge.rect)
        if self.stats.should_generation_gas_station():
            self.map_part_next.generate_gas_station()
        elif self.car_needs_repair and random.random() > 0.5:
            self.map_part_next.generate_repair_station()
        else:
            gen_granny = not self.car_has_passenger() and random.random() > 0.5
            self.map_part_next.generate_town(gen_granny)
        self.river_sprites.add(self.map_part.river)
        self.bridge_sprites.add(self.map_part.bridge)
        self.road_sprites.add(self.map_part.road, self.map_part_next.road)
        self.town_sprites.add(self.map_part.car_stop, self.map_part_next.car_stop)
        self.map_part.add_passengers_to_sprite_group(self.passengers_at_car_stop_sprites)
        self.map_part_next.add_passengers_to_sprite_group(self.passengers_at_car_stop_sprites)
        self.logger.info(self.map_part.get_descr())

    def is_obstacle_finish(self, sprite: TSprite):
        return sprite.rect.top > min(self.height - 100, self.my_car.rect.bottom + 200)

    def change_obstacle_positions(self):
        if self.map_part is not None:
            speed = self.get_car_speed()
            if speed > 0:
                self.map_part.change_spite_position(speed)
                self.map_part_next.change_spite_position(speed)
                #self.logger.info("next_bridge.top={}, next_river.top={}".format(
                #    self.map_part_next.bridge.rect.top, self.map_part_next.river.rect.top))
            if self.is_obstacle_finish(self.map_part.river):
                self.init_new_map_part()

    def use_brakes(self):
        self.logger.info("use brakes")
        self.sounds.play_sound("brakes", loops=0)
        self.engine_sound.set_idling_state()

    def passenger_gets_on_the_car(self, sprite: TSprite):
        self.passengers_in_car_sprites.empty()
        sprite.parent = self.screen
        sprite.rect.top = self.height - sprite.rect.height
        sprite.rect.left = self.width - sprite.rect.width
        self.passenger_in_car = sprite
        self.passengers_in_car_sprites.add(sprite)
        self.passengers_at_car_stop_sprites.empty()
        self.map_part.passengers.clear()

    def passenger_leaves_car(self, sound_name):
        #self.passenger_in_car.kill()
        self.sounds.play_sound(sound_name, loops=0)
        time.sleep(1)
        self.map_part.passenger_goes_to_car_stop(self.passenger_in_car)
        self.map_part.add_passengers_to_sprite_group(self.passengers_in_car_sprites)
        self.passenger_in_car = None

    def passenger_goes_to_river(self, sound_name):
        self.passenger_in_car.kill()
        self.passengers_in_car_sprites.empty()
        self.sounds.play_sound(sound_name, loops=0)
        self.passenger_in_car = None
        time.sleep(1)

    def repair_car(self):
        self.car_needs_repair = False
        self.sounds.play_sound("repair_car", loops=0)
        self.init_engine_sound()
        self.river_collisions_1 = 0

    def refuel_car(self):
        self.engine_sound.stop_engine()
        length = self.sounds.play_sound("gas_station", loops=0)
        time.sleep(length)
        self.stats.refuel_car()
        self.init_engine_sound()

    def granny_leaves_the_car(self):
        if self.map_part.car_stop.color.color == self.get_granny_in_car_color():
            self.logger.info("granny leaves the car")
            self.sounds.play_sound("door_open", loops=0)
            time.sleep(2)
            self.passenger_leaves_car("thank")
            self.stats.success_tasks_count += 1
        else:
            self.logger.info("granny refuses to leave the car")
            self.sounds.play_sound("door_open", loops=0)
            time.sleep(2)
            self.sounds.play_sound("wrong_stop", loops=0)
            time.sleep(1)

    def open_door(self):
        if self.get_car_speed() == 1:
            self.use_brakes()
            time.sleep(2)

        if self.get_car_speed() != 0:
            return

        town = pygame.sprite.spritecollideany(self.my_car, self.town_sprites, collided=pygame.sprite.collide_mask)
        if self.car_needs_repair and isinstance(town, TRepairStation):
            self.repair_car()
            return

        if isinstance(town, TGasStation):
            if not self.stats.is_full_tank():
                self.refuel_car()
            return

        passenger_at_car_stop = pygame.sprite.spritecollideany(self.my_car, self.passengers_at_car_stop_sprites,
                                                collided=pygame.sprite.collide_mask)
        if town or passenger_at_car_stop:
            self.logger.info("open door")
            if self.map_part.has_passengers() and not self.car_has_passenger():
                self.logger.info("granny comes to the car")
                self.sounds.play_sound("door_open", loops=0)
                time.sleep(1)
                self.passenger_gets_on_the_car(self.map_part.passengers[0])
                self.map_part_next.kill_passengers()
            elif self.car_has_granny():
                self.granny_leaves_the_car()
            elif self.car_has_girl():
                self.logger.info("girl refuses to leave the car")
                self.sounds.play_sound("door_open", loops=0)
                time.sleep(2)
                self.sounds.play_sound("gde_voda", loops=0)
                time.sleep(1)

        bridge = pygame.sprite.spritecollideany(self.my_car, self.bridge_sprites, collided=pygame.sprite.collide_mask)
        if bridge and self.car_has_girl():
            self.stats.success_tasks_count += 1
            self.passenger_goes_to_river("hurra")

    def process_keyboard_and_wheel_events(self, x_change):
        wheel_angle = self.racing_wheel.get_angle()
        if wheel_angle is not None:
            x_change = wheel_angle
        for event in pygame.event.get():
            #self.logger.debug('event = {}'.format(event))
            if event.type == pygame.QUIT:
                self.stats.game_over = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    x_change = -self.my_car.horizontal_speed
                elif event.key == pygame.K_RIGHT:
                    x_change = +self.my_car.horizontal_speed
                elif event.key == pygame.K_UP:
                    self.logger.info("pygame.K_UP")
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
                elif event.key == pygame.K_F2:
                    self.sounds.play_sound("door_open", loops=0)

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    x_change = 0
                if event.key == pygame.K_UP:
                    self.engine_sound.decrease_speed()
        if TRacingWheel.left_hat_button in self.racing_wheel.pressed_buttons:
            self.open_door()
            self.racing_wheel.pressed_buttons.remove(TRacingWheel.left_hat_button)
        if self.my_car.horizontal_speed_increase_with_get_speed:
            car_speed = self.get_car_speed()
            if car_speed > 0:
                x_change += 0.01 * x_change * math.sqrt(car_speed)

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
        self.passengers_at_car_stop_sprites.draw(self.screen)
        self.passengers_in_car_sprites.draw(self.screen)
        pygame.draw.line(self.screen, TColors.white, (0, self.finish_top),
                         (self.width, self.finish_top))

        self.stats.draw_params(self.my_car.rect.top, self.get_car_speed(), self.car_needs_repair)
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
        self.passengers_at_car_stop_sprites.empty()
        self.my_car.rect.left = self.width / 2
        self.my_car.rect.top = self.height - 250
        if self.map_part is not None:
            self.map_part.destroy_sprites()
            self.map_part = None
        #self.my_car.rect.top = self.height - 650
        self.stats = TGameRegisters(self.screen)
        self.redraw_background()
        self.car_needs_repair = False
        self.init_new_map_part()
        self.engine_sound.start_play_stream()
        self.river_collisions_1 = 0

    def game_loop(self):
        self.init_game_loop()
        x_change = 0

        while not self.stats.game_over and not self.exit_game:
            self.process_wheel_pedals()
            x_change = self.process_keyboard_and_wheel_events(x_change)
            if not self.stats.paused:
                self.change_obstacle_positions()
            self.check_finish()
            self.check_all_collisions()
            self.redraw_all()
            clock.tick(20)
            #pygame.time.delay(200)
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
    parser.add_argument("--max-car-speed-limit", dest='max_car_speed_limit', default=10, type=int)
    parser.add_argument("--bridge-width", dest='bridge_width', default=300, type=int)
    parser.add_argument("--verbose", dest='verbose', default=False, action="store_true")

    parser.add_argument("--car-sprite-folder", dest='my_sprite_folder')
    parser.add_argument("--angle-level-ratio", dest='angle_level_ratio', type=float, default=30,
                        help="the less value, the less one must turn the angle to change the direction")
    parser.add_argument("--engine-audio-folder", dest='engine_audio_folder',
                        default= os.path.join(os.path.dirname(__file__), 'assets/sounds/ford'))

    return parser.parse_args()


if __name__ == "__main__":
    clock = pygame.time.Clock()
    args = parse_args()
    #pr.enable()

    pygame.display.init()
    pygame.font.init()
    game = TRiverGame(args)
    game.draw_game_intro()


#=========
# Звук старта ( если есть)
# Макс. громкость

