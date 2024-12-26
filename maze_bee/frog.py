import pygame
import random
import os


class TFrog(pygame.sprite.Sprite):
    sprites = [
        ('frog.png', 'sound_frog.wav'),
    ]

    def __init__(self, parent, pos):
        pygame.sprite.Sprite.__init__(self)
        self.parent = parent
        sprite_basename, sound_basename = random.choice(self.sprites)
        self.image = pygame.image.load(os.path.join('assets', 'sprites', sprite_basename))
        self.sound_frog = pygame.mixer.Sound(os.path.join('assets', 'sounds', sound_basename))
        self.sound_frog.set_volume(0.2)
        self.image = pygame.transform.scale(self.image, (50, 50))
        self.rect = self.image.get_rect()
        self.rect.topleft = pygame.math.Vector2(self.parent.maze_rect.topleft) + pos
        self.contacted = False

    def contact_object(self):
        if not self.contacted:
            if not self.parent.chan_2.get_busy():
                self.parent.chan_2.play(self.sound_frog)
        self.contacted = True
        self.parent.open_closed_rooms()
        self.kill()
