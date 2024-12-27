import pygame
import random
import os


class TFlower(pygame.sprite.Sprite):
    sprites = [
        ('flower.png', 'sound_flower.wav'),
        ('flower1.png', 'sound_flower1.wav'),
        ('flower2.png', 'sound_flower2.wav'),
        ('flower3.png', 'sound_flower3.wav'),
    ]

    def __init__(self, parent, pos):
        pygame.sprite.Sprite.__init__(self)
        self.parent = parent
        sprite_basename, sound_basename = random.choice(self.sprites)
        self.image = pygame.image.load(os.path.join('assets', 'sprites', sprite_basename))
        self.sound_flower = pygame.mixer.Sound(os.path.join('assets', 'sounds', sound_basename))
        self.image = pygame.transform.scale(self.image,
                                            (100,
                                             100))
        self.rect = self.image.get_rect()
        self.rect.topleft = pygame.math.Vector2(self.parent.maze_rect.topleft) + pos

    def contact_object(self):
        if not self.parent.chan_2.get_busy():
            self.parent.chan_2.play(self.sound_flower)
        self.kill()
