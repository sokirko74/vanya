import os 
import pygame 
import json


class TSounds:

    def __init__(self, sounds_dir, enable_sounds):
        self.enable_sounds = enable_sounds
        self.sounds = dict()
        if self.enable_sounds:
            pygame.mixer.init()
            with open (os.path.join(sounds_dir, "sounds.json")) as inp:
                for k, v in json.load(inp).items():
                    path = os.path.join(sounds_dir, k + ".wav")
                    sound = pygame.mixer.Sound(path)
                    sound.set_volume(v['volume'])
                    self.sounds[k] = sound

    def stop_sounds(self):
        for k in self.sounds.values():
            k.stop()

    def play_sound(self, sound_type, loops=0, volume=None):
        if self.enable_sounds:
            if volume is not None:
                self.sounds[sound_type].set_volume(volume)
            self.sounds[sound_type].play(loops=loops)

    def stop_all_and_play(self, sound_type, loops=1000, volume=None):
        self.stop_sounds()
        self.play_sound(sound_type, loops=loops, volume=volume)

