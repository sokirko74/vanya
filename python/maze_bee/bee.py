from utils.maze_player import MazePlayer
from utils.colors import TColors
import pygame
import os
from pygame.math import Vector2


def create_circle():
    surface = pygame.Surface((100, 100),  pygame.SRCALPHA, 32)
    pygame.draw.circle(surface, TColors.blue, (50, 50), 50, 1)
    return surface


normal_sound = os.path.join('assets', 'sounds', 'bee_moving.wav')
loaded_sound = os.path.join('assets', 'sounds', 'bee_moving_loaded.wav')


class TBee(MazePlayer):
    def __init__(self, parent, speed=3, width=2, height=2):
        super().__init__(parent,
                         image=create_circle(),
                         height=height,
                         width=width,
                         max_speed=speed,
                         sound_moving=normal_sound)

        self.direction_vector = Vector2(0, -1)
        self.move_player = False
        self.rotate_player = False
        self.loaded_with_milk = False
        self.loaded_with_bone = False

        self.shadow = pygame.sprite.Sprite()
        self.shadow.image = pygame.image.load(os.path.join('assets', 'sprites', 'bee.png'))
        w, h = self.rect.size
        self.shadow.image = pygame.transform.scale(self.shadow.image, (w+30, h+30))
        self.orig_shadow_image = self.shadow.image.copy()

    def load_milk(self):
        self.change_music(loaded_sound)
        self.loaded_with_milk = True

    def unload_milk(self):
        self.change_music(normal_sound)
        self.loaded_with_milk = False

    def load_bone(self):
        self.change_music(loaded_sound)
        self.loaded_with_bone = True

    def unload_bone(self):
        self.change_music(normal_sound)
        self.loaded_with_bone = False

    def is_loaded(self):
        return self.loaded_with_bone or self.loaded_with_milk

    def get_sound_success(self):
        return pygame.mixer.Sound(os.path.join('assets', 'sounds', 'success.wav'))

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

    def draw_shadow(self):
        rect = self.shadow.image.get_rect(center=self.rect.center)
        self.parent.screen.blit(self.shadow.image, rect)

    def update(self):
        if not self.move_player and not self.rotate_player:
            return
        angle = Vector2(0, 0).angle_to(self.direction_vector) + 270

        save_rect = self.rect.copy()
        save_shadow_image = self.shadow.image
        #print(self.rect.center)
        self.shadow.image = pygame.transform.rotate(self.orig_shadow_image, -angle)

        #https://stackoverflow.com/questions/47645155/pygame-sprite-rotation-not-staying-centeTColors.red
        self.rect = self.image.get_rect(center=self.rect.center)

        if self.move_player:
            self.rect.center += self.direction_vector * self.max_speed

        if not self.check_all_collisions():
            self.shadow.image = save_shadow_image
            self.rect = save_rect
