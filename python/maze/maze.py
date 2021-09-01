import sys
import time

from player import Player, Car, Bee
from common import  TMazeCommon
import generator

import pygame
import pygame_gui
from enum import Enum
import argparse
import logging

'''
SPACE - Pause and Settings
ESC - Quit
R - New map
F - Enter Fullscreen
'''




BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
TEXT_COLOR = (120, 120, 120)


class Direction(Enum):
    UP = (0, -1)
    RIGHT = (1, 0)
    DOWN = (0, 1)
    LEFT = (-1, 0)


ColorMap = {
    generator.WALKABLE_TILE: WHITE,
    generator.WALL_TILE: RED,
    generator.START_TILE: BLUE,
    generator.TARGET_TILE: GREEN,
}


class Tile(pygame.sprite.Sprite):
    def __init__(self, parent, pos, tile_type=-1, color=BLACK):
        pygame.sprite.Sprite.__init__(self)
        self.parent = parent
        if tile_type in ColorMap:
            color = ColorMap[tile_type]
        self.tile_type = tile_type
        self.image = pygame.Surface((self.parent.BLOCK_SIZE, self.parent.BLOCK_SIZE))
        self.wall = False
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.center = TMazeCommon.add_tuples(self.parent.screen_rect.center, pos)

    def draw(self):
        self.parent.screen.blit(self.image, self.rect)


class AnotSlider():
    def __init__(self, parent, disp, text, start_value, value_range, func):
        self.parent = parent
        self.text = text
        self.func = func
        s_w = self.parent.screen_width / 2 + disp[0]
        s_h = self.parent.screen_height / 2 + disp[1]
        self.s = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect((s_w, s_h), (300, 30)),
                                                        start_value=start_value, value_range=value_range,
                                                        manager=parent.manager)
        self.s_button_rect = pygame.Rect((s_w - 200, s_h), (200, 30))
        self.s_button = pygame_gui.elements.UIButton(relative_rect=self.s_button_rect,
                                                     text=text + ': ' + str(self.s.current_value),
                                                     manager=parent.manager)

    def update(self):
        self.func(self.s.current_value)
        self.s_button.text = self.text + ': ' + str(self.s.current_value)
        self.s_button.rebuild()


def setup_logging():
    logger = logging.getLogger("maze_logger")
    logger.setLevel(logging.DEBUG)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh = logging.FileHandler("maze.log",  mode='w')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)

    return logger


class TKeyEventType:
    def __init__(self, type, key_code):
        self.type = type
        self.key = key_code
    @staticmethod
    def from_joystick_event(event):
        if event.axis == 0:
            if event.value > 0:
                yield TKeyEventType(pygame.KEYDOWN, pygame.K_RIGHT)
            elif event.value < 0:
                yield TKeyEventType(pygame.KEYDOWN, pygame.K_LEFT)
            else:
                yield TKeyEventType(pygame.KEYUP, pygame.K_LEFT)
                yield TKeyEventType(pygame.KEYUP, pygame.K_RIGHT)
        elif event.axis == 1:
            if event.value > 0:
                yield TKeyEventType(pygame.KEYDOWN, pygame.K_DOWN)
            elif event.value < 0:
                yield TKeyEventType(pygame.KEYDOWN, pygame.K_UP)
            else:
                yield TKeyEventType(pygame.KEYUP, pygame.K_DOWN)
                yield TKeyEventType(pygame.KEYUP, pygame.K_UP)


class TMaze:
    def __init__(self, use_joystick, is_full_screen):
        self.gen = generator.Generator()
        self.logger = setup_logging()
        self.rendered_map = None
        self.tiles = []
        self.walls = []
        self.target_tiles = []
        self.text_surfaces = []
        self.playable_types = Player.__subclasses__()
        self.playable_types_buttons = []
        self.score = 0
        self.is_running = True
        self.is_paused = False
        if is_full_screen:
            self.screen = pygame.display.set_mode((0, 0), flags=pygame.FULLSCREEN)
            pygame.display.toggle_fullscreen()
            self.screen_width = pygame.display.get_window_size()[0]
            self.screen_height = pygame.display.get_window_size()[1]
            self.screen_rect = self.screen.get_rect()
            self.logger.info("{}".format(self.screen_rect))
        else:
            self.screen_width = 800
            self.screen_height = 600
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
            self.screen_rect = self.screen.get_rect()
        pygame.init()
        pygame.mixer.set_num_channels(8)
        self.BLOCK_SIZE = 25
        self.manager = pygame_gui.UIManager((self.screen_width, self.screen_height))
        self.chan_2 = pygame.mixer.Channel(2)
        self.font = pygame.font.SysFont('Impact', 20, italic=False, bold=True)
        self.player = Bee(self)
        self.joystick = None
        if use_joystick:
            self.init_joystick()

        self.settings_sliders = self.init_settings_sliders()


    def init_joystick(self):
        pygame.joystick.init()
        self.logger.info("joysticks count = {}".format(pygame.joystick.get_count()))
        if not pygame.joystick.get_init() or pygame.joystick.get_count() < 1:
            self.logger.error("cannot find joystick")
            return
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        if not self.joystick.get_init():
            self.joystick = None
            self.logger.error("cannot init joystick")
            return
        self.logger.info("joystick name = {}".format(self.joystick.get_name()))
        self.logger.info("joystick axes count = {}".format(self.joystick.get_numaxes()))
        self.logger.info("joystick get_numballs = {}".format(self.joystick.get_numballs()))
        self.logger.info("joystick get_numbuttons = {}".format(self.joystick.get_numbuttons()))

    def init_settings_sliders(self):
        return [
            AnotSlider(self, disp=(-100, -150), text='Min Rooms', start_value=self.gen.min_rooms, value_range=(1, 100),
                       func=self.set_min_rooms),
            AnotSlider(self, disp=(-100, -110), text='Max Rooms', start_value=self.gen.max_rooms, value_range=(1, 100),
                       func=self.set_max_rooms),
            AnotSlider(self, disp=(-100, -70), text='Min Room Connections', start_value=self.gen.min_room_connections,
                       value_range=(1, 20), func=self.set_min_room_conn),
            AnotSlider(self, disp=(-100, -30), text='Max Room Size', start_value=self.gen.max_room_size, value_range=(1, 500),
                       func=self.set_max_room_conn),
            AnotSlider(self, disp=(-100, 10), text='Redundant Connections', start_value=int(self.gen.allow_redundant_connections),
                       value_range=(0, 1), func=self.set_redundant_conn),
            AnotSlider(self, disp=(-100, 50), text='Distance To Target', start_value=self.gen.distance_to_target,
                       value_range=(0, 100), func=self.set_distant_to_target),
            AnotSlider(self,disp=(-100, 90), text='Path Width', start_value=self.gen.path_width, value_range=(1, 20),
                       func=self.set_path_width),
            AnotSlider(self, disp=(-100, 130), text='Map Width', start_value=self.gen.cols, value_range=(1, 500),
                       func=self.set_map_width),
            AnotSlider(self, disp=(-100, 170), text='Map Height', start_value=self.gen.rows, value_range=(1, 500),
                       func=self.set_map_height),
            AnotSlider(self, disp=(-100, 210), text='Player Size', start_value=self.player.size, value_range=(1, 10),
                       func=self.set_player_size),
            AnotSlider(self, disp=(-100, 250), text='Player Max Speed', start_value=self.player.max_speed, value_range=(1, 50),
                       func=self.set_player_max_speed),
            AnotSlider(self, disp=(-100, 290), text='Block Size', start_value=self.BLOCK_SIZE, value_range=(1, 100),
                       func=self.set_block_size)
        ]

    def clear_map(self):
        self.tiles.clear()
        self.walls.clear()
        self.gen.clear()
        self.screen.fill(BLACK)

    def grid_to_screen(self, pos):
        t = (pos[0] * self.BLOCK_SIZE - len(self.gen.grid[0]) * self.BLOCK_SIZE / 2 - 10,
             pos[1] * self.BLOCK_SIZE - len(self.gen.grid) * self.BLOCK_SIZE / 2 - 10)
        return t

    def setup_map(self):
        self.gen.generate_maze()
        self.player.set_pos(self.grid_to_screen(self.gen.start))
        for i in range(len(self.gen.grid)):
            for j in range(len(self.gen.grid[0])):
                self.tiles.append(Tile(self, self.grid_to_screen((j, i)), self.gen.grid[i][j]))
        self.walls = [t.rect for t in self.tiles if t.tile_type == generator.WALL_TILE]
        self.target_tiles = [t for t in self.tiles if t.tile_type == generator.TARGET_TILE]

    def render_map(self):
        for t in self.tiles:
            t.draw()

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            pygame.mixer.music.stop()
        else:
            self.player.switch_sound = True

    def next_map(self):
        self.clear_map()
        self.setup_map()
        self.render_map()
        self.rendered_map = self.screen.copy()
        self.player.set_pos(self.grid_to_screen(self.gen.start))

    def update_text_surface(self, text=None):
        if text is not None:
            texts = text.splitlines()
            self.text_surfaces = [None] * len(texts)
            for i, t in enumerate(texts):
                self.text_surfaces[i] = self.font.render(t, False, TEXT_COLOR)
                self.screen.blit(self.text_surfaces[i], (self.screen_width - self.font.size(t)[1] * 10 - 50,
                                                         self.screen_height - 1000 + self.font.size(t)[1] * i))

    def arrange_buttons(self):
        s_w = self.screen_width / 2
        s_h = self.screen_height / 2
        button_width = 500 / len(self.playable_types)
        for i, x in enumerate(self.playable_types):
            pos = (s_w - 300 + button_width * i, s_h - 400)
            self.playable_types_buttons.append(
                pygame_gui.elements.UIButton(relative_rect=pygame.Rect(pos, (button_width, 200)), text=x.__name__,
                                             manager=self.manager))

    def start_game(self):
        self.screen.fill(BLACK)
        self.gen.rows = int(self.screen_height / self.BLOCK_SIZE)
        self.gen.cols = int(self.screen_width / self.BLOCK_SIZE)
        self.setup_map()
        self.render_map()
        self.rendered_map = self.screen.copy()
        self.arrange_buttons()
        self.logger.info("start_game")
        pygame.display.update()

    def set_min_rooms(self, x):
        self.gen.min_rooms = x

    def set_max_rooms(self, x):
        self.gen.max_rooms = x

    def set_min_room_conn(self, x):
        self.gen.min_room_connections = x

    def set_max_room_conn(self, x):
        self.gen.max_room_size = x

    def set_redundant_conn(self, x):
        self.gen.allow_redundant_connections = bool(x)

    def set_distant_to_target(self, x):
        self.gen.distance_to_target = x

    def set_path_width(self, x):
        self.gen.path_width = x

    def set_map_width(self, x):
        self.gen.cols = x

    def set_map_height(self, x):
        self.gen.rows = x

    def set_player_size(self, x):
        self.player.set_scale(x)

    def set_player_max_speed(self, x):
        self.player.max_speed = x

    def set_block_size(self, x):
        self.BLOCK_SIZE = x

    def check_game_events(self, event):
        if event.type == pygame.QUIT:
            self.is_running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.toggle_pause()
            if event.key == pygame.K_ESCAPE:
                self.is_running = False
            elif event.key == pygame.K_r:
                self.next_map()

        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element in self.playable_types_buttons:
                    self.player = self.playable_types[self.playable_types_buttons.index(event.ui_element)]()
                    self.player.set_pos(self.grid_to_screen(self.gen.target_room_source))
            elif event.user_type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                settings = self.settings_sliders
                [s for s in settings if s.s == event.ui_element][0].update()
                if event.ui_element == settings[0].s:
                    if settings[0].s.current_value >= settings[1].s.current_value:
                        settings[1].s.current_value = settings[0].s.current_value
                        settings[1].s.rebuild()
                        settings[1].update()
                elif event.ui_element == settings[1].s:
                    if settings[1].s.current_value <= settings[0].s.current_value:
                        settings[0].s.current_value = settings[1].s.current_value
                        settings[0].s.rebuild()
                        settings[0].update()
                if settings[5].s.current_value == 0:
                    settings[5].s_button.text = settings[5].text + ': Rand'
                    settings[5].s_button.rebuild()
                elif settings[5].s.current_value == 100:
                    settings[5].s_button.text = settings[5].text + ': Max'
                    settings[5].s_button.rebuild()

    def main_loop(self):
        self.start_game()
        clock = pygame.time.Clock()
        while self.is_running:
            time_delta = clock.tick(120) / 1000.0
            joystick_direction = [0, 0]
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN:
                    self.logger.info("Joystick button pressed.")
                elif event.type == pygame.JOYBUTTONUP:
                    self.logger.info("Joystick button released.")
                elif event.type == pygame.JOYAXISMOTION:
                    #axis = ['X', 'Y']
                    #self.logger.info("joystick: {}, movement: {} in the {}-axis".format(event.joy, event.value, axis[event.axis]))
                    joystick_direction[event.axis] = int(event.value)
                    for e in TKeyEventType.from_joystick_event(event):
                        #self.logger.info("key={}, type={}".format(e.key, e.type))
                        self.player.handle_event(e)
                else:
                   self.check_game_events(event)
                if not self.is_paused:
                   self.player.handle_event(event)
                if self.is_paused:
                   self.manager.process_events(event)
                if joystick_direction[0] != 0 or joystick_direction[1] != 0:
                    self.logger.info("joystick_direction = {}".format(joystick_direction))

            self.manager.update(time_delta)
            self.player.update()
            self.screen.blit(self.rendered_map, (0, 0))
            self.update_text_surface(f'MazeGame    |    Score:   {self.player.score} \n\n'
                                f'R - New Level\n'
                                f'F - Fullscreen\n'
                                f'SPACE - Pause')
            self.player.draw(self.screen)
            if self.is_paused:
                self.manager.draw_ui(self.screen)
            pygame.display.update([self.player.rect, self.screen_rect])
            clock.tick(25)
            #time.sleep(1)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-joystick", dest='use_joystick', default=False, action="store_true")
    parser.add_argument("--fullscreen", dest='fullscreen', default=False, action="store_true")
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    maze = TMaze(args.use_joystick, args.fullscreen)
    maze.main_loop()
    pygame.quit()
