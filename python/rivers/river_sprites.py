from draw_road import draw_road
from utils.colors import TColors

import pygame
import os
import random


class TSprite(pygame.sprite.Sprite):
    SPRITES_DIR = os.path.join(os.path.dirname(__file__), "assets", 'sprites')
    BACKGROUND_COLOR = TColors.gray

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
    def __init__(self, parent, left, top):
        super().__init__(parent,
                         'river.png',
                         pygame.Rect(left, top, parent.get_width(), 160))
        self.collided = False


class TBridge(TSprite):
    def __init__(self, parent, left, top, width=300):
        super().__init__(parent,
                         'bridge.png',
                         pygame.Rect(left, top, width, 200))
        self.used = False


class TRoadSprite(TSprite):
    def __init__(self, parent, start_point, end_point, road_width=30):
        x1, y1 = start_point[0], start_point[1]
        x2, y2 = end_point[0], end_point[1]
        rct = pygame.Rect(min(x1, x2), y1, abs(x2-x1)+road_width, y2-y1)
        srf = pygame.Surface((rct.width, rct.height))
        srf.fill(TSprite.BACKGROUND_COLOR)
        #pygame.draw.rect(srf, TColors.white,   min(x1, x2) + abs(x1-x2)/2  pygame.Rect(1,1, rct.width-2, rct.top-2), width=1 )
        draw_road(srf, x1-rct.left, y1-rct.top, x2-rct.left, y2-rct.top, width=road_width)
        self.town_position = (min(x1, x2) + abs(x1 - x2)/2, min(y1, y2) + abs(y1 - y2)/2)
        self.granny_position = (self.town_position[0] + 50,  self.town_position[1] - 75)
        super().__init__(parent, None, rct, surface=srf)


class TTownColor:
    def __init__(self, color=None, minus_color=None):
        if color is None:
            colors = [TColors.red, TColors.green, TColors.blue]
            if minus_color is not None:
                colors.remove(minus_color)
            self.color = random.choice(colors)
            #self.color = random.choice([TColors.red])
        else:
            self.color = color

    def get_color_id(self):
        if self.color == TColors.red:
            return 1
        if self.color == TColors.green:
            return 2
        if self.color == TColors.blue:
            return 3
        raise Exception("unk color {}".format(c))

    def get_color_str(self):
        if self.color == TColors.red:
            return "red"
        if self.color == TColors.green:
            return "green"
        if self.color == TColors.blue:
            return "blue"
        raise Exception("unk color {}".format(c))


class TGrannySprite(TSprite):
    GRANNY_WIDTH = 150

    def __init__(self, parent, left, top, width=None, color=None, minus_color=None):
        self.river_fall_count = 0
        self.color = TTownColor(color, minus_color)
        if width is None:
            width = TGrannySprite.GRANNY_WIDTH
        fname = "granny{}.png".format(self.color.get_color_id())
        super().__init__(parent,
                         fname,
                         pygame.Rect(left, top, width, width),
                         )
        self.collided = False


class TTownSprite(TSprite):
    def __init__(self, parent, left, top, width=300, replicate_width=3):
        self.color = TTownColor()
        fname = "town{}.png".format(self.color.get_color_id())
        img = pygame.image.load(os.path.join(TSprite.SPRITES_DIR, fname))
        img = pygame.transform.scale(img, (width, width))
        srf = pygame.Surface((width*replicate_width, width))
        srf.fill(TSprite.BACKGROUND_COLOR)
        for i in range(replicate_width):
            srf.blit(img, (i*width, 0))

        super().__init__(parent,
                         None,
                         pygame.Rect(left-srf.get_width()/2, top-width/2, srf.get_width(), srf.get_height()),
                         surface=srf
                         )
        self.collided = False


class TMapPart:
    def __init__(self, parent, top, bridge_width, road_width, prev_bridge_rect, generate_granny: bool):
        self.bridge_width = bridge_width
        self.road_width = road_width
        self.river = TRiver(parent, 0, top)
        self.bridge = TBridge(parent, 0, top, width=self.bridge_width)
        self.bridge.rect.top = top
        self.bridge.rect.left = random.randrange(0, parent.get_width() - self.bridge_width)
        anchor1 = (self.bridge.rect.left + bridge_width/2 - road_width, self.bridge.rect.bottom)
        anchor2 = (prev_bridge_rect.left + bridge_width / 2 - road_width, prev_bridge_rect.top)
        self.road = TRoadSprite(parent, anchor1, anchor2)
        self.town = TTownSprite(parent, self.road.town_position[0], self.road.town_position[1])
        self.grannies = list()
        if generate_granny:
            self.generate_granny(minus_color=self.town.color.color)

    def destroy_sprites(self):
        self.river.kill()
        self.river = None
        self.bridge.kill()
        self.bridge = None
        self.road.kill()
        self.road = None
        self.town.kill()
        self.town = None
        self.kill_grannies()

    def change_spite_position(self, delta):
        self.river.change_spite_position(delta)
        self.bridge.change_spite_position(delta)
        self.road.change_spite_position(delta)
        self.town.change_spite_position(delta)
        for g in self.grannies:
            g.change_spite_position(delta)

    def has_grannies(self):
        return len(self.grannies) > 0

    def kill_grannies(self):
        for g in self.grannies:
            g.kill()
        self.grannies = list()

    def add_grannies_to_group(self, grp):
        for g in self.grannies:
            grp.add(g)

    def generate_granny(self, color=None, minus_color=None):
        if self.town.rect.left < self.town.parent.get_width() / 2:
            x = self.town.rect.left + self.town.rect.width + len(self.grannies)*20
        else:
            x = self.town.rect.left - self.town.rect.width + len(self.grannies) * 20

        g = TGrannySprite(self.road.parent, x, self.town.rect.top, color=color, minus_color=minus_color)
        self.grannies.append(g)

    def get_descr(self):
        message = "town color: {}".format(self.town.color.get_color_str())
        if len(self.grannies) > 0:
            message += ", granny color: {}".format(self.grannies[0].color.get_color_str())
        return message

class TMyCar(TSprite):
    def __init__(self, parent, image_file_name, horizontal_speed=10):
        car_width = 160
        car_height = 160
        if image_file_name.startswith('truck') or image_file_name.startswith('bus'):
            car_height = 200
        rct = pygame.Rect(0, 0, car_width, car_height)
        super().__init__(parent, image_file_name, rct)
        self.horizontal_speed = horizontal_speed
        self.horizontal_speed_increase_with_get_speed = True


