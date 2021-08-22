import pygame
import pygame_gui
import random
from enum import Enum
import numpy as np
import math
import os
import generator

'''
SPACE - Pause and Settings
ESC - Quit
R - New map
F - Enter Fullscreen
'''

# === CONSTANTS ===

MAP_FILL_SCREEN = True

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

BLOCK_SIZE = 25

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# === CLASSES ===


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


class Player(pygame.sprite.Sprite):
    def __init__(self, image, height, width, max_speed, sound_moving, collider_size, size=2,
                 sound_crash=os.path.join('assets', 'sounds', 'bee_crash.wav'),
                 sound_success=os.path.join('assets', 'sounds', 'success.wav')):
        pygame.sprite.Sprite.__init__(self)
        self.move_x = 0
        self.move_y = 0
        self.size = size
        self.image = pygame.image.load(image)
        self.sound_moving = sound_moving
        self.sound_crash = pygame.mixer.Sound(sound_crash)
        self.sound_success = pygame.mixer.Sound(sound_success)
        self.width = width
        self.height = height
        pygame.mixer.music.load(self.sound_moving)
        pygame.mixer.music.play(-1, fade_ms=2000)
        self.image = pygame.transform.scale(self.image, (BLOCK_SIZE * self.width * self.size, BLOCK_SIZE * self.height *self.size))
        self.rect = self.image.get_rect()
        self.collider_size_start = collider_size
        self.collider_size = self.collider_size_start
        self.default_image = self.image.copy()
        self.default_rect = self.rect.copy()
        self.rect.center = screen_rect.center
        self.max_speed = max_speed
        self.score = 0
        self.set_scale(size)

    def set_scale(self, scale):
        self.size = scale
        self.collider_size = self.collider_size_start * self.size
        self.image = pygame.transform.scale(self.image,
                                            (BLOCK_SIZE * self.width * self.size, BLOCK_SIZE * self.height * self.size))
        self.rect = self.image.get_rect()
        self.default_image = self.image.copy()
        self.default_rect = self.rect.copy()

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def update(self):
        self.update_move()
        new_rect = self.rect.copy()
        new_rect.x += round(self.move_x)
        new_rect.y += round(self.move_y)
        if self.collision_check(new_rect, [t.rect for t in target_tiles]):
            if not chan_2.get_busy(): chan_2.play(self.sound_success)
            self.score += 1
            next_map()
        elif not self.collision_check(new_rect, walls):
            self.rect = new_rect
        elif not chan_2.get_busy():
            chan_2.play(self.sound_crash)

    def collision_check(self, new_rect, c_ls):
        return circle_collidelist(new_rect.center, self.collider_size, c_ls) != -1

    def update_move(self):
        pass

    def set_pos(self, pos):
        self.rect.center = add_tuples(screen_rect.center, pos)

    def handle_event(self, event):
        pass


class Bee(Player):
    def __init__(self):
        super().__init__(image=os.path.join('assets', 'sprites', 'bee.png'),
                         height=2,
                         width=2,
                         max_speed=6,
                         collider_size=5,
                         sound_moving=os.path.join('assets', 'sounds', 'bee_moving.wav'))

    def update_move(self):
        pass

    def set_pos(self, pos):
        self.rect.center = add_tuples(screen_rect.center, pos)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.move_x -= self.max_speed
            elif event.key == pygame.K_RIGHT:
                self.move_x += self.max_speed
            elif event.key == pygame.K_UP:
                self.move_y -= self.max_speed
            elif event.key == pygame.K_DOWN:
                self.move_y += self.max_speed
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                self.move_x += self.max_speed
            elif event.key == pygame.K_RIGHT:
                self.move_x -= self.max_speed
            elif event.key == pygame.K_UP:
                self.move_y += self.max_speed
            elif event.key == pygame.K_DOWN:
                self.move_y -= self.max_speed


class Car(Player):
    def __init__(self):
        super().__init__(image=os.path.join('assets', 'sprites', 'truck.png'),
                         height=4,
                         width=3,
                         max_speed=4,
                         collider_size=16,
                         sound_moving=os.path.join('assets', 'sounds', 'truck_driving.wav'),
                         sound_crash=os.path.join('assets', 'sounds', 'truck_crash.wav'))

        self.sound_idle = os.path.join('assets', 'sounds', 'truck.wav')
        self.switch_sound = False
        pygame.mixer.music.load(self.sound_idle)
        pygame.mixer.music.play(-1, fade_ms=2000)
        self.move_dir = 0
        self.rotation = 0
        self.rotation_changed = True
        self.tire_rotation = 0
        self.tire_rotation_max = 40
        self.target_rotation = 0

        self.collider_front_start = (0, -self.height / 4 * self.collider_size)
        self.collider_back_start = (0, self.height / 4 * self.collider_size)
        self.collider_front = self.collider_front_start
        self.collider_back = self.collider_back_start

    def update(self):
        self.target_rotation += self.tire_rotation
        if self.switch_sound:
            pygame.mixer.music.stop()
            if self.move_dir == 0: pygame.mixer.music.load(self.sound_idle)
            else: pygame.mixer.music.load(self.sound_moving)
            pygame.mixer.music.play(-1, fade_ms=300)
            self.switch_sound = False
        if self.move_dir != 0:
            if self.rotation != self.target_rotation:
                c_f = self.collider_front
                c_b = self.collider_back
                self.collider_front = rotate_point(self.collider_front_start, self.rotation - 90)
                self.collider_back = rotate_point(self.collider_back_start, self.rotation - 90)
                if self.collision_check(self.rect, walls):
                    self.collider_front = c_f
                    self.collider_back = c_b
                else:
                    self.rotation += self.tire_rotation / 5
                    self.image, self.rect = rot_center(self.default_image, self.rect, self.rotation)
                    self.target_rotation %= 360
                    self.rotation %= 360
        super().update()

    def set_scale(self, scale):
        super().set_scale(scale)
        self.collider_front_start = (0, -self.height / 4 * self.collider_size)
        self.collider_back_start = (0, self.height / 4 * self.collider_size)
        self.collider_front = self.collider_front_start
        self.collider_back = self.collider_back_start

    def collision_check(self, new_rect, c_ls):
        if circle_collidelist(add_tuples(new_rect.center, self.collider_front), self.collider_size, c_ls) != -1: return True
        if circle_collidelist(add_tuples(new_rect.center, self.collider_back), self.collider_size, c_ls) != -1: return True
        return False

    def update_move(self):
        self.move_x = -math.sin(math.radians(self.rotation)) * self.max_speed * self.move_dir
        self.move_y = -math.cos(math.radians(self.rotation)) * self.max_speed * self.move_dir

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.tire_rotation = self.tire_rotation_max
            elif event.key == pygame.K_RIGHT:
                self.tire_rotation = -self.tire_rotation_max
            elif event.key == pygame.K_UP:
                self.move_dir = 1
                self.switch_sound = True
            elif event.key == pygame.K_DOWN:
                self.move_dir = -1
                self.switch_sound = True
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                self.tire_rotation = 0
            elif event.key == pygame.K_RIGHT:
                self.tire_rotation = 0
            elif event.key == pygame.K_UP:
                self.move_dir = 0
                self.switch_sound = True
            elif event.key == pygame.K_DOWN:
                self.move_dir = 0
                self.switch_sound = True
        if event.type == pygame.KEYUP or event.type == pygame.KEYDOWN:
            pass


class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, tile_type=-1, color=BLACK):
        pygame.sprite.Sprite.__init__(self)
        if tile_type in ColorMap: color = ColorMap[tile_type]
        self.tile_type = tile_type
        self.image = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE))
        self.wall = False
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.center = add_tuples(screen_rect.center, pos)

    def draw(self):
        screen.blit(self.image, self.rect)


class AnotSlider():
    def __init__(self, disp, text, start_value, value_range, func):
        self.text = text
        self.func = func
        s_w = SCREEN_WIDTH / 2 + disp[0]
        s_h = SCREEN_HEIGHT / 2 + disp[1]
        self.s = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect((s_w, s_h), (300, 30)),
                                                        start_value=start_value, value_range=value_range,
                                                        manager=manager)
        self.s_button_rect = pygame.Rect((s_w - 200, s_h), (200, 30))
        self.s_button = pygame_gui.elements.UIButton(relative_rect=self.s_button_rect,
                                                     text=text + ': ' + str(self.s.current_value), manager=manager)

    def update(self):
        self.func(self.s.current_value)
        self.s_button.text = self.text + ': ' + str(self.s.current_value)
        self.s_button.rebuild()


# === FUNCTIONS ===

def circle_collidelist(center, r, rec_ls):
    for i in range(len(rec_ls)):
        circle_distance_x = abs(center[0]-rec_ls[i].centerx)
        circle_distance_y = abs(center[1]-rec_ls[i].centery)
        if circle_distance_x > rec_ls[i].w/2.0+r or circle_distance_y > rec_ls[i].h/2.0+r:
            continue
        if circle_distance_x <= rec_ls[i].w/2.0 or circle_distance_y <= rec_ls[i].h/2.0:
            return i
    return -1


def rotate_point(pt, angle):
    x = pt[1] * math.cos(math.radians(angle)) + pt[0] * math.sin(math.radians(angle))
    y = pt[0] * math.cos(math.radians(angle)) - pt[1] * math.sin(math.radians(angle))
    return (x, y)


def rotate_shape(pt_ls, angle):
    res = []
    s = math.sin(math.radians(angle))
    c = math.cos(math.radians(angle))
    for pt in pt_ls:
        x = pt[1] * c + pt[0] * s
        y = pt[0] * c - pt[1] * s
        res.append((x, y))
    return res


def rot_center(image, rect, angle):
    c = rect.center
    rot_image = pygame.transform.rotate(image, angle)
    rot_rect = rot_image.get_rect()
    rot_rect.center = c
    return rot_image, rot_rect


def clear_map():
    tiles.clear()
    walls.clear()
    gen.clear()
    screen.fill(BLACK)


def grid_to_screen(pos):
    t = (pos[0] * BLOCK_SIZE - len(gen.grid[0]) * BLOCK_SIZE / 2 - 10,
         pos[1] * BLOCK_SIZE - len(gen.grid) * BLOCK_SIZE / 2 - 10)
    return t


def add_tuples(a, b):
    return (a[0] + b[0], a[1] + b[1])


def setup_map():
    gen.generate_maze()
    player.set_pos(grid_to_screen(gen.start))
    for i in range(len(gen.grid)):
        for j in range(len(gen.grid[0])):
            tiles.append(Tile(grid_to_screen((j, i)), gen.grid[i][j]))
    global walls, target_tiles
    walls = [t.rect for t in tiles if t.tile_type == generator.WALL_TILE]
    target_tiles = [t for t in tiles if t.tile_type == generator.TARGET_TILE]


def render_map():
    for t in tiles:
        t.draw()


def toggle_pause():
    global is_paused
    is_paused = not is_paused
    if is_paused:
        pygame.mixer.music.stop()
    else:
        player.switch_sound = True


def next_map():
    clear_map()
    setup_map()
    render_map()
    global rendered_map
    rendered_map = screen.copy()
    player.set_pos(grid_to_screen(gen.start))


def update_text_surface(text=None):
    global text_surfaces
    if text is not None:
        texts = text.splitlines()
        text_surfaces = [None] * len(texts)
        for i, t in enumerate(texts):
            text_surfaces[i] = font.render(t, False, text_color)
            screen.blit(text_surfaces[i], (SCREEN_WIDTH - font.size(t)[1] * 10 - 50, SCREEN_HEIGHT - 1000 + font.size(t)[1] * i))


def arrange_buttons():
    s_w = SCREEN_WIDTH / 2
    s_h = SCREEN_HEIGHT / 2
    button_width = 500 / len(playable_types)
    for i, x in enumerate(playable_types):
        pos = (s_w - 300 + button_width * i, s_h - 400)
        playable_types_buttons.append(
            pygame_gui.elements.UIButton(relative_rect=pygame.Rect(pos, (button_width, 200)), text=x.__name__,
                                         manager=manager))


def start_game():
    global rendered_map
    screen.fill(BLACK)
    if MAP_FILL_SCREEN:
        gen.rows = int(SCREEN_HEIGHT / BLOCK_SIZE)
        gen.cols = int(SCREEN_WIDTH / BLOCK_SIZE)
    setup_map()
    render_map()
    rendered_map = screen.copy()
    arrange_buttons()


def check_game_events(event):
    global is_running, screen, player
    if event.type == pygame.QUIT:
        is_running = False
    elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_SPACE:
            toggle_pause()
        if event.key == pygame.K_ESCAPE:
            is_running = False
        elif event.key == pygame.K_r:
            next_map()
        elif event.key == pygame.K_f:
            if not is_fullscreen:
                screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags=pygame.FULLSCREEN)
            else:
                screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags=pygame.RESIZABLE)

    if event.type == pygame.USEREVENT:
        if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element in playable_types_buttons:
                player = playable_types[playable_types_buttons.index(event.ui_element)]()
                player.set_pos(grid_to_screen(gen.target_room_source))
        elif event.user_type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            [s for s in settings_sliders if s.s == event.ui_element][0].update()
            if event.ui_element == settings_sliders[0].s:
                if settings_sliders[0].s.current_value >= settings_sliders[1].s.current_value:
                    settings_sliders[1].s.current_value = settings_sliders[0].s.current_value
                    settings_sliders[1].s.rebuild()
                    settings_sliders[1].update()
            elif event.ui_element == settings_sliders[1].s:
                if settings_sliders[1].s.current_value <= settings_sliders[0].s.current_value:
                    settings_sliders[0].s.current_value = settings_sliders[1].s.current_value
                    settings_sliders[0].s.rebuild()
                    settings_sliders[0].update()
            if settings_sliders[5].s.current_value == 0:
                settings_sliders[5].s_button.text = settings_sliders[5].text + ': Rand'
                settings_sliders[5].s_button.rebuild()
            elif settings_sliders[5].s.current_value == 100:
                settings_sliders[5].s_button.text = settings_sliders[5].text + ': Max'
                settings_sliders[5].s_button.rebuild()

# --- init ---

pygame.init()
pygame.font.init()

pygame.mixer.set_num_channels(8)
chan_2 = pygame.mixer.Channel(2)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
screen_rect = screen.get_rect()

manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT))

# --- objects ---

font = pygame.font.SysFont('Impact', 20, italic=False, bold=True)
text_color = (120, 120, 120)

gen = generator.Generator()
player = Car()
rendered_map = None
tiles = []
walls = []
target_tiles = []
text_surfaces = []
playable_types = Player.__subclasses__()
playable_types_buttons = []
score = 0
start_game()

def s1_f(x): gen.min_rooms = x
def s2_f(x): gen.max_rooms = x
def s3_f(x): gen.min_room_connections = x
def s4_f(x): gen.max_room_size = x
def s5_f(x): gen.allow_redundant_connections = bool(x)
def s6_f(x): gen.distance_to_target = x
def s7_f(x): gen.path_width = x
def s8_f(x): gen.cols = x
def s9_f(x): gen.rows = x
def s10_f(x): player.set_scale(x)
def s11_f(x): player.max_speed = x
def s12_f(x): global BLOCK_SIZE; BLOCK_SIZE = x

settings_sliders = [
    AnotSlider(disp=(-100, -150), text='Min Rooms', start_value=gen.min_rooms, value_range=(1, 100), func=s1_f),
    AnotSlider(disp=(-100, -110), text='Max Rooms', start_value=gen.max_rooms, value_range=(1, 100), func=s2_f),
    AnotSlider(disp=(-100, -70), text='Min Room Connections', start_value=gen.min_room_connections, value_range=(1, 20),func=s3_f),
    AnotSlider(disp=(-100, -30), text='Max Room Size', start_value=gen.max_room_size, value_range=(1, 500), func=s4_f),
    AnotSlider(disp=(-100, 10), text='Redundant Connections', start_value=int(gen.allow_redundant_connections),value_range=(0, 1), func=s5_f),
    AnotSlider(disp=(-100, 50), text='Distance To Target', start_value=gen.distance_to_target, value_range=(0, 100),func=s6_f),
    AnotSlider(disp=(-100, 90), text='Path Width', start_value=gen.path_width, value_range=(1, 20), func=s7_f),
    AnotSlider(disp=(-100, 130), text='Map Width', start_value=gen.cols, value_range=(1, 500), func=s8_f),
    AnotSlider(disp=(-100, 170), text='Map Height', start_value=gen.rows, value_range=(1, 500), func=s9_f),
    AnotSlider(disp=(-100, 210), text='Player Size', start_value=player.size, value_range=(1, 10), func=s10_f),
    AnotSlider(disp=(-100, 250), text='Player Max Speed', start_value=player.max_speed, value_range=(1, 50), func=s11_f),
    AnotSlider(disp=(-100, 290), text='Block Size', start_value=BLOCK_SIZE, value_range=(1, 100), func=s12_f)
]

# --- mainloop ---

clock = pygame.time.Clock()
is_running = True
is_paused = False
is_fullscreen = False

while is_running:
    time_delta = clock.tick(120) / 1000.0
    for event in pygame.event.get():
        check_game_events(event)
        if (not is_paused):
            player.handle_event(event)
        if (is_paused): manager.process_events(event)

    manager.update(time_delta)
    player.update()
    screen.blit(rendered_map, (0, 0))
    update_text_surface(f'MazeGame    |    Score:   {player.score} \n\n'
                        f'R - New Level\n'
                        f'F - Fullscreen\n'
                        f'SPACE - Pause')
    player.draw(screen)
    if (is_paused): manager.draw_ui(screen)
    pygame.display.update([player.rect, screen_rect])

    clock.tick(25)

pygame.quit()
