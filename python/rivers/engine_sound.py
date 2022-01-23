import os
import time
import pygame
import sys
import threading, queue


class TEngineState:
    engine_increase = 1
    engine_decrease = 2
    engine_stable = 3


FOLDER = 'assets/sounds/ford'


class TSound(pygame.mixer.Sound):
    def get_state(self):
        if self.start_speed < self.last_speed:
            return TEngineState.engine_increase
        elif self.start_speed == self.last_speed:
            return TEngineState.engine_stable
        else:
            return TEngineState.engine_decrease

    def get_speed(self):
        return self.last_speed

    def __init__(self, start_speed, last_speed):
        self.start_speed = start_speed
        self.last_speed = last_speed
        filename = os.path.join(FOLDER, 'speed_{}_{}.wav'.format(self.start_speed, self.last_speed))
        super().__init__(filename)
        self.filename = filename


class TEngineSound(threading.Thread):
    def __init__(self, max_speed=10):
        threading.Thread.__init__(self)
        self.max_speed = max_speed
        pygame.mixer.init()
        self.sounds = dict()
        for i in range(self.max_speed):
            self.sounds[(i, i+1)] = TSound(i, i+1)
            self.sounds[(i+1, i)] = TSound(i+1, i)
            self.sounds[(i + 1, i + 1)] = TSound(i + 1, i + 1)

        self.stop = False
        self.current_sound = None
        self.channel = pygame.mixer.Channel(0)

    def get_state(self):
        if not self.channel.get_busy():
            return TEngineState.engine_stable
        return self.channel.get_sound().get_state()

    def is_working(self):
        return self.channel.get_busy()

    def get_current_speed(self):
        if not self.is_working():
            return 0
        return self.channel.get_sound().get_speed()

    def stop_sounds(self):
        self.channel.stop()

    def get_increase_sound(self, speed):
        return self.sounds[(speed, speed + 1)]

    def get_decrease_sound(self, speed):
        return self.sounds[(speed+1, speed)]

    def get_stable_sound(self, speed):
        return self.sounds[(speed, speed)]

    def queue_sound(self, snd):
        print("queue sound {} {} ".format(snd.start_speed, snd.last_speed))
        self.channel.queue(snd)

    def play_sound(self, snd):
        print("play sound {} {} ".format(snd.start_speed, snd.last_speed))
        self.channel.play(snd)

    def queue_sound_after(self, snd):
        state = snd.get_state()
        speed = snd.get_speed()
        print  ("state = {}".format(state))
        if state == TEngineState.engine_increase:
            if speed != self.max_speed:
                self.queue_sound(self.get_increase_sound(speed))
            else:
                self.queue_sound(self.get_stable_sound(speed))
        elif state == TEngineState.engine_stable:
            self.queue_sound(self.get_stable_sound(speed))
        elif state == TEngineState.engine_decrease:
            if speed > 0:
                self.queue_sound(self.get_decrease_sound(speed - 1))
        else:
            assert False

    def run(self):
        while not self.stop:
            if self.channel.get_busy():
                snd = self.channel.get_sound()
                print('now playing {}'.format(snd.filename))
                if self.channel.get_queue() is None:
                    self.queue_sound_after(snd)

            time.sleep(0.5)

    def increase_speed(self):
        if self.get_state() != TEngineState.engine_increase:
            speed = self.get_current_speed()
            if speed != self.max_speed:
                self.play_sound(self.get_increase_sound(speed))

    def decrease_speed(self):
        if self.is_working():
            if self.get_state() != TEngineState.engine_decrease:
                speed = self.get_current_speed()
                self.play_sound(self.get_decrease_sound(speed-1))


if __name__ == '__main__':
    sound = TEngineSound(max_speed=10)
    sound.start()
    pygame.display.init()
    screen = pygame.display.set_mode((800, 600))
    up_pressed = False
    down_pressed = False
    while True:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            sound.increase_speed()
        elif not keys[pygame.K_UP]:
            sound.decrease_speed()
        #sound.increase_speed()
        if keys[pygame.K_ESCAPE]:
            print ("got escape key")
            sound.stop = True
            sound.join(2)
            break
        time.sleep(0.2)
        pygame.event.pump()