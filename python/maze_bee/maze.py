import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.joystick import init_joystick
import utils.maze_generator as generator
from utils.logging_wrapper import setup_logging
from utils.colors import TColors
from bee import TBee
from tile import TTile
from flower import TFlower
from frog import TFrog


import random
import pygame
import argparse



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
    def __init__(self, use_joystick, is_full_screen, rooms_count, speed, block_size):
        self.logger = setup_logging("maze_logger")
        self.gen = generator.Generator(logger=self.logger, rooms=max(rooms_count, 2))
        self.tiles = []
        self.walls = []
        self.target_tiles = []
        self.text_surfaces = []
        self.score = 0
        self.is_running = True
        self.is_paused = False
        self.all_sprites = None
        self.objects = None
        self.print_victory = False
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
            self.maze_width = 1000
            self.maze_height = 800
            self.screen = pygame.display.set_mode((self.maze_width, self.maze_height))
            pygame.init()

        self.maze_rect = pygame.Rect(self.left_maze, self.top_maze, self.maze_width, self.maze_height)
        self.logger.info("{}".format(self.maze_rect))
        pygame.mixer.set_num_channels(8)
        self.block_size = block_size
        self.chan_2 = pygame.mixer.Channel(2)
        self.font = pygame.font.SysFont('Impact', 20, italic=False, bold=True)
        self.player = TBee(self, speed=speed, width=2, height=2)
        #self.shadow_player =
        self.joystick = None
        if use_joystick:
            self.joystick = init_joystick(self.logger)

    def clear_map(self):
        self.tiles.clear()
        self.walls.clear()
        self.screen.fill(TColors.black)

    def grid_to_screen(self, pos):
        x = pos[0] * self.block_size
        y = pos[1] * self.block_size
        return x, y

    def draw_rooms(self):
        self.tiles.clear()
        sprites_wo_tiles = list()
        for sprite in self.all_sprites:
            if not isinstance(sprite, TTile):
                sprites_wo_tiles.append(sprite)
        self.all_sprites.empty()

        for x in range(self.gen.grid_width):
            for y in range(self.gen.grid_height):
                tile_type = self.gen.grid[x][y]
                if tile_type != generator.WALKABLE_TILE:
                    tile = TTile(self, self.grid_to_screen((x, y)), tile_type)
                    self.tiles.append(tile)
                    self.all_sprites.add(tile)

        for s in sprites_wo_tiles:
            self.all_sprites.add(s)

        self.target_tiles = [t for t in self.tiles if t.tile_type == generator.TARGET_TILE]
        self.walls = [t for t in self.tiles if t.tile_type == generator.WALL_TILE]
        self.logger.info("walls count = {}".format(len(self.walls)))

    def open_closed_rooms(self):
        self.gen.open_closed_rooms()
        self.draw_rooms()

    def set_player_initial(self):
        pos = self.grid_to_screen(self.gen.start_pos)
        self.player.set_initial_position(pos)

    def set_player_sprites_to_groups(self):
        self.all_sprites.add(self.player)

    def handle_player_events(self, e):
        self.player.handle_event(e)

    def setup_map(self):
        self.gen.generate_maze(int(self.maze_width / self.block_size), int(self.maze_height / self.block_size))
        self.set_player_initial()
        self.all_sprites = pygame.sprite.Group()
        self.objects = pygame.sprite.Group()

        for x,y in self.gen.room_centers_except_start_room:
            flower = TFlower(self, self.grid_to_screen((x, y)))
            self.all_sprites.add(flower)
            self.objects.add(flower)
        if len(self.gen.room_corners_except_start_room) >  0:
            frog_place = random.choice(self.gen.room_corners_except_start_room)
            frog = TFrog(self, self.grid_to_screen(frog_place))
            self.all_sprites.add(frog)
            self.objects.add(frog)
        self.set_player_sprites_to_groups()
        self.draw_rooms()

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            pygame.mixer.music.stop()
        else:
            self.player.switch_sound = True

    def next_map(self):
        self.print_victory  = False
        self.clear_map()
        self.setup_map()
        self.set_player_initial()

    def start_game(self):
        self.screen.fill(TColors.black)
        self.setup_map()
        self.logger.info("start_game")
        pygame.display.flip()

    def check_game_events(self, event):
        if event.type == pygame.QUIT:
            self.player.stop_playing()
            self.is_running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.toggle_pause()
            if event.key == pygame.K_ESCAPE:
                self.is_running = False
            elif event.key == pygame.K_r:
                self.next_map()
            elif event.key == pygame.K_o:
                self.open_closed_rooms()

    def main_loop(self):
        self.start_game()
        clock = pygame.time.Clock()
        while self.is_running:
            joystick_direction = [0, 0]
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN:
                    self.logger.info("Joystick button pressed.")
                elif event.type == pygame.JOYBUTTONUP:
                    self.next_map()
                    self.logger.info("Joystick button released.")
                elif event.type == pygame.JOYAXISMOTION:
                    joystick_direction[event.axis] = int(event.value)
                    for e in TKeyEventType.from_joystick_event(event):
                        self.handle_player_events(e)
                else:
                   self.check_game_events(event)
                   self.handle_player_events(event)
                if joystick_direction[0] != 0 or joystick_direction[1] != 0:
                    self.logger.info("joystick_direction = {}".format(joystick_direction))

            self.screen.fill(TColors.white)
            self.all_sprites.update()
            self.all_sprites.draw(self.screen)

            if self.print_victory:
                self.screen.fill((0, 0, 255))
                font = pygame.font.SysFont(None, 300)
                screen_text = font.render('ПОБЕДА!', True, (0, 200, 0))
                self.screen.blit(screen_text, (250, 280))

            #   pygame.draw.rect(self.screen, TColors.black, self.player.rect, width=1)
            #pygame.draw.rect(self.screen, TColors.black, self.player.image.get_rect(), width=1)
            self.player.draw_shadow()
            pygame.display.flip()
            clock.tick(25)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-joystick", dest='use_joystick', default=False, action="store_true")
    parser.add_argument("--fullscreen", dest='fullscreen', default=False, action="store_true")
    parser.add_argument("--rooms-count", dest='rooms_count', default=2, type=int)
    parser.add_argument("--speed", dest='speed', default=2, type=int)
    parser.add_argument("--block-size", dest='block_size', default=25, type=int)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    maze = TMaze(args.use_joystick, args.fullscreen, args.rooms_count, args.speed, args.block_size)
    maze.main_loop()
    pygame.quit()
