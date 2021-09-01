import sys
import time

from player import Player, Car, Bee
from common import TMazeCommon
import generator

import pygame
import pygame_gui
import argparse
import logging

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)


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
        self.image = pygame.Surface((self.parent.block_size, self.parent.block_size))
        self.wall = False
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.topleft = TMazeCommon.add_tuples(self.parent.maze_rect.topleft, pos)

    def draw(self):
        self.parent.screen.blit(self.image, self.rect)


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
    def __init__(self, use_joystick, is_full_screen, player_type_str):
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
            self.left_maze = 80
            self.top_maze = 0
            self.screen = pygame.display.set_mode((0, 0), flags=pygame.FULLSCREEN)
            pygame.display.toggle_fullscreen()
            pygame.init()
            self.maze_width = pygame.display.get_window_size()[0] - self.left_maze
            self.maze_height = pygame.display.get_window_size()[1] - 40
        else:
            self.left_maze = 0
            self.top_maze = 0
            self.maze_width = 800
            self.maze_height = 600
            self.screen = pygame.display.set_mode((self.maze_width, self.maze_height))
            pygame.init()

        self.maze_rect = pygame.Rect(self.left_maze, self.top_maze, self.maze_width, self.maze_height)
        self.logger.info("{}".format(self.maze_rect))
        pygame.mixer.set_num_channels(8)
        self.block_size = 25
        self.manager = pygame_gui.UIManager((self.maze_width, self.maze_height))
        self.chan_2 = pygame.mixer.Channel(2)
        self.font = pygame.font.SysFont('Impact', 20, italic=False, bold=True)
        if player_type_str == "bee":
            self.player = Bee(self)
        else:
            self.player = Car(self)
        self.joystick = None
        if use_joystick:
            self.init_joystick()

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

    def clear_map(self):
        self.tiles.clear()
        self.walls.clear()
        self.gen.clear()
        self.screen.fill(BLACK)

    def grid_to_screen(self, pos):
        x = pos[0] * self.block_size
        y = pos[1] * self.block_size
        return x, y

    def setup_map(self):
        self.gen.generate_maze()
        self.player.set_pos(self.grid_to_screen(self.gen.start))
        for i in range(self.gen.rows):
            for j in range(self.gen.cols):
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

    def start_game(self):
        self.screen.fill(BLACK)
        self.gen.rows = int(self.maze_height / self.block_size)
        self.gen.cols = int(self.maze_width / self.block_size)
        self.setup_map()
        self.render_map()
        self.rendered_map = self.screen.copy()
        self.logger.info("start_game")
        pygame.display.update()

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
            self.player.draw(self.screen)
            if self.is_paused:
                self.manager.draw_ui(self.screen)
            pygame.display.update([self.player.rect, self.maze_rect])
            clock.tick(25)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-joystick", dest='use_joystick', default=False, action="store_true")
    parser.add_argument("--fullscreen", dest='fullscreen', default=False, action="store_true")
    parser.add_argument("--player", dest='player', default="bee", help="can be car or bee (default)")
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    maze = TMaze(args.use_joystick, args.fullscreen, args.player)
    maze.main_loop()
    pygame.quit()
