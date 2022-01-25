# this game was not released yet
from utils.joystick import init_joystick
import utils.maze_generator as generator
from utils.maze_player import MazePlayer
from utils.logging_wrapper import setup_logging

import pygame
import argparse
import logging
from pygame.math import Vector2
import os
import random


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)


class Car(MazePlayer):
    def __init__(self, parent, speed=4):
        super().__init__(parent,
                         image=pygame.image.load(os.path.join('assets', 'sprites', 'truck.png')),
                         height=3,
                         width=2,
                         max_speed=speed,
                         sound_moving=os.path.join('assets', 'sounds', 'truck_driving.wav'),
                         sound_crash=os.path.join('assets', 'sounds', 'truck_crash.wav'))

        self.sound_idle = os.path.join('assets', 'sounds', 'truck.wav')
        self.switch_sound = False
        pygame.mixer.music.load(self.sound_idle)
        pygame.mixer.music.play(-1, fade_ms=2000)
        self.move_direction = 0  # 1 forward, -1 backward
        self.steering_wheel_angle = 0

    def update(self):
        if self.switch_sound:
            pygame.mixer.music.stop()
            if self.move_direction == 0:
                pygame.mixer.music.load(self.sound_idle)
            else:
                pygame.mixer.music.load(self.sound_moving)
            pygame.mixer.music.play(-1, fade_ms=300)
            self.switch_sound = False

        if self.move_direction == 0:
            return
        save_angle = self.angle
        save_rect = self.rect.copy()
        save_image = self.image

        if self.steering_wheel_angle != 0:
            radius = 100 * self.move_direction
            angle_delta = 0 if self.steering_wheel_angle > 0 else 180
            pivot_point = self.rect.center - unit_vector(self.angle + angle_delta, radius)
            self.angle += self.steering_wheel_angle
            new_center = pivot_point + unit_vector(self.angle + angle_delta, radius)
            self.image = pygame.transform.rotate(self.orig_image, -self.angle)
            self.rect = self.image.get_rect(center=new_center)
        else:
            self.rect.center = Vector2(self.rect.center) + \
                               unit_vector(self.angle + 90, self.max_speed) * self.move_direction

        if not self.check_all_collisions():
            self.rect = save_rect
            self.image = save_image
            self.angle = save_angle

    def set_scale(self, scale):
        super().set_scale(scale)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.steering_wheel_angle = -3
            elif event.key == pygame.K_RIGHT:
                self.steering_wheel_angle = +3
            elif event.key == pygame.K_UP:
                self.move_direction = 1
                self.switch_sound = True
            elif event.key == pygame.K_DOWN:
                self.move_direction = -1
                self.switch_sound = True
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                self.steering_wheel_angle = 0
            elif event.key == pygame.K_RIGHT:
                self.steering_wheel_angle = 0
            elif event.key == pygame.K_UP:
                self.move_direction = 0
                self.switch_sound = True
            elif event.key == pygame.K_DOWN:
                self.move_direction = 0
                self.switch_sound = True
        if event.type == pygame.KEYUP or event.type == pygame.KEYDOWN:
            pass




ColorMap = {
    generator.WALKABLE_TILE: WHITE,
    generator.WALL_TILE: RED,
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
        self.rect.topleft = Vector2(self.parent.maze_rect.topleft) + pos

    def draw(self):
        self.parent.screen.blit(self.image, self.rect)


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
        self.rect.topleft = Vector2(self.parent.maze_rect.topleft) + pos

    def contact_object(self):
        if not self.parent.chan_2.get_busy():
            self.parent.chan_2.play(self.sound_flower)
        self.kill()


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
        self.rect.topleft = Vector2(self.parent.maze_rect.topleft) + pos
        self.contacted = False

    def contact_object(self):
        if not self.contacted:
            if not self.parent.chan_2.get_busy():
                self.parent.chan_2.play(self.sound_frog)
        self.contacted = True
        self.parent.open_closed_rooms()


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
    def __init__(self, use_joystick, is_full_screen, player_type_str, rooms_count, speed, block_size):
        self.logger = setup_logging()
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
        if player_type_str == "bee":
            self.player = Bee(self, speed=speed)
        else:
            self.player = Car(self, speed=speed)
        self.joystick = None
        if use_joystick:
            self.joystick = init_joystick(self.logger)

    def clear_map(self):
        self.tiles.clear()
        self.walls.clear()
        self.screen.fill(BLACK)

    def grid_to_screen(self, pos):
        x = pos[0] * self.block_size
        y = pos[1] * self.block_size
        return x, y

    def draw_rooms(self):
        self.tiles.clear()
        sprites_wo_tiles = list()
        for sprite in self.all_sprites:
            if not isinstance(sprite, Tile):
                sprites_wo_tiles.append(sprite)
        self.all_sprites.empty()

        for x in range(self.gen.grid_width):
            for y in range(self.gen.grid_height):
                tile_type = self.gen.grid[x][y]
                if tile_type != generator.WALKABLE_TILE:
                    tile = Tile(self, self.grid_to_screen((x, y)), tile_type)
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

    def setup_map(self):
        self.gen.generate_maze(int(self.maze_width / self.block_size), int(self.maze_height / self.block_size))
        self.player.set_initial_position(self.grid_to_screen(self.gen.start_pos))
        self.all_sprites = pygame.sprite.Group()
        self.objects = pygame.sprite.Group()

        if isinstance( self.player, Bee):
            for x,y in self.gen.room_centers_except_start_room:
                flower = TFlower(self, self.grid_to_screen((x, y)))
                self.all_sprites.add(flower)
                self.objects.add(flower)
            if len(self.gen.room_corners_except_start_room) >  0:
                frog_place = random.choice(self.gen.room_corners_except_start_room)
                frog = TFrog(self, self.grid_to_screen(frog_place))
                self.all_sprites.add(frog)
                self.objects.add(frog)

        self.all_sprites.add(self.player)
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
        self.player.set_initial_position(self.grid_to_screen(self.gen.start_pos))

    def start_game(self):
        self.screen.fill(BLACK)
        self.setup_map()
        self.logger.info("start_game")
        pygame.display.flip()

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
            elif event.key == pygame.K_o:
                self.open_closed_rooms()

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
                    self.next_map()
                    self.logger.info("Joystick button released.")
                elif event.type == pygame.JOYAXISMOTION:
                    #axis = ['X', 'Y']
                    #self.logger.info("joystick: {}, movement: {} in the {}-axis".format(event.joy, event.value, axis[event.axis]))
                    joystick_direction[event.axis] = int(event.value)
                    for e in TKeyEventType.from_joystick_event(event):
                        self.player.handle_event(e)
                else:
                   self.check_game_events(event)
                self.player.handle_event(event)
                if joystick_direction[0] != 0 or joystick_direction[1] != 0:
                    self.logger.info("joystick_direction = {}".format(joystick_direction))

            self.screen.fill(WHITE)
            self.all_sprites.update()
            self.all_sprites.draw(self.screen)

            if self.print_victory:
                self.screen.fill((0, 0, 255))
                font = pygame.font.SysFont(None, 300)
                screen_text = font.render('ПОБЕДА!', True, (0, 200, 0))
                self.screen.blit(screen_text, (250, 280))
            pygame.display.flip()
            clock.tick(25)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-joystick", dest='use_joystick', default=False, action="store_true")
    parser.add_argument("--fullscreen", dest='fullscreen', default=False, action="store_true")
    parser.add_argument("--player", dest='player', default="bee", help="can be car or bee (default)")
    parser.add_argument("--rooms-count", dest='rooms_count', default=2, type=int)
    parser.add_argument("--speed", dest='speed', default=2, type=int)
    parser.add_argument("--block-size", dest='block_size', default=25, type=int)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    maze = TMaze(args.use_joystick, args.fullscreen, args.player, args.rooms_count, args.speed, args.block_size)
    maze.main_loop()
    pygame.quit()
