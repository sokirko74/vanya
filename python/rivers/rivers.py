from utils.logging_wrapper import setup_logging
from utils.racing_wheel import TRacingWheel
from utils.colors import TColors
from utils.game_sounds import TSounds
from utils.game_intro import TGameIntro
from river_sprites import TSprite, TMapPart, TGrannySprite, TRepairStation, TGirlSprite,TGasStation, \
    TRiverSprites,  THospital, TTownSprite, TBank
from car_dashboard import TCarDashboard
from vehicles import BaseCar

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
        self.car_is_ambulance = False
        self.args = args
        self.logger = setup_logging("rivers", console_level=logging.DEBUG if args.verbose else logging.INFO)
        self.sprites = TRiverSprites()
        self.finish_top = 300
        self.road_width = 30
        self.start_time_on_the_road_side = None
        self.sounds = TSounds(SOUNDS_DIR, not args.silent)
        self.racing_wheel = TRacingWheel(self.logger, args.wheel_center, angle_level_ratio=args.angle_level_ratio)
        self.river_collisions_1 = 0
        self.chase_bridge_count = 0
        self.game_over = False
        self.game_paused = False

        if args.full_screen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            pygame.display.toggle_fullscreen()
            self.width = pygame.display.get_window_size()[0]
            self.height = pygame.display.get_window_size()[1]
        else:
            self.width = self.args.width
            self.height = self.args.height
            self.screen: pygame.Surface = pygame.display.set_mode((self.width, self.height))
        self.game_intro = TGameIntro(self.screen, os.path.join(TSprite.SPRITES_DIR, 'background1.jpg'),  self.racing_wheel)
        self.my_car = self.create_my_car()
        self.saved_my_car = None
        self.robber_car = None

        self.map_part: TMapPart = None
        self.map_part_next = None
        self.passenger_in_car: TSprite = None
        self.exit_game = False

    def get_car_top(self):
        return self.my_car.sprite.rect.top

    def get_dashboard(self) -> TCarDashboard :
        return self.my_car.dashboard

    def create_my_car(self):
        self.my_car = BaseCar(self.logger,
                    self.screen,
                    self.sounds,
                    self.args.my_sprite_folder, self.args.engine_audio_folder, None, self.args.max_car_speed_limit)
        self.my_car.move_car(self.width / 2, self.height - 250)
        self.car_is_ambulance = False
        return self.my_car

    def create_ambulance(self):
        self.my_car.stop_engine()
        self.sounds.play_sound('granny_wants_to_hospital')
        time.sleep(3)

        sprite_folder = os.path.join(os.path.dirname(__file__), "assets", 'sprites', 'ambulance')
        engine_sound_folder = os.path.join(os.path.dirname(__file__), 'assets/sounds/ambulance')
        max_speed = self.args.max_car_speed_limit
        c = BaseCar(self.logger,
                    self.screen,
                    self.sounds,
                    sprite_folder, engine_sound_folder, "siren", max_speed)
        c.dashboard.is_on_alarm = False
        c.move_car(self.my_car.sprite.rect.left, self.my_car.sprite.rect.top)
        c.start_warm_engine()
        self.saved_my_car = self.my_car
        self.car_is_ambulance = True
        return c

    def init_robber_car(self):
        if not isinstance(self.map_part.car_stop, TBank):
            return
        if self.get_car_top() - self.map_part.car_stop.rect.top > 400:
            return
        if self.robber_car is not None:
            return

        self.chase_bridge_count = 0
        self.logger.info("create robber car")
        self.robber_car = BaseCar(self.logger,
                                  self.screen,
                                  self.sounds,
                                  os.path.join(os.path.dirname(__file__), "assets", 'sprites', 'robber_car'),
                                  os.path.join(os.path.dirname(__file__), 'assets/sounds/robber'),
                                  "police-siren",
                                  5
                                  )
        self.my_car.use_police_light = True
        left, _ = self.map_part.car_stop.rect.center
        self.robber_car.move_car(left, self.finish_top - 100)
        self.sprites.passengers_at_car_stop.empty()
        self.map_part.kill_passengers()
        self.robber_car.start_warm_engine()

    def destroy_robber_car(self, success=True):
        self.logger.info('destroy robber car')
        self.chase_bridge_count = 0
        self.my_car.stop_engine()
        if success:
            length = self.sounds.stop_all_and_play('handcuffs', loops=0)
            time.sleep(length)
            self.get_dashboard().success_tasks_count += 1
        self.robber_car.destroy_car()
        self.robber_car = None
        self.my_car.use_police_light = False
        self.my_car.start_warm_engine()

    def quit(self):
        self.exit_game = True

    def check_finish(self):
        if self.finish_top > self.get_car_top():
            self.my_car.stop_engine()
            if self.get_dashboard().get_score() < self.args.great_victory_level:
                font = pygame.font.SysFont(None, 50)
                screen_text = font.render('Победа! Очки: {}'.format(self.get_dashboard().get_score()), True, TColors.white)
                loops = 0
            else:
                font = pygame.font.SysFont(None, 150)
                screen_text = font.render('Победа! Очки: {}'.format(self.get_dashboard().get_score()), True, TColors.green)
                loops = 1
            self.sounds.stop_all_and_play("victory", loops=loops)
            self.screen.blit(screen_text, (250, 280))
            pygame.display.update()
            time.sleep(5)
            self.draw_game_intro("Очки: {}".format(self.get_dashboard().get_score()))

    def redraw_background(self):
        self.screen.fill(TSprite.BACKGROUND_COLOR)

    def get_engine_sound(self):
        return self.my_car.engine_sound

    def check_river_collision(self, river_sprite):
        if not river_sprite.alive() or river_sprite.collided:
            return
        self.logger.info("river collision")
        self.sounds.play_sound("river_accident", loops=0)
        self.get_engine_sound().set_idling_state()
        river_sprite.collided = True
        self.get_dashboard().river_accident_count += 1
        self.river_collisions_1 += 1
        if self.car_has_granny():
            self.passenger_in_car.river_fall_count += 1
            if self.passenger_in_car.river_fall_count >= 3:
                self.passenger_goes_to_river("granny_sea_voyage")
                #self.make_normal_car()

        if self.river_collisions_1 == 2:
            self.my_car.bad_collision()

    def draw_game_intro(self, message_text=None):
        self.sounds.stop_sounds()
        self.my_car.stop_engine()
        self.game_intro.get_next_action(message_text)
        if self.game_intro.action == TGameIntro.exit_game_action:
            self.quit()
        elif self.game_intro.action == TGameIntro.start_game_action:
            self.game_loop()
        else:
            raise Exception("unknown action")

    def car_bridge_success_event(self):
        if not self.car_is_ambulance:
            self.my_car.promote_to_finish(20)
            self.get_dashboard().bridge_passing_count += 1
            length = self.sounds.play_sound("bridge_passing", loops=0)
            if self.robber_car is not None:
                self.chase_bridge_count += 1
                if self.chase_bridge_count >= self.args.min_chase_bridge_count:
                    time.sleep(length)
                    self.destroy_robber_car()

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

    def get_bank_probability(self):
        bank_prob = self.args.bank_prob
        if self.robber_car is not None:
            bank_prob = 0
        if isinstance(self.map_part.car_stop, TBank):
            bank_prob = 0
        if self.get_car_top() < self.finish_top + 150:
            bank_prob = 0
        return bank_prob

    def _create_next_map_part(self):
        mp = TMapPart(self.screen, -self.height, self.args.bridge_width, self.road_width,
                                      self.map_part.bridge.rect, self.args.girl_probability)
        if self.car_is_ambulance and random.random() < 0.8:
            mp.generate_hospital()
        elif self.my_car.should_generate_gas_station():
            mp.generate_gas_station()
        elif self.my_car.car_needs_repair and random.random() > 0.5:
            mp.generate_repair_station()
        elif self.my_car.broken_tires and random.random() > 0.4 and not isinstance(self.map_part.car_stop, TRepairStation):
            mp.generate_repair_station()
        else:
            gen_granny = not self.car_has_passenger() and random.random() < self.args.passenger_at_stop_prob and not self.map_part.has_passengers()
            bank_prob = self.get_bank_probability()
            mp.generate_town(gen_granny, bank_prob)
        return mp

    def init_new_map_part(self):
        self.logger.debug("init_new_map_part")
        if self.map_part is not None:
            self.map_part.destroy_sprites()
            self.map_part = self.map_part_next
        else:
            #first time
            dummy_rct = pygame.Rect(self.my_car.sprite.rect.center[0] - self.args.bridge_width/2,
                                    self.get_car_top(), self.args.bridge_width, 10)
            self.map_part = TMapPart(self.screen, 0, self.args.bridge_width, self.road_width, dummy_rct, self.args.girl_probability)
            self.map_part.generate_town(True, self.args.bank_prob)
            #self.logger.info("prev rect {}".format(dummy_rct))
            #self.logger.info("car rect {}".format(self.my_car.rect))
            pygame.draw.rect(self.screen, TColors.white, dummy_rct)

        self.map_part_next = self._create_next_map_part()

        self.sprites.rivers.add(self.map_part.river)
        self.sprites.bridges.add(self.map_part.bridge)
        self.sprites.roads.add(self.map_part.road, self.map_part_next.road)
        self.sprites.towns.add(self.map_part.car_stop, self.map_part_next.car_stop)
        self.map_part.add_passengers_to_sprite_group(self.sprites.passengers_at_car_stop)
        self.map_part_next.add_passengers_to_sprite_group(self.sprites.passengers_at_car_stop)
        self.logger.info(self.map_part.get_descr())

    def change_obstacle_positions(self):
        if self.map_part is not None:
            speed = self.my_car.get_speed()
            if speed > 0:
                self.map_part.change_spite_position(speed)
                self.map_part_next.change_spite_position(speed)
            is_map_part_finished = self.map_part.river.rect.top > min(self.height - 100, self.my_car.sprite.rect.bottom + 200)
            #is_map_part_finished = self.map_part.river.rect.top > self.height

            if is_map_part_finished:
                if not self.map_part.river.collided:
                    self.car_bridge_success_event()
                if not self.my_car.pass_map_part():
                    self.draw_game_intro("Нет бензина!")
                    return
                self.init_new_map_part()

    def passenger_gets_on_the_car(self, sprite: TSprite):
        self.sprites.passengers_in_car.empty()
        sprite.parent = self.screen
        sprite.rect.top = self.height - sprite.rect.height
        sprite.rect.left = self.width - sprite.rect.width
        self.passenger_in_car = sprite
        self.sprites.passengers_in_car.add(sprite)
        self.sprites.passengers_at_car_stop.empty()
        self.map_part.passengers.clear()

    def passenger_leaves_car(self, sound_name):
        self.sounds.play_sound(sound_name, loops=0)
        time.sleep(1)
        self.map_part.passenger_goes_to_car_stop(self.passenger_in_car)
        self.map_part.add_passengers_to_sprite_group(self.sprites.passengers_in_car)
        self.passenger_in_car = None

    def passenger_goes_to_river(self, sound_name):
        self.passenger_in_car.kill()
        self.sprites.passengers_in_car.empty()
        self.sounds.play_sound(sound_name, loops=0)
        self.passenger_in_car = None
        time.sleep(1)

    def granny_leaves_the_car(self):
        if self.car_is_ambulance:
            self.sounds.play_sound('granny_wants_to_hospital')
        elif self.map_part.car_stop.color.color == self.get_granny_in_car_color():
            self.logger.info("granny leaves the car")
            self.sounds.play_sound("door_open", loops=0)
            time.sleep(2)
            self.passenger_leaves_car("thank")
            self.get_dashboard().success_tasks_count += 1
        else:
            self.logger.info("granny refuses to leave the car")
            self.sounds.play_sound("door_open", loops=0)
            time.sleep(2)
            self.sounds.play_sound("wrong_stop", loops=0)
            time.sleep(1)

    def open_door(self):
        if self.my_car.get_speed() == 1:
            self.my_car.use_brakes()
            time.sleep(2)

        if self.my_car.get_speed() != 0:
            return

        car_stop = self.my_car.find_collision(self.sprites.towns)
        if (self.my_car.car_needs_repair or self.my_car.broken_tires) and isinstance(car_stop, TRepairStation):
            self.my_car.repair_car()
            self.river_collisions_1 = 0
            return

        if isinstance(car_stop, TGasStation):
            if not self.my_car.is_full_tank():
                self.my_car.refuel_car()
            return

        if isinstance(car_stop, THospital) and self.car_has_passenger():
            self.passenger_leaves_car("thank")
            self.get_dashboard().success_tasks_count += 1
            self.my_car.stop_engine()
            self.my_car = self.saved_my_car
            self.my_car.start_warm_engine()
            return

        passenger_at_car_stop = self.my_car.find_collision(self.sprites.passengers_at_car_stop)
        bridge = self.my_car.find_collision(self.sprites.bridges)

        if passenger_at_car_stop is None:
            if car_stop and car_stop.traveller is not None:
                passenger_at_car_stop = car_stop.traveller
        if passenger_at_car_stop and not self.car_has_passenger():
            self.logger.info("granny comes to the car")
            self.sounds.play_sound("door_open", loops=0)
            time.sleep(1)
            self.passenger_gets_on_the_car(passenger_at_car_stop)


        elif car_stop and self.car_has_granny() and isinstance(car_stop, TTownSprite):
            self.granny_leaves_the_car()
        elif car_stop and self.car_has_girl():
            self.logger.info("girl refuses to leave the car")
            self.sounds.play_sound("door_open", loops=0)
            time.sleep(2)
            self.sounds.play_sound("gde_voda", loops=0)
            time.sleep(1)
        elif bridge and self.car_has_girl():
            self.get_dashboard().success_tasks_count += 1
            self.passenger_goes_to_river("hurra")

    def set_alarm_on(self):
        self.logger.info("set_alarm_on")
        self.get_dashboard().is_on_alarm = True
        self.sounds.stop_sound("alarm")
        self.sounds.play_sound("set_on_alarm", loops=0)
        time.sleep(1)

    def set_alarm_off(self):
        self.logger.info("set_alarm_off")
        self.get_dashboard().is_on_alarm = False
        self.sounds.stop_sound("alarm")
        self.sounds.play_sound("set_off_alarm", loops=0)
        time.sleep(1)

    def increase_speeds(self):
        self.my_car.increase_speed()
        if self.robber_car:
            self.robber_car.increase_speed()

    def decrease_speeds(self):
        self.my_car.decrease_speed()
        if self.robber_car:
            self.robber_car.decrease_speed()
        if self.my_car.get_speed() == 0 and self.robber_car is not None:
            self.destroy_robber_car(False)

    def make_tires_broken(self):
        self.my_car.broken_tires = True

    def process_keyboard_and_wheel_events(self, x_change):
        wheel_angle = self.racing_wheel.get_angle()
        if wheel_angle is not None:
            x_change = wheel_angle
        for event in pygame.event.get():
            #self.logger.debug('event = {}'.format(event))
            if event.type == pygame.QUIT:
                self.game_over = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    x_change = -self.my_car.horizontal_speed
                elif event.key == pygame.K_RIGHT:
                    x_change = +self.my_car.horizontal_speed
                elif event.key == pygame.K_UP:
                    self.logger.info("pygame.K_UP")
                    self.increase_speeds()
                elif event.key == pygame.K_s:
                    self.logger.info("pygame.К_s")
                    self.set_alarm_on()
                elif event.key == pygame.K_f:
                    self.logger.info("pygame.К_f")
                    self.set_alarm_off()
                elif event.key == pygame.K_e:
                    self.logger.info("pygame.К_e")
                    self.my_car.toggle_engine()
                elif event.key == pygame.K_DOWN:
                    self.my_car.use_brakes()
                elif event.key == pygame.K_ESCAPE:
                    self.draw_game_intro()
                elif event.key == pygame.K_SPACE:
                    self.game_paused = not self.game_paused
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
                    self.decrease_speeds()

        if TRacingWheel.right_button in self.racing_wheel.pressed_buttons:
            self.racing_wheel.pressed_buttons.remove(TRacingWheel.right_button)
            if self.get_dashboard().is_on_alarm:
                self.set_alarm_off()
            else:
                self.set_alarm_on()

        if self.racing_wheel.left_hat_was_pressed():
            self.open_door()

        if self.racing_wheel.right_hat_was_pressed():
            self.my_car.toggle_engine()

        if self.my_car.horizontal_speed_increase_with_get_speed:
            car_speed = self.my_car.get_speed()
            if car_speed > 0:
                x_change += 0.01 * x_change * math.sqrt(car_speed)

        self.my_car.shift_horizontally(x_change, self.width)
        return x_change

    def process_wheel_pedals(self):
        if self.game_paused:
            return
        if not self.racing_wheel.is_attached():
            return
        if self.racing_wheel.is_left_pedal_pressed():
            #self.logger.info("left pedal is on")
            self.increase_speeds()
        else:
            #self.logger.info("left pedal is off    ")
            self.decrease_speeds()

        if self.racing_wheel.is_right_pedal_pressed():
            #self.logger.info("right pedal is on")
            self.my_car.use_brakes()

    def redraw_all(self):
        self.redraw_background()
        self.sprites.redraw_without_cars(self.screen)
        pygame.draw.line(self.screen, TColors.white, (0, self.finish_top),
                         (self.width, self.finish_top))

        self.my_car.draw_dashboard(self.game_paused)
        self.my_car.draw()
        if self.robber_car is not None:
            self.robber_car.draw()
        pygame.display.flip()

    def check_all_collisions(self):
        bridge = self.my_car.find_collision(self.sprites.bridges)
        river = self.my_car.find_collision(self.sprites.rivers)
        if bridge is not None:
            pass
        elif river is not None:
            self.check_river_collision(river)
        if self.car_has_granny() and not self.car_is_ambulance:
            if (int(time.time()) % 33 == 0) and random.random() < self.args.granny_heart_attack_probability:
                self.my_car = self.create_ambulance()

    def init_game_loop(self):
        self.game_over = False
        self.my_car = self.create_my_car()
        self.sprites.clear_groups()
        if self.map_part is not None:
            self.map_part.destroy_sprites()
            self.map_part = None
        self.redraw_background()
        self.init_new_map_part()
        self.river_collisions_1 = 0
        self.passenger_in_car = None

    def update_robber_car_position(self):
        if self.robber_car is None:
            return
        src = self.robber_car.sprite.rect.center
        trg = None
        for m in self.sprites.bridges:
            trg = m.rect.center
            break
        if not trg:
            self.logger.info("no bridge to head towards")
            return
        distance_x = int(src[0] - trg[0])
        if abs(distance_x) < 15:
            #self.logger.info("already correct direction")
            return
        shift = int(distance_x / 10)
        self.robber_car.shift_horizontally(-shift, self.width)
        #self.logger.info("robber car is on {}".format(self.robber_car.rect.center))

    def game_loop(self):
        self.init_game_loop()
        x_change = 0
        #self.make_ambulance()
        if self.args.engine_auto_start:
            self.my_car.start_warm_engine()
        cycle_index = 0

        while not self.game_over and not self.exit_game:
            self.process_wheel_pedals()
            x_change = self.process_keyboard_and_wheel_events(x_change)
            if not self.game_paused:
                self.change_obstacle_positions()
            self.check_finish()
            self.check_all_collisions()
            self.redraw_all()
            clock.tick(20)
            #pygame.time.delay(200)
            #if self.robber_car is not None:
            #    self.police_light.render(self.screen, self.my_car.rect.center)
            if self.get_car_top() + 30 > self.height:
                self.my_car.sprite.rect.top = self.height - 30
            cycle_index += 1
            if (cycle_index % 300 == 0) and self.get_dashboard().is_on_alarm and self.my_car.get_speed() > 0:
                if self.sounds.has_sound("alarm"):
                    self.sounds.play_sound("alarm")
            if cycle_index % 10 == 0:
                self.init_robber_car()
                self.update_robber_car_position()
            if cycle_index % 161 == 0:
                if not self.my_car.broken_tires and random.random() > 0.99:
                    if self.my_car.get_speed() > 0:
                        self.my_car.broken_tires = True
                        self.logger.info("tires are broken!")
                self.my_car.set_broken_tires_sound()


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
    parser.add_argument("--girl-probability", dest='girl_probability', default=0.4, type=float)
    parser.add_argument("--granny-heart-attack-probability", dest='granny_heart_attack_probability', default=0.005, type=float)
    parser.add_argument("--engine-auto-start", dest='engine_auto_start', default=False, action="store_true")
    parser.add_argument("--passenger-at-stop-prob", dest='passenger_at_stop_prob', default=0.7, type=float)
    parser.add_argument("--min-chase-bridge-count", dest='min_chase_bridge_count', default=3, type=int)
    parser.add_argument("--bank-prob", dest='bank_prob', default=0.05, type=float)

    return parser.parse_args()


if __name__ == "__main__":
    clock = pygame.time.Clock()
    args = parse_args()

    pygame.display.init()
    pygame.font.init()
    game = TRiverGame(args)
    game.draw_game_intro()



