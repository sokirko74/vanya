import os
import random

import pygame 
import json


class TSounds:

    def __init__(self, sounds_dir, enable_sounds, logger):
        self.enable_sounds = enable_sounds
        self.logger = logger
        self._sounds = dict()
        self._birds = list()

        if self.enable_sounds:
            pygame.mixer.init()
            with open (os.path.join(sounds_dir, "sounds.json")) as inp:
                for k, v in json.load(inp).items():
                    path = os.path.join(sounds_dir, k + ".wav")
                    sound = pygame.mixer.Sound(path)
                    sound.set_volume(v['volume'])
                    self._sounds[k] = sound
            bird_dir = os.path.join(sounds_dir, "birds")
            for f in os.listdir(bird_dir):
                if f.endswith('.wav'):
                    path = os.path.join(bird_dir, f)
                    sound = pygame.mixer.Sound(path)
                    self._sounds[f] = sound
                    self._birds.append(f)
            self.logger.info("birds: {}".format(self._birds))

    def set_sound(self, key, path, volume=None):
        if path is None and key in self._sounds:
            del self._sounds[key]
        elif path is not None:
            sound = pygame.mixer.Sound(path)
            if volume is not None:
                sound.set_volume(volume)
            self._sounds[key] = sound

    def has_sound(self, key):
        return key in self._sounds and self._sounds[key]

    def stop_sounds(self):
        for k in self._sounds.values():
            k.stop()

    def play_sound(self, sound_type, loops=0, volume=None):
        if not self.enable_sounds:
            return 0
        if sound_type == 'bird':
            sound_type = random.choice(self._birds)
        if volume is not None:
            self._sounds[sound_type].set_volume(volume)
        self.logger.info("play {}".format(sound_type))
        self._sounds[sound_type].play(loops=loops)
        length = self._sounds[sound_type].get_length()
        return length

    def this_sound_is_playing(self, sound_type):
        for i in range(pygame.mixer.get_num_channels()):
            channel = pygame.mixer.Channel(i)
            sound = channel.get_sound()
            if sound == self._sounds[sound_type]:
                return True
        return False

    def stop_sound(self, sound_type):
        sound = self._sounds.get(sound_type)
        if sound:
            sound.stop()

    def stop_all_and_play(self, sound_type, loops=1000, volume=None):
        self.stop_sounds()
        return self.play_sound(sound_type, loops=loops, volume=volume)

