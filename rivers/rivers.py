from river_sprites import TPrison
from utils.logging_wrapper import setup_logging
from utils.racing_wheel import TRacingWheel
from utils.colors import TColors
from utils.game_sounds import TSounds
from utils.game_intro import TGameIntro
from river_sprites import TSprite, TMapPart, TGrannySprite, TRepairStation, TGirlSprite,TGasStation, \
    TRiverSprites,  THospital, TTownSprite, TBank, TRobberSprite, TForest
from car_dashboard import TCarDashboard
from vehicles import BaseCar
from threading import Thread

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
        self.sounds = TSounds(SOUNDS_DIR, not args.silent, self.logger)
        self.racing_wheel = TRacingWheel(self.logger, args.wheel_center, angle_level_ratio=args.angle_level_ratio)
        self.game_over = False
        self.game_paused = False
        self.exit_game = False
        self.ambulance_index  = 0
        self.x_change = 0

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
        vars = ['granny_wants_to_hospital', 'granny_wants_to_hospital1', 'granny_wants_to_hospital2', 'granny_wants_to_hospital3']
        snd_name = random.choice(vars)
        delay = self.sounds.play_sound(snd_name)
        time.sleep(delay)

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
        c.add_passenger(self.my_car.passenger)
        self.my_car.remove_passenger()

        return c

    def init_robber_car(self):
        if not isinstance(self.map_part.car_stop, TBank):
            return
        if self.get_car_top() - self.map_part.car_stop.rect.top > 400:
            return
        if self.robber_car is not None:
            return

        self.get_dashboard().chase_bridge_count = 0
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
        self.get_dashboard().chase_bridge_count = 0
        self.my_car.stop_engine()
        if success:
            length = self.sounds.stop_all_and_play('handcuffs', loops=0)
            time.sleep(length)
            self.get_dashboard().success_tasks_count += 1
            self.passenger_gets_on_the_car(TRobberSprite(self.screen, 0, 0))

        self.robber_car.destroy_car()
        self.robber_car = None
        self.my_car.use_police_light = False
        self.my_car.start_warm_engine()


    def quit(self):
        self.exit_game = True

    def check_finish(self):
        if self.finish_top > self.get_car_top():
            self.my_car.stop_engine()
            self.my_car.remove_passenger(True)
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
        if self.car_has_granny():
            self.my_car.passenger.river_fall_count += 1
            if self.my_car.passenger.river_fall_count >= 3:
                self.passenger_goes_to_river("granny_sea_voyage")

        if self.get_dashboard().too_many_rivers_accidents():
            self.my_car.bad_collision()

    def check_gates_collision(self, gate_sprite):
        if not gate_sprite.alive() or gate_sprite.collided:
            return
        self.logger.info("gate collision")
        self.sounds.play_sound("gates_accident", loops=0)
        self.get_engine_sound().set_idling_state()
        gate_sprite.collided = True
        self.get_dashboard().gates_accident_count += 1
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
                self.get_dashboard().chase_bridge_count += 1
                if self.get_dashboard().chase_bridge_count >= self.args.min_chase_bridge_count:
                    time.sleep(length)
                    self.destroy_robber_car()

    def car_has_passenger(self):
        return self.my_car.passenger is not None

    def car_has_granny(self):
        if self.my_car.passenger is None:
            return False
        return isinstance(self.my_car.passenger, TGrannySprite)

    def car_has_girl(self):
        if self.my_car.passenger is None:
            return False
        return isinstance(self.my_car.passenger, TGirlSprite)

    def get_granny_in_car_color(self):
        if not self.car_has_granny():
            return None
        return self.my_car.passenger.color.color

    def my_car_has_robber(self):
        return self.my_car.passenger and isinstance(self.my_car.passenger, TRobberSprite)

    def get_bank_probability(self):
        if self.robber_car is not None:
            return 0
        if isinstance(self.map_part.car_stop, TBank):
            return 0
        if self.get_car_top() < self.finish_top + 150:
            return 0
        if self.my_car_has_robber():
                return 0
        return self.args.bank_prob

    def get_random_car_stop_type(self):
        r = random.random()
        weights  = [
                (self.args.forest_prob, "forest"),
                (self.get_bank_probability(), "bank"),
                (self.args.gates_prob, "gates"),
            ]
        s = 0
        for w, name in weights:
            s += w
            if r <= s:
                return name
        return "town"


    def _create_next_map_part(self):
        mp = TMapPart(self.screen, -self.height, self.args.bridge_width, self.road_width,
                                      self.map_part.bridge.rect, self.args.girl_probability)
        if self.car_is_ambulance and random.random() < 0.8:
            mp.generate_hospital()
        elif self.my_car.should_generate_gas_station():
            mp.generate_gas_station()
        elif self.my_car_has_robber() and random.random()  < 0.8:
            mp.generate_prison()
        elif self.my_car.car_needs_repair and random.random() > 0.4:
            mp.generate_repair_station()
        elif self.my_car.broken_tires and random.random() > 0.4 and not isinstance(self.map_part.car_stop, TRepairStation):
            mp.generate_repair_station()
        else:
            t = self.get_random_car_stop_type()
            if t == "forest":
                mp.generate_forest()
            elif t == "bank":
                mp.generate_bank()
            elif t == "gates":
                mp.generate_gates()
            else:
                assert t == "town"
                gen_granny = not self.car_has_passenger() and random.random() < self.args.passenger_at_stop_prob and not self.map_part.has_passengers()
                mp.generate_town(gen_granny)
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
            self.map_part.generate_town(True)
            pygame.draw.rect(self.screen, TColors.white, dummy_rct)

        self.map_part_next = self._create_next_map_part()
        self.sprites.update_spites(self.map_part)
        self.sprites.update_spites(self.map_part_next)
        self.logger.info(self.map_part.get_descr())

    def change_obstacle_positions(self):
        if self.map_part is not None:
            speed = self.my_car.get_speed()
            if speed > 0:
                self.map_part.change_spite_position(speed)
                self.map_part_next.change_spite_position(speed)
            is_map_part_finished = self.map_part.river.rect.top >= self.height

            if is_map_part_finished:
                if not self.map_part.river.collided:
                    self.car_bridge_success_event()
                if not self.my_car.pass_map_part():
                    self.draw_game_intro("Нет бензина!")
                    return
                self.init_new_map_part()

    def passenger_gets_on_the_car(self, sprite: TSprite):
        self.sprites.passengers_at_car_stop.empty()
        self.map_part.car_stop.traveller = None
        self.my_car.add_passenger(sprite)

    def passenger_leaves_car(self, sound_name, success=True):
        len = self.sounds.play_sound(sound_name, loops=0)
        time.sleep(len)
        self.map_part.passenger_goes_to_car_stop(self.my_car.passenger)
        self.my_car.remove_passenger()
        if success:
            self.get_dashboard().success_tasks_count += 1

    def passenger_goes_to_river(self, sound_name):
        self.my_car.remove_passenger(True)
        self.sounds.play_sound(sound_name, loops=0)
        time.sleep(1)

    def granny_leaves_the_car(self):
        if self.car_is_ambulance:
            #self.sounds.play_sound('granny_wants_to_hospital')
            pass
        elif not hasattr(self.map_part.car_stop, "color"):
            #it is not a town
            pass
        elif self.map_part.car_stop.color.color == self.get_granny_in_car_color():
            self.logger.info("granny leaves the car")
            self.door_open()
            self.passenger_leaves_car("thank")
        else:
            self.logger.info("granny refuses to leave the car")
            self.door_open()
            self.sounds.play_sound("wrong_stop", loops=0)
            time.sleep(1)

    def bird_sings(self):
        self.logger.info("a bird sings")
        self.sounds.play_sound("bird", loops=0)

    def move_gates_to_the_left(self, gates):
        gates.collided = True
        seconds = int(self.sounds.play_sound("car_horn"))
        time.sleep(seconds)
        time.sleep(1)
        seconds = int(self.sounds.play_sound("rolling_gates_open")) - 4
        step = gates.rect.right / (seconds - 5)
        for i in range(int(seconds)):
            gates.rect.left -= step
            #self.redraw_all()
            time.sleep(1)
        gates.kill()

    def check_gates(self):
        print("len(self.sprites.gates) = {}".format(len(self.sprites.gates)))
        gates = list()
        for g in self.sprites.gates:
            if g.alive() and not g.collided and g.rect.top > 1:
                gates.append((self.my_car.sprite.rect.top, g))

        for _, g  in sorted(gates, reverse=True, key=lambda x: x[0]):
            thread = Thread(target=self.move_gates_to_the_left, args=(g,))
            thread.start()
            return True

        return False

    def door_open(self):
        self.sounds.play_sound("door_open", loops=0)
        time.sleep(2)
        self.get_dashboard().door_open_count += 1

    def on_press_main_user_button(self):
        if self.my_car.get_speed() == 1:
            self.my_car.use_brakes()
            time.sleep(2)

        if self.my_car.get_speed() != 0:
            return

        if self.check_gates():
            return

        car_stop = self.my_car.find_collision(self.sprites.towns)
        if (self.my_car.car_needs_repair or self.my_car.broken_tires) and isinstance(car_stop, TRepairStation):
            self.my_car.repair_car()
            return

        if isinstance(car_stop, TGasStation):
            if not self.my_car.is_full_tank():
                self.my_car.refuel_car()
            return

        if isinstance(car_stop, THospital) and self.car_has_passenger():
            self.my_car.stop_engine()
            self.passenger_leaves_car("hospital")
            self.my_car = self.saved_my_car
            self.my_car.start_warm_engine()
            if self.robber_car:
                self.destroy_robber_car(False)
            self.car_is_ambulance = False
            return

        passenger_at_car_stop = self.my_car.find_collision(self.sprites.passengers_at_car_stop)
        bridge = self.my_car.find_collision(self.sprites.bridges)
        is_town  = car_stop and isinstance(car_stop, TTownSprite)
        if passenger_at_car_stop is None:
            if is_town and car_stop.traveller is not None:
                passenger_at_car_stop = car_stop.traveller
        if passenger_at_car_stop and not self.car_has_passenger():
            self.logger.info("granny comes to the car")
            self.door_open()
            self.passenger_gets_on_the_car(passenger_at_car_stop)

        elif car_stop and self.car_has_granny() and is_town:
            self.granny_leaves_the_car()
        elif car_stop and isinstance(car_stop, TForest):
            self.bird_sings()
        elif car_stop and self.car_has_girl():
            self.logger.info("girl refuses to leave the car")
            self.door_open()
            self.sounds.play_sound("gde_voda", loops=0)
            time.sleep(1)
        elif bridge and self.car_has_girl():
            self.get_dashboard().success_tasks_count += 1
            self.passenger_goes_to_river("hurra")
        elif car_stop and self.my_car_has_robber():
            self.logger.info("robber goes to the prison")
            if isinstance(car_stop, TPrison):
                self.my_car.stop_engine()
                self.passenger_leaves_car("prison_gate")
                self.my_car.start_warm_engine()
            else:
                self.passenger_leaves_car("lets_robber", False)
        elif not self.my_car.engine and not self.get_dashboard().is_on_alarm and self.get_dashboard().map_parts_count == 0:
            self.door_open()


    def set_alarm_on(self):
        self.logger.info("set_alarm_on")
        self.get_dashboard().is_on_alarm = True
        self.sounds.stop_sound("alarm")
        self.sounds.play_sound("set_on_alarm", loops=0)
        time.sleep(1)

    def set_horn_on(self):
        if not  self.get_dashboard().is_on_horn:
            self.logger.info("set_horn_on")
            self.get_dashboard().is_on_horn = True
            self.sounds.stop_sound("car_horn")
            self.sounds.play_sound("car_horn", loops=10)
            self.check_gates()

    def set_horn_off(self):
        if self.get_dashboard().is_on_horn:
            self.logger.info("set_horn_off")
            self.get_dashboard().is_on_horn = False
            self.sounds.stop_sound("car_horn")

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

    def process_wheel_events(self):
        if self.game_paused:
            return
        if not self.racing_wheel.is_attached():
            return
        if self.racing_wheel.is_right_pedal_pressed():
            #self.logger.info("left pedal is on")
            self.increase_speeds()
        else:
            #self.logger.info("left pedal is off    ")
            self.decrease_speeds()

        if self.racing_wheel.is_left_pedal_pressed():
            #self.logger.info("right pedal is on")
            self.my_car.use_brakes()

        self.racing_wheel.read_wheel_events()
        wheel_angle = self.racing_wheel.get_wheel_angle()
        if wheel_angle is not None:
            self.x_change = wheel_angle
        if TRacingWheel.right_button in self.racing_wheel.pressed_buttons:
            self.racing_wheel.pressed_buttons.remove(TRacingWheel.right_button)
            if self.get_dashboard().is_on_alarm:
                self.set_alarm_off()
            else:
                self.set_alarm_on()

        if TRacingWheel.left_button in self.racing_wheel.pressed_buttons:
            #self.logger.info("call self.set_horn_on")
            self.set_horn_on()
        else:
            #self.logger.info("call self.set_horn_off")
            self.set_horn_off()

        if self.racing_wheel.left_hat_was_pressed():
            self.on_press_main_user_button()

        if self.racing_wheel.right_hat_was_pressed():
            if self.get_dashboard().door_open_count > 0:
                self.my_car.toggle_engine()

    def process_keyboard_events(self):
        for event in pygame.event.get():
            #self.logger.debug('event = {}'.format(event))
            if event.type == pygame.QUIT:
                self.game_over = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.x_change = -self.my_car.horizontal_speed
                elif event.key == pygame.K_RIGHT:
                    self.x_change = +self.my_car.horizontal_speed
                elif event.key == pygame.K_UP:
                    self.logger.info("pygame.K_UP")
                    self.increase_speeds()
                elif event.key == pygame.K_s:
                    self.logger.info("pygame.К_s")
                    self.set_alarm_on()
                elif event.key == pygame.K_h:
                    self.set_horn_on()
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
                    self.on_press_main_user_button()
                elif event.key == pygame.K_F1:
                    self.racing_wheel.save_wheel_center()
                elif event.key == pygame.K_F2:
                    self.door_open()

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    self.x_change = 0
                elif event.key == pygame.K_UP:
                    self.decrease_speeds()
                elif event.key == pygame.K_h:
                    self.set_horn_off()


    def move_horizontally(self):
        if self.my_car.horizontal_speed_increase_with_get_speed:
            car_speed = self.my_car.get_speed()
            if car_speed > 0:
                self.x_change += 0.01 * self.x_change * math.sqrt(car_speed)
        self.my_car.shift_horizontally(self.x_change, self.width)


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
        gates = self.my_car.find_collision(self.sprites.gates)
        if bridge is not None:
            pass
        elif river is not None:
            self.check_river_collision(river)
        elif gates is not None:
            self.check_gates_collision(gates)
        if self.car_has_granny() and not self.car_is_ambulance:
            self.ambulance_index += 1
            if (self.ambulance_index % 60 == 0) and random.random() < self.args.granny_heart_attack_probability:
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
        self.x_change = 0
        #self.make_ambulance()
        if self.args.engine_auto_start:
            self.my_car.start_warm_engine()
        cycle_index = 0

        #dummy = TPrison(self.screen, 0, -20)

        while not self.game_over and not self.exit_game:
            self.process_wheel_events()
            self.process_keyboard_events()
            self.move_horizontally()
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
    parser.add_argument("--silent", default=False, action="store_true")
    parser.add_argument("--wheel-center", default=300, type=int)
    parser.add_argument("--great-victory-level",  default=15, type=int)
    parser.add_argument("--full-screen",  default=False, action="store_true")
    parser.add_argument("--width",  default=1600, type=int)
    parser.add_argument("--height",  default=1000, type=int)
    parser.add_argument("--max-car-speed-limit",  default=10, type=int)
    parser.add_argument("--bridge-width",  default=300, type=int)
    parser.add_argument("--verbose",  default=False, action="store_true")

    parser.add_argument("--car-sprite-folder", dest='my_sprite_folder')
    parser.add_argument("--angle-level-ratio", type=float, default=30,
                        help="the less value, the less one must turn the angle to change the direction")
    parser.add_argument("--engine-audio-folder",
                        default= os.path.join(os.path.dirname(__file__), 'assets/sounds/ford'))
    parser.add_argument("--girl-probability",  default=0.4, type=float)
    parser.add_argument("--granny-heart-attack-probability",  default=0.003, type=float)
    parser.add_argument("--engine-auto-start", default=False, action="store_true")
    parser.add_argument("--passenger-at-stop-prob", default=0.7, type=float)
    parser.add_argument("--min-chase-bridge-count",  default=3, type=int)
    parser.add_argument("--bank-prob", default=0.05, type=float)
    parser.add_argument("--forest-prob", default=0.03, type=float)
    parser.add_argument("--gates-prob", default=0.03, type=float)

    return parser.parse_args()


if __name__ == "__main__":
    clock = pygame.time.Clock()
    args = parse_args()

    pygame.display.init()
    pygame.font.init()
    game = TRiverGame(args)
    game.draw_game_intro()



