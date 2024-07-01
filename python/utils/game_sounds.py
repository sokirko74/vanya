import os 
import pygame 
import json


class TSounds:

    def __init__(self, sounds_dir, enable_sounds):
        self.enable_sounds = enable_sounds
        self._sounds = dict()
        if self.enable_sounds:
            pygame.mixer.init()
            with open (os.path.join(sounds_dir, "sounds.json")) as inp:
                for k, v in json.load(inp).items():
                    path = os.path.join(sounds_dir, k + ".wav")
                    sound = pygame.mixer.Sound(path)
                    sound.set_volume(v['volume'])
                    self._sounds[k] = sound

    def stop_sounds(self):
        for k in self._sounds.values():
            k.stop()

    def play_sound(self, sound_type, loops=0, volume=None):
        length = 0
        if self.enable_sounds:
            if volume is not None:
                self._sounds[sound_type].set_volume(volume)
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
        self.play_sound(sound_type, loops=loops, volume=volume)

