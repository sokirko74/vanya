from common import TMazeCommon

import pygame
import os
import math


class Player(pygame.sprite.Sprite):
    def __init__(self, parent, image, height, width, max_speed, sound_moving, collider_size, size=2,
                 sound_crash=os.path.join('assets', 'sounds', 'bee_crash.wav'),
                 sound_success=os.path.join('assets', 'sounds', 'success.wav')):
        pygame.sprite.Sprite.__init__(self)
        self.parent = parent
        self.screen_rect = self.parent.maze_rect
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
        self.image = pygame.transform.scale(self.image,
                                            (self.parent.block_size * self.width * self.size,
                                             self.parent.block_size * self.height * self.size))
        self.rect = self.image.get_rect()
        self.collider_size_start = collider_size
        self.collider_size = self.collider_size_start
        self.default_image = self.image.copy()
        self.default_rect = self.rect.copy()
        self.rect.topleft = parent.maze_rect.topleft
        self.max_speed = max_speed
        self.score = 0
        self.set_scale(size)

    def set_scale(self, scale):
        self.size = scale
        self.collider_size = self.collider_size_start * self.size
        self.image = pygame.transform.scale(self.image,
                                            (self.parent.block_size * self.width * self.size,
                                             self.parent.block_size * self.height * self.size))
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
        if self.collision_check(new_rect, [t.rect for t in self.parent.target_tiles]):
            if not self.parent.chan_2.get_busy():
                self.parent.chan_2.play(self.sound_success)
            self.score += 1
            self.parent.next_map()
        elif not self.collision_check(new_rect, self.parent.walls):
            self.rect = new_rect
        elif not self.parent.chan_2.get_busy():
            self.parent.chan_2.play(self.sound_crash)

    def collision_check(self, new_rect, c_ls):
        return TMazeCommon.rect_collide_list(new_rect, c_ls)

    def update_move(self):
        pass

    def set_pos(self, pos):
        self.rect.topleft = TMazeCommon.add_tuples(self.parent.maze_rect.topleft, pos)

    def handle_event(self, event):
        pass


class Bee(Player):
    def __init__(self, parent):
        super().__init__(parent,
                         image=os.path.join('assets', 'sprites', 'bee.png'),
                         height=2,
                         width=2,
                         max_speed=6,
                         collider_size=5,
                         sound_moving=os.path.join('assets', 'sounds', 'bee_moving.wav'))

    def update_move(self):
        pass

    def set_pos(self, pos):
        self.rect.topleft = TMazeCommon.add_tuples(self.screen_rect.topleft, pos)

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
                self.move_x = 0
            elif event.key == pygame.K_RIGHT:
                self.move_x = 0
            elif event.key == pygame.K_UP:
                self.move_y = 0
            elif event.key == pygame.K_DOWN:
                self.move_y = 0


class Car(Player):
    def __init__(self, parent):
        super().__init__(parent,
                         image=os.path.join('assets', 'sprites', 'truck.png'),
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
            if self.move_dir == 0:
                pygame.mixer.music.load(self.sound_idle)
            else:
                pygame.mixer.music.load(self.sound_moving)
            pygame.mixer.music.play(-1, fade_ms=300)
            self.switch_sound = False
        if self.move_dir != 0:
            if self.rotation != self.target_rotation:
                c_f = self.collider_front
                c_b = self.collider_back
                self.collider_front = TMazeCommon.rotate_point(self.collider_front_start, self.rotation - 90)
                self.collider_back = TMazeCommon.rotate_point(self.collider_back_start, self.rotation - 90)
                if self.collision_check(self.rect, self.parent.walls):
                    self.collider_front = c_f
                    self.collider_back = c_b
                else:
                    self.rotation += self.tire_rotation / 5
                    self.image, self.rect = TMazeCommon.rot_center(self.default_image, self.rect, self.rotation)
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
        t = TMazeCommon.add_tuples(new_rect.center, self.collider_front)
        if TMazeCommon.circle_collidelist(t, self.collider_size, c_ls) != -1:
            return True
        t = TMazeCommon.add_tuples(new_rect.center, self.collider_back)
        if TMazeCommon.circle_collidelist(t, self.collider_size, c_ls) != -1:
            return True
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
