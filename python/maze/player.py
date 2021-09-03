import pygame
import os
import math
from pygame.math import Vector2


# https://en.wikipedia.org/wiki/Unit_vector

def unit_vector(angle, coef):
    theta = math.radians(angle)
    return Vector2(round(coef * math.cos(theta)), round(coef * math.sin(theta)))


class Player(pygame.sprite.Sprite):
    def __init__(self, parent, image, height, width, max_speed, sound_moving,  size=2,
                 sound_crash=os.path.join('assets', 'sounds', 'bee_crash.wav'),
                 sound_success=os.path.join('assets', 'sounds', 'success.wav')):
        pygame.sprite.Sprite.__init__(self)
        self.angle = 180
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
        self.orig_image = self.image.copy()
        self.default_rect = self.rect.copy()
        self.max_speed = max_speed
        self.score = 0
        self.set_scale(size)

    def set_scale(self, scale):
        self.size = scale
        self.image = pygame.transform.scale(self.image,
                                            (self.parent.block_size * self.width * self.size,
                                             self.parent.block_size * self.height * self.size))
        self.rect = self.image.get_rect()
        self.orig_image = self.image.copy()
        self.default_rect = self.rect.copy()

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def collision_check(self, obstacles):
        collided = pygame.sprite.spritecollideany(self, obstacles, collided=pygame.sprite.collide_mask)
        return collided is not None

    def check_all_collisions(self):
        if self.collision_check(self.parent.target_tiles):
            if not self.parent.chan_2.get_busy():
                self.parent.chan_2.play(self.sound_success)
            self.score += 1
            self.parent.next_map()
            return True
        elif self.collision_check(self.parent.walls):
            if not self.parent.chan_2.get_busy():
                self.parent.chan_2.play(self.sound_crash)
            return False
        else:
            return True

    def set_initial_position(self, pos):
        self.rect.center = Vector2(self.parent.maze_rect.topleft) + Vector2(pos)
        self.angle = 180
        self.image = pygame.transform.rotate(self.orig_image, -self.angle)

    def handle_event(self, event):
        pass


class Bee(Player):
    def __init__(self, parent):
        super().__init__(parent,
                         image=os.path.join('assets', 'sprites', 'bee.png'),
                         height=2,
                         width=2,
                         max_speed=6,
                         sound_moving=os.path.join('assets', 'sounds', 'bee_moving.wav'))
        self.orig_image = self.image.copy()

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

    def update(self):
        save_rect = self.rect.copy()
        self.rect.x += round(self.move_x)
        self.rect.y += round(self.move_y)
        if not self.check_all_collisions():
            self.rect = save_rect


class Car(Player):
    def __init__(self, parent):
        super().__init__(parent,
                         image=os.path.join('assets', 'sprites', 'truck.png'),
                         height=3,
                         width=2,
                         max_speed=4,
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
                self.steering_wheel_angle = -1
            elif event.key == pygame.K_RIGHT:
                self.steering_wheel_angle = +1
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
