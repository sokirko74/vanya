import pygame
import random
import os


class TCat(pygame.sprite.Sprite):
    sprites = [
        ('cat.png', 'sound_cat.wav'),
    ]

    def __init__(self, parent, pos):
        pygame.sprite.Sprite.__init__(self)
        self.parent = parent
        sprite_basename, sound_basename = random.choice(self.sprites)
        self.image = pygame.image.load(os.path.join('assets', 'sprites', sprite_basename))
        self.sound_wants_milk = pygame.mixer.Sound(os.path.join('assets', 'sounds', sound_basename))
        self.sound_wants_milk.set_volume(0.2)
        self.sound_thanks = pygame.mixer.Sound(os.path.join('assets', 'sounds', "cat_thank.wav"))
        self.sound_thanks.set_volume(0.6)

        self.image = pygame.transform.scale(self.image, (100, 100))
        self.rect = self.image.get_rect()
        self.rect.topleft = pygame.math.Vector2(self.parent.maze_rect.topleft) + pos
        self.contacted = False

    def contact_object(self):
        if self.parent.player.loaded_with_milk:
            if not self.parent.chan_2.get_busy():
                self.parent.chan_2.play(self.sound_thanks)
            self.parent.player.unload_milk()
            self.kill()
        else:
            if not self.parent.chan_2.get_busy():
                self.parent.chan_2.play(self.sound_wants_milk)
