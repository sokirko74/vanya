from draw_road import draw_road
from utils.colors import TColors

import pygame
import os
import random
import math

class TSprite(pygame.sprite.Sprite):
    SPRITES_DIR = os.path.join(os.path.dirname(__file__), "assets", 'sprites')

    def __init__(self, parent, image_file_name, rect, surface=None):
        super().__init__()
        self.parent = parent
        self.rect = rect
        if image_file_name is not None:
            img = pygame.image.load(os.path.join(TSprite.SPRITES_DIR, image_file_name))
            self.image = pygame.transform.scale(img, (rect.width, rect.height))
        else:
            assert surface is not None
            self.image = surface

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


class TRoadSprite(TSprite):
    def __init__(self, parent, start_point, end_point, road_width=30):
        x1, y1 = start_point[0], start_point[1]
        x2, y2 = end_point[0], end_point[1]
        rct = pygame.Rect(min(x1, x2), y1, abs(x2-x1)+road_width, y2-y1)
        srf = pygame.Surface((rct.width, rct.height))
        srf.fill(TColors.gray)
        #pygame.draw.rect(srf, TColors.white,     pygame.Rect(1,1, rct.width-2, rct.top-2), width=1 )
        draw_road(srf, x1-rct.left, y1-rct.top, x2-rct.left, y2-rct.top, width=road_width)
        super().__init__(parent, None, rct, surface=srf)


class TRiverGroup:
    def __init__(self,   parent, top, bridge_width, road_width, prev_bridge_rect):
        self.bridge_width = bridge_width
        self.road_width = road_width
        self.river = TRiver(parent, top=top)
        self.bridge = TBridge(parent, top=top, width=self.bridge_width)
        self.bridge.rect.top = top
        self.bridge.rect.left = random.randrange(0, parent.get_width() - self.bridge_width)
        anchor1 = (self.bridge.rect.left + bridge_width/2 - road_width, self.bridge.rect.bottom)
        anchor2 = (prev_bridge_rect.left + bridge_width / 2 - road_width, prev_bridge_rect.top)
        self.road = TRoadSprite(parent, anchor1, anchor2)

    def destroy_sprites(self):
        self.river.kill()
        self.river = None
        self.bridge.kill()
        self.bridge = None
        self.road.kill()
        self.road = None

    def change_spite_position(self, delta):
        self.river.change_spite_position(delta)
        self.bridge.change_spite_position(delta)
        self.road.change_spite_position(delta)


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


