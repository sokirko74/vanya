from river_sprites import TCarSprite
from car_dashboard import TCarDashboard
import gif_pygame
from threading import Lock
import pygame
import os
import time
from engine_sound import TEngineSound
import random

MAX_FUEL_VOLUME = 5
RED_LAMP_FUEL_MIN_LEVEL = 2


class BaseCar:
    def __init__(self, logger, screen, sounds, sprite_folder,
                 engine_sound_folder, siren, max_car_speed_limit,
                 horizontal_speed=10):
        self.logger = logger
        self.screen = screen
        self.sounds = sounds
        self.engine = False
        self.sprite_folder = sprite_folder
        self.siren = siren
        self.engine_sound_folder = engine_sound_folder
        self.max_car_speed_limit = max_car_speed_limit
        self.engine_sound = None
        self.car_needs_repair = False
        self.broken_tires = False
        self.start_engine_mutex = Lock()
        self.use_police_light = False
        self.police_light = gif_pygame.load(os.path.join(os.path.dirname(__file__), 'assets/animation/police-lights.gif'))
        self.sprite_group = pygame.sprite.Group()
        self.sprite = TCarSprite(self.screen, self.sprite_folder)
        self.name = os.path.basename(sprite_folder)
        self.sprite_group.add(self.sprite)
        if self.siren:
            self.sounds.stop_all_and_play(self.siren)
        self.init_engine_sound(False)
        self.horizontal_speed = horizontal_speed
        self.horizontal_speed_increase_with_get_speed = True
        self.fuel_volume = MAX_FUEL_VOLUME
        #self.fuel_volume = 1
        self.dashboard = TCarDashboard(screen)

    def init_engine_sound(self, start_playing=True):
        if self.car_needs_repair:
            folder = os.path.join(os.path.dirname(__file__), 'assets/sounds/vaz_wo_muffler')
        else:
            folder = self.engine_sound_folder
        new_engine_sound = TEngineSound(self.logger, folder, self.max_car_speed_limit + 1, self.sounds)
        old_engine_sound = self.engine_sound
        self.engine_sound = new_engine_sound
        if start_playing:
            self.engine_sound.start_play_stream()
        if old_engine_sound is not None:
            old_engine_sound.stop_engine()

    def move_car(self, left, top):
        self.sprite.rect.left = left
        self.sprite.rect.top = top

    def shift_horizontally(self, delta, max_width):
        self.sprite.rect.left += delta
        if self.sprite.rect.left < 0:
            self.sprite.rect.left = 0
        if self.sprite.rect.left > max_width - 50:
            self.sprite.rect.left = max_width - 50

    def promote_to_finish(self, delta):
        self.sprite.rect.top -= delta

    def destroy_car(self):
        if self.siren:
            self.sounds.stop_sound(self.siren)
        self.stop_engine()
        self.sprite_group.empty()

    def bad_collision(self):
        if not self.car_needs_repair:
            self.car_needs_repair = True
            self.init_engine_sound()

    def repair_car(self):
        self.car_needs_repair = False
        self.sounds.play_sound("repair_car", loops=0)
        self.init_engine_sound()
        self.broken_tires = False

    def find_collision(self, sprites):
        return pygame.sprite.spritecollideany(self.sprite, sprites,
                                              collided=pygame.sprite.collide_mask)

    def draw(self):
        self.sprite_group.draw(self.screen)
        if self.use_police_light:
            p = self.sprite.rect.center
            self.police_light.render(self.screen, (p[0] - self.sprite.rect.width / 2 + 10, p[1]))

    def start_warm_engine(self):
        with self.start_engine_mutex:
            if not self.engine:
                self.logger.info("{} start warm engine".format(self.name))
                self.engine_sound.start_play_stream()
                self.engine = True

    def start_cold_engine(self):
        with self.start_engine_mutex:
            if not self.engine:
                self.logger.info("start cold engine")
                self.sounds.stop_sound("engine_start")
                length = self.sounds.play_sound("engine_start", loops=0)
                time.sleep(length - 0.5)
                self.engine_sound.start_play_stream()
                self.engine = True

    def get_speed(self):
        if not self.engine:
            return 0
        engine_speed = self.engine_sound.get_current_speed()
        self.logger.debug('engine speed = {}'.format(engine_speed))
        return engine_speed - 1

    def set_broken_tires_sound(self):
        if self.get_speed() > 0 and self.broken_tires:
            if not self.sounds.this_sound_is_playing("broken_tires"):
                self.sounds.play_sound('broken_tires')
        else:
            if self.sounds.this_sound_is_playing("broken_tires"):
                self.sounds.stop_sound("broken_tires")

    def use_brakes(self):
        if self.engine:
            self.logger.info("use brakes")
            self.sounds.play_sound("brakes", loops=0)
            self.engine_sound.set_idling_state()

    def refuel_car(self):
        if not self.engine:
            length = self.sounds.play_sound("gas_station", loops=0)
            time.sleep(length)
            self.fuel_volume = MAX_FUEL_VOLUME
        else:
            self.logger.info("stop engine, before refuel")

    def stop_engine(self):
        self.logger.info("{} stop cold engine".format(self.name))
        self.engine = False
        if self.engine_sound is not None:
            self.engine_sound.stop_engine()
        if self.siren:
            self.sounds.stop_sound(self.siren)

    def increase_speed(self):
        if self.engine:
            if self.engine_sound.increase_speed():
                self.logger.info("{} increase speed".format(self.name))
        else:
            self.logger.debug("no effect, since engine does not work")

    def decrease_speed(self):
        if self.engine:
            if self.engine_sound.decrease_speed():
                self.logger.info("{} decrease speed".format(self.name))

    def toggle_engine(self):
        if self.engine:
            self.stop_engine()
        else:
            self.start_cold_engine()

    def is_full_tank(self):
        return self.fuel_volume == MAX_FUEL_VOLUME

    def should_generate_gas_station(self):
        return self.need_fuel() and random.random() > 1.5 * self.fuel_volume / MAX_FUEL_VOLUME #prod

    def need_fuel(self):
        return self.fuel_volume <= RED_LAMP_FUEL_MIN_LEVEL

    def decrement_fuel(self):
        self.fuel_volume -= 1
        return self.fuel_volume > 0

    def get_fuel_volume(self):
        return self.fuel_volume

    def draw_dashboard(self, game_paused):
        self.dashboard.draw_params(
            game_paused,
            self.sprite.rect.top,
            self.get_speed(),
            self.car_needs_repair,
            self.broken_tires,
            self.get_fuel_volume(),
            self.need_fuel(),
            self.engine
        )

    def pass_map_part(self):
        self.dashboard.map_parts_count += 1

        if (self.dashboard.map_parts_count % 3) == 0:
            if not self.decrement_fuel():
                return False
        return True

