import pygame
import os
import math
from pygame.math import Vector2
import threading
import time


# https://en.wikipedia.org/wiki/Unit_vector
def unit_vector(angle, coef):
    theta = math.radians(angle)
    return Vector2(round(coef * math.cos(theta)), round(coef * math.sin(theta)))


class MazePlayer(pygame.sprite.Sprite):
    def __init__(self, parent, image, height, width, max_speed, sound_moving,  size=2,
                 sound_crash=os.path.join('assets', 'sounds', 'bee_crash.wav'),
                 sound_success=os.path.join('assets', 'sounds', 'success.wav')):
        super().__init__()
        self.angle = 180
        self.parent = parent
        self.screen_rect = self.parent.maze_rect
        self.image = image
        self.orig_image = self.image.copy()
        self.sound_moving = sound_moving
        self.sound_crash = pygame.mixer.Sound(sound_crash)
        self.sound_crash.set_volume(0.2)
        self.sound_success = pygame.mixer.Sound(sound_success)
        self.width = width
        self.height = height
        self.music_thread = threading.Thread(target=self.watch_moving)
        self.music_thread.daemon = True
        self.run = True
        self.last_move_time_stamp = None
        self.music_thread.start()
        pygame.mixer.music.load(self.sound_moving)
        pygame.mixer.music.set_volume(0.2)


        self.max_speed = max_speed
        self.score = 0
        self.set_scale(size)

    def watch_moving(self):
        while self.run:
            if self.last_move_time_stamp is not None:
                if time.time() - self.last_move_time_stamp > 1:
                    pygame.mixer.music.stop()
                elif not pygame.mixer.music.get_busy():
                    print ("play music")
                    pygame.mixer.music.play(loops=-1, fade_ms=2000)
            time.sleep(0.5)

    def get_sound_success(self):
        return self.sound_success

    def set_scale(self, size):
        self.image = pygame.transform.scale(self.image,
                                            (self.parent.block_size * self.width * size,
                                             self.parent.block_size * self.height * size))
        self.rect = self.image.get_rect()
        self.orig_image = self.image.copy()

    def collision_check(self, obstacles):
        collided = pygame.sprite.spritecollideany(self, obstacles, collided=pygame.sprite.collide_mask)
        return collided

    def check_all_collisions(self, play_sound=True):
        if self.collision_check(self.parent.target_tiles) is not None:
            pygame.mixer.music.stop()
            time.sleep(0.1)
            if not self.parent.chan_2.get_busy():
                self.parent.chan_2.play(self.get_sound_success())
            self.score += 1
            time.sleep(1)
            #pygame.mixer.music.play(-1, fade_ms=2000)
            self.kill()
            for f in self.parent.objects:
                f.kill()
            self.parent.print_victory = True
            return True
        else:
            wall_collision = self.collision_check(self.parent.walls)
            if wall_collision is not None:
                if play_sound:
                    if not self.parent.chan_2.get_busy():
                        self.parent.chan_2.play(self.sound_crash)
                return False
            else:
                collided_objects = pygame.sprite.spritecollideany(self, self.parent.objects, collided=pygame.sprite.collide_mask)
                if collided_objects is not None:
                    collided_objects.contact_object()
                self.last_move_time_stamp = time.time()
                return True

    def set_initial_position(self, pos):
        self.rect.center = Vector2(self.parent.maze_rect.topleft) + Vector2(pos)
        self.angle = 180
        self.image = pygame.transform.rotate(self.orig_image, -self.angle)

    def handle_event(self, event):
        pass

    def stop_playing(self):
        self.run = False
        self.music_thread.join(1)


