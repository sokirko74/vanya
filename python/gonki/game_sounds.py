import os 
import pygame 


def load_sound(file_path, volume):
    sound = pygame.mixer.Sound(file_path)
    sound.set_volume(volume)
    return sound


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

    def __init__(self, sounds_dir, enable_sounds):
        self.enable_sounds = enable_sounds
        self.sounds = dict()
        if self.enable_sounds:
            pygame.mixer.init()
            self.sounds = {
                self.roadside: load_sound(os.path.join(sounds_dir, "roadside.wav"), 0.4),
                self.normal_driving: load_sound(os.path.join(sounds_dir, "normal_driving.wav"), 0.3),
                self.accident: load_sound(os.path.join(sounds_dir, "accident.wav"), 1),
                self.victory: load_sound(os.path.join(sounds_dir, "victory.wav"), 1),
                self.truck: load_sound(os.path.join(sounds_dir, "truck.wav"), 0.6),
                self.tractor: load_sound(os.path.join(sounds_dir, "tractor.wav"), 1),
                self.spider: load_sound(os.path.join(sounds_dir, "spider.wav"), 0.2),
                self.spider_accident: load_sound(os.path.join(sounds_dir, "spider_accident.wav"), 1),
                self.mosquito: load_sound(os.path.join(sounds_dir, "mosquito.wav"), 0.2),
                self.mosquito_accident: load_sound(os.path.join(sounds_dir, "mosquito_accident.wav"), 0.2),
                self.car_honk_left: load_sound(os.path.join(sounds_dir, "car_honk_left.wav"), 0.3),
                self.car_honk_right: load_sound(os.path.join(sounds_dir, "car_honk_right.wav"), 0.3),
                self.puddle_accident: load_sound(os.path.join(sounds_dir, "puddle.wav"), 0.3),
                self.broken_driving: load_sound(os.path.join(sounds_dir, "broken_driving.wav"), 0.3),
                self.repair_car: load_sound(os.path.join(sounds_dir, "repair_car.wav"), 0.3),
            }

    def stop_sounds(self):
        if self.enable_sounds:
            for k in self.sounds.values():
                k.stop()

    def switch_music(self, sound_type, loops=1000):
        if self.enable_sounds:
            self.stop_sounds()
            self.sounds[sound_type].play(loops=loops)

    def play_sound(self, sound_type):
        self.sounds[sound_type].play()
