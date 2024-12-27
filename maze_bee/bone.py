import pygame
import random
import os


class TBone(pygame.sprite.Sprite):
    sprites = [
        ('bone.png', 'bone.wav'),
    ]

    def __init__(self, parent, pos):
        pygame.sprite.Sprite.__init__(self)
        self.parent = parent
        sprite_basename, sound_basename = random.choice(self.sprites)
        self.image = pygame.image.load(os.path.join('assets', 'sprites', sprite_basename))
        self.sound = pygame.mixer.Sound(os.path.join('assets', 'sounds', sound_basename))
        self.sound.set_volume(0.2)
        self.image = pygame.transform.scale(self.image, (80, 80))
        self.rect = self.image.get_rect()
        self.rect.topleft = pygame.math.Vector2(self.parent.maze_rect.topleft) + pos
        self.contacted = False

    def contact_object(self):
        if not self.parent.player.is_loaded():
            if not self.parent.chan_2.get_busy():
                self.parent.chan_2.play(self.sound)
            self.kill()
            self.parent.player.load_bone()
