import pygame
import os
import random


class TSprite(pygame.sprite.Sprite):
    SPRITES_DIR = os.path.join(os.path.dirname(__file__), "assets", 'sprites')

    def __init__(self, parent, image_file_name, rect):
        super().__init__()
        self.parent = parent
        self.rect = rect
        img = pygame.image.load(os.path.join(TSprite.SPRITES_DIR, image_file_name))
        self.image = pygame.transform.scale(img, (rect.width, rect.height))

        self.angle = 0
        self.speed_modifier = 1.0

        self.retreat_after_crash = False
        self.sound = None
        self.sound_volume = 0

    def change_spite_position(self, speed):
        self.rect.top += self.speed_modifier * speed


class TRiver(TSprite):
    def __init__(self, parent, top=0, left=0):
        super().__init__(parent,
                         'river.png',
                         pygame.Rect(0, top, parent.get_width(), 160))
        self.collided = False


class TBridge(TSprite):
    def __init__(self, parent, top=0, left=0, width=300):
        super().__init__(parent,
                         'bridge.png',
                         pygame.Rect(0, top, width, 200))
        self.used = False


class TRiverAndBridge:
    def __init__(self, parent, top, bridge_width):
        self.bridge_width = bridge_width
        self.river = TRiver(parent, top=top)
        self.bridge = TBridge(parent, top=top, width=self.bridge_width)
        self.bridge.rect.top = top
        self.bridge.rect.left = random.randrange(0, parent.get_width() - self.bridge_width)

    def destroy_sprites(self):
        self.river.kill()
        self.river = None
        self.bridge.kill()
        self.bridge = None

    def change_spite_position(self, delta):
        self.river.change_spite_position(delta)
        self.bridge.change_spite_position(delta)


class TMyCar(TSprite):
    def __init__(self, parent, image_file_name, horizontal_speed=10):
        car_width = 160
        car_height = 160
        if image_file_name.startswith('truck'):
            car_height = 200
        rct = pygame.Rect(0, 0, car_width, car_height)
        super().__init__(parent, image_file_name, rct)
        self.horizontal_speed = horizontal_speed
        self.horizontal_speed_increase_with_get_speed = True
