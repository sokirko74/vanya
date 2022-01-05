from utils.joystick import init_joystick
import utils.maze_generator as generator
from utils.maze_player import Player
from utils.logging_wrapper import setup_logging

import random
import os
import pygame
import argparse
from pygame.math import Vector2


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)


ColorMap = {
    generator.WALKABLE_TILE: WHITE,
    generator.WALL_TILE: RED,
    generator.TARGET_TILE: GREEN,
}


class Bee(Player):
    def __init__(self, parent, speed=3):
        super().__init__(parent,
                         image=os.path.join('assets', 'sprites', 'bee.png'),
                         height=2,
                         width=2,
                         max_speed=speed,
                         sound_moving=os.path.join('assets', 'sounds', 'bee_moving.wav'))
        self.direction_vector = Vector2(0, -1)
        self.move_player = False
        self.rotate_player = False

    def get_sound_success(self):
        paths = list([os.path.join('assets', 'sounds', 'success.wav')])
        self.parent.logger.info("choice out of {} sounds".format(len(paths)))
        path = random.choice(paths)
        return pygame.mixer.Sound(path)

    def set_move_x(self, x):
        self.direction_vector.x = x
        self.move_player = True

    def set_move_y(self, y):
        self.direction_vector.y = y
        self.move_player = True

    def rotate(self):
        self.direction_vector = self.direction_vector.rotate(45)
        self.rotate_player = True

    def handle_event(self, event):
        self.move_player = False
        self.rotate_player = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.set_move_x(-1)
            elif event.key == pygame.K_RIGHT:
                self.set_move_x(1)
            elif event.key == pygame.K_UP:
                self.set_move_y(-1)
            elif event.key == pygame.K_DOWN:
                self.set_move_y(1)
            elif event.key == pygame.K_a:
                self.rotate()
                self.update()
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                self.direction_vector.x = 0
            elif event.key == pygame.K_RIGHT:
                self.direction_vector.x = 0
            elif event.key == pygame.K_UP:
                self.direction_vector.y = 0
            elif event.key == pygame.K_DOWN:
                self.direction_vector.y = 0

    def update(self):
        if not self.move_player and not self.rotate_player:
            return
        angle = Vector2(0, 0).angle_to(self.direction_vector) + 270

        save_rect = self.rect.copy()
        save_image = self.image
        print(self.rect.center)
        self.image = pygame.transform.rotate(self.orig_image, -angle)

        #https://stackoverflow.com/questions/47645155/pygame-sprite-rotation-not-staying-centered
        self.rect = self.image.get_rect(center=self.rect.center)

        if self.move_player:
            self.rect.center += self.direction_vector * self.max_speed

        s = self.image.get_rect(topleft=self.rect.topleft)
        #print(self.rect.center, s.center)
        #if s.center != self.rect.center:
        #    self.image
        #self.image.get_rect()
        if not self.check_all_collisions():
            self.image = save_image
            if not self.check_all_collisions():
                # bee is not a rect
                self.rect = save_rect


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
        self.playable_types = Player.__subclasses__()
        self.playable_types_buttons = []
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
        self.player = Bee(self, speed=speed)
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

            pygame.draw.rect(self.screen, BLACK, self.player.rect, width=1)
            pygame.draw.rect(self.screen, BLACK, self.player.image.get_rect(), width=1)
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
