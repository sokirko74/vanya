import json

from draw_road import draw_road
from utils.colors import TColors

import pygame
import os
import random


class TSprite(pygame.sprite.Sprite):
    SPRITES_DIR = os.path.join(os.path.dirname(__file__), "assets", 'sprites')
    BACKGROUND_COLOR = TColors.gray

    def __init__(self, screen, image_file_name, rect, surface=None):
        super().__init__()
        self.screen = screen
        self.river_fall_count = 0
        self.rect = rect
        self.file_name = image_file_name
        if image_file_name is not None:
            if not os.path.isabs(image_file_name):
                image_file_name = os.path.join(TSprite.SPRITES_DIR, image_file_name)
            img = pygame.image.load(os.path.join(TSprite.SPRITES_DIR, image_file_name))
            self.image = pygame.transform.scale(img, (rect.width, rect.height))
        else:
            assert surface is not None
            self.image = surface


    def change_spite_position(self, speed):
        self.rect.top += speed


class TRiver(TSprite):
    def __init__(self, screen, left, top):
        super().__init__(screen,
                         'river.png',
                         pygame.Rect(left, top, screen.get_width(), 160))
        self.collided = False


class TBridge(TSprite):
    def __init__(self, screen, left, top, width=300):
        super().__init__(screen,
                         'bridge.png',
                         pygame.Rect(left, top, width, 200))
        self.used = False


class TRoadSprite(TSprite):
    def __init__(self, screen, start_point, end_point, road_width=30):
        x1, y1 = start_point[0], start_point[1]
        x2, y2 = end_point[0], end_point[1]
        rct = pygame.Rect(min(x1, x2), y1, abs(x2-x1)+road_width, y2-y1)
        srf = pygame.Surface((rct.width, rct.height))
        srf.fill(TSprite.BACKGROUND_COLOR)
        #pygame.draw.rect(srf, TColors.white,   min(x1, x2) + abs(x1-x2)/2  pygame.Rect(1,1, rct.width-2, rct.top-2), width=1 )
        draw_road(srf, x1-rct.left, y1-rct.top, x2-rct.left, y2-rct.top, width=road_width)
        self.car_stop_position = (min(x1, x2) + abs(x1 - x2) / 2, min(y1, y2) + abs(y1 - y2) / 2)
        self.granny_position = (self.car_stop_position[0] + 50, self.car_stop_position[1] - 75)
        super().__init__(screen, None, rct, surface=srf)


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
        raise Exception("unk color {}".format(self.color))

    def get_color_str(self):
        if self.color == TColors.red:
            return "red"
        if self.color == TColors.green:
            return "green"
        if self.color == TColors.blue:
            return "blue"
        raise Exception("unk color {}".format(self.color))


class TGrannySprite(TSprite):
    GRANNY_WIDTH = 150

    def __init__(self, screen, left, top, width=None, color=None, minus_color=None):

        self.color = TTownColor(color, minus_color)
        if width is None:
            width = TGrannySprite.GRANNY_WIDTH
        fname = "granny{}.png".format(self.color.get_color_id())
        super().__init__(screen,
                         fname,
                         pygame.Rect(left, top, width, width),
                         )
        self.collided = False

    def get_description(self):
        return self.color.get_color_str() + " granny"


class TGirlSprite(TSprite):
    GIRL_WIDTH = 150

    def __init__(self, screen, left, top, width=None):
        if width is None:
            width = TGirlSprite.GIRL_WIDTH
        fname = "girl.png"
        super().__init__(screen,
                         fname,
                         pygame.Rect(left, top, width, width),
                         )
        self.collided = False
    def get_description(self):
        return "girl"


class TRobberSprite(TSprite):
    _WIDTH = 150

    def __init__(self, screen, left, top, width=None):
        if width is None:
            width = TRobberSprite._WIDTH
        fname = "robber.png"
        super().__init__(screen,
                         fname,
                         pygame.Rect(left, top, width, width),
                         )
        self.collided = False

    def get_description(self):
        return "robber"


class TTownSprite(TSprite):
    def __init__(self, screen, left, top, width=300, replicate_width=3):
        self.color = TTownColor()
        fname = "town{}.png".format(self.color.get_color_id())
        img = pygame.image.load(os.path.join(TSprite.SPRITES_DIR, fname))
        img = pygame.transform.scale(img, (width, width))
        srf = pygame.Surface((width*replicate_width, width))
        srf.fill(TSprite.BACKGROUND_COLOR)
        for i in range(replicate_width):
            srf.blit(img, (i*width, 0))

        super().__init__(screen,
                         None,
                         pygame.Rect(left-srf.get_width()/2, top-width/2, srf.get_width(), srf.get_height()),
                         surface=srf
                         )
        self.collided = False
        self.traveller = None


class TStation(TSprite):
    def __init__(self, screen, left, top, image_file_name, width=300, replicate_width=1):
        img = pygame.image.load(os.path.join(TSprite.SPRITES_DIR, image_file_name))
        img = pygame.transform.scale(img, (width, width))
        srf = pygame.Surface((width*replicate_width, width))
        srf.fill(TSprite.BACKGROUND_COLOR)
        for i in range(replicate_width):
            srf.blit(img, (i*width, 0))
        super().__init__(screen,
                         None,
                         pygame.Rect(left-srf.get_width()/2, top-width/2, srf.get_width(), srf.get_height()),
                         surface=srf
                         )
        self.collided = False


class TBank(TSprite):
    def __init__(self, screen, left, top):
        width = 300
        height = 300
        img = pygame.image.load(os.path.join(TSprite.SPRITES_DIR, "bank.png"))
        img = pygame.transform.scale(img, (width, height))
        srf = pygame.Surface((width, height))
        srf.fill(TSprite.BACKGROUND_COLOR)
        srf.blit(img, (0, 0))
        super().__init__(screen,
                         None,
                         pygame.Rect(left-srf.get_width()/2, top-width/2, srf.get_width(), srf.get_height()),
                         surface=srf
                         )
        self.collided = False


class TRepairStation(TStation):
    def __init__(self, screen, left, top, width=300, replicate_width=1):
        super().__init__(screen, left, top, "repair.png", width=width, replicate_width=replicate_width)


class THospital(TStation):
    def __init__(self, screen, left, top, width=300, replicate_width=1):
        super().__init__(screen, left, top, "hospital.png", width=width, replicate_width=replicate_width)


class TGasStation(TStation):
    def __init__(self, screen, left, top, width=300, replicate_width=1):
        super().__init__(screen, left, top, "gas_station.png", width=width, replicate_width=replicate_width)


class TMapPart:
    def __init__(self, screen, top, bridge_width, road_width, prev_bridge_rect, girl_probability):
        self.screen = screen
        self.girl_probability = girl_probability
        self.bridge_width = bridge_width
        self.road_width = road_width
        self.river = TRiver(screen, 0, top)
        self.bridge = TBridge(screen, 0, top, width=self.bridge_width)
        self.bridge.rect.top = top
        self.bridge.rect.left = random.randrange(0, screen.get_width() - self.bridge_width)
        anchor1 = (self.bridge.rect.left + bridge_width/2 - road_width, self.bridge.rect.bottom)
        anchor2 = (prev_bridge_rect.left + bridge_width / 2 - road_width, prev_bridge_rect.top)
        self.road = TRoadSprite(screen, anchor1, anchor2)
        self.car_stop = None
        self.passengers = list()

    def generate_town(self, generate_passenger: bool, bank_prob):
        if random.random() < bank_prob:
            self.generate_bank()
        else:
            self.car_stop = TTownSprite(self.screen, self.road.car_stop_position[0], self.road.car_stop_position[1])
            if generate_passenger:
                p = self._generate_passenger(minus_color=self.car_stop.color.color)
                self.car_stop.traveller = p

    def generate_bank(self):
        self.car_stop = TBank(self.screen, self.road.car_stop_position[0], self.road.car_stop_position[1])
        left, top = self._get_passenger_position_at_car_stop()
        g = TRobberSprite(self.road.screen, left, top)
        self.passengers.append(g)

    def generate_repair_station(self):
        self.car_stop = TRepairStation(self.screen, self.road.car_stop_position[0], self.road.car_stop_position[1])

    def generate_gas_station(self):
        self.car_stop = TGasStation(self.screen, self.road.car_stop_position[0], self.road.car_stop_position[1])

    def generate_hospital(self):
        self.car_stop = THospital(self.screen, self.road.car_stop_position[0], self.road.car_stop_position[1])

    def destroy_sprites(self):
        self.river.kill()
        self.river = None
        self.bridge.kill()
        self.bridge = None
        self.road.kill()
        self.road = None
        self.car_stop.kill()
        self.car_stop = None
        self.kill_passengers()

    def change_spite_position(self, delta):
        self.river.change_spite_position(delta)
        self.bridge.change_spite_position(delta)
        self.road.change_spite_position(delta)
        self.car_stop.change_spite_position(delta)
        for g in self.passengers:
            g.change_spite_position(delta)

    def has_passengers(self):
        return len(self.passengers) > 0

    def kill_passengers(self):
        for g in self.passengers:
            g.kill()
        self.passengers = list()

    def add_passengers_to_sprite_group(self, grp: pygame.sprite.Group):
        for g in self.passengers:
            grp.add(g)

    def _get_passenger_position_at_car_stop(self):
        if self.car_stop.rect.left < self.car_stop.screen.get_width() / 2:
            x = self.car_stop.rect.left + self.car_stop.rect.width + len(self.passengers) * 20
        else:
            x = self.car_stop.rect.left - self.car_stop.rect.width + len(self.passengers) * 20
        return x, self.car_stop.rect.top

    def _generate_passenger(self, color=None, minus_color=None):
        left, top = self._get_passenger_position_at_car_stop()
        if random.random() < self.girl_probability:
            g = TGirlSprite(self.road.screen, left, top)
        else:
            g = TGrannySprite(self.road.screen, left, top, color=color, minus_color=minus_color)
        self.passengers.append(g)
        return g

    def passenger_goes_to_car_stop(self, passenger: TSprite):
        passenger.screen = self.road.screen
        self.passengers.append(passenger)
        left, top = self._get_passenger_position_at_car_stop()
        passenger.rect.left = left
        passenger.rect.top = top

    def get_descr(self):
        if  isinstance(self.car_stop, TTownSprite):
            message = "a {} town ".format(self.car_stop.color.get_color_str())
            if len(self.passengers) > 0:
                message += " with a " + self.passengers[0].get_description()
            return message
        elif isinstance(self.car_stop, TGasStation):
            return "Gas station"
        elif isinstance(self.car_stop, TRepairStation):
            return "Repair station"
        elif isinstance(self.car_stop, THospital):
            return "Hospital"
        else:
            return "unknown object"


class TCarSprite(TSprite):
    def __init__(self, screen, image_folder):
        if not os.path.exists(image_folder):
            image_folder = os.path.join(os.path.dirname(__file__), image_folder)
        info_path = os.path.join(image_folder, "info.json")
        with open(info_path) as inp:
            info = json.load(inp)
        car_width = info['width']
        car_height = info['height']
        image_file_name = os.path.abspath(os.path.join(image_folder, "body.png"))
        rct = pygame.Rect(0, 0, car_width, car_height)
        super().__init__(screen, image_file_name, rct)


class TRiverSprites:
    def __init__(self):
        self.rivers = pygame.sprite.Group()
        self.bridges = pygame.sprite.Group()
        self.roads = pygame.sprite.Group()
        self.towns = pygame.sprite.Group()
        self.passengers_at_car_stop = pygame.sprite.Group()
        self.passengers_in_car = pygame.sprite.Group()

    def clear_groups(self):
        self.rivers.empty()
        self.bridges.empty()
        self.roads.empty()
        self.towns.empty()
        self.passengers_at_car_stop.empty()
        self.passengers_in_car.empty()

    def redraw_without_cars(self, screen):
        self.rivers.draw(screen)
        self.roads.draw(screen)
        self.bridges.draw(screen)
        self.towns.draw(screen)
        self.passengers_at_car_stop.draw(screen)
        self.passengers_in_car.draw(screen)

