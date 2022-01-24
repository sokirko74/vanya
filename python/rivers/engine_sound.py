#we have to create separate files since pygame.mixer.music.set_pos  does not work on our wav files
# ppygame.error: set_pos unsupported for this codec
#snd = pygame.mixer.music.load('assets/sounds/engine_increase.wav')
#pygame.mixer.music.play()
#pygame.mixer.music.set_pos(10)

#Use this script:
#rm -rf assets/sounds/ford
#python3 engine_sound.py --action prepare  --input assets/sounds/engine_increase.wav --segment-folder assets/sounds/ford/
#python3 engine_sound.py --action test  --segment-folder assets/sounds/ford/


import os
import time
import pygame
import threading
from pydub import AudioSegment
import argparse


class TEngineState:
    engine_increase = 1
    engine_decrease = 2
    engine_stable = 3


class TSpeedSound(pygame.mixer.Sound):
    segment_folder = None

    def get_state(self):
        if self.start_speed < self.last_speed:
            return TEngineState.engine_increase
        elif self.start_speed == self.last_speed:
            return TEngineState.engine_stable
        else:
            return TEngineState.engine_decrease

    def get_speed(self):
        return self.last_speed

    @staticmethod
    def get_file_name(start_speed, last_speed):
        return os.path.join(TSpeedSound.segment_folder, 'speed_{}_{}.wav'.format(start_speed, last_speed))

    def __init__(self, start_speed, last_speed):
        self.start_speed = start_speed
        self.last_speed = last_speed
        filename = TSpeedSound.get_file_name(self.start_speed, self.last_speed)
        super().__init__(filename)
        self.filename = filename


class TEngineSound(threading.Thread):
    def __init__(self, max_speed, segment_folder):
        TSpeedSound.segment_folder = segment_folder
        threading.Thread.__init__(self)
        self.max_speed = max_speed
        self.sounds = dict()
        self.stop = False
        self.channel = pygame.mixer.Channel(0)

    def load_sounds(self):
        for i in range(self.max_speed):
            self.sounds[(i, i+1)] = TSpeedSound(i, i+1)
            self.sounds[(i+1, i)] = TSpeedSound(i+1, i)
            self.sounds[(i + 1, i + 1)] = TSpeedSound(i + 1, i + 1)

    def start_engine(self):
        self.load_sounds()
        self.start()

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

    def create_sound_segments_from_engine_increasing_file(self, input, segment_time):
        if not os.path.exists(TSpeedSound.segment_folder):
            print("create {}".format(TSpeedSound.segment_folder))
            os.mkdir(TSpeedSound.segment_folder)

        format = 'wav'
        assert input.endswith(format)
        song = AudioSegment.from_wav(input)
        assert self.max_speed * segment_time < song.duration_seconds
        for speed in range(self.max_speed):
            offset = segment_time * speed
            increasing = song[offset*1000:(offset+segment_time)*1000]
            increasing.export(TSpeedSound.get_file_name(speed, speed+1), format=format)
            decreasing = increasing.reverse().set_channels(1)
            decreasing.export(TSpeedSound.get_file_name(speed + 1, speed), format=format)
            stable = (increasing[-1500:] + decreasing[:1500]) * 10
            stable = stable.set_channels(1)
            stable.export(TSpeedSound.get_file_name(speed + 1, speed + 1), format=format)
        print("all done")

    def test_engine(self):
         self.start_engine()
         pygame.display.init()
         screen = pygame.display.set_mode((800, 600))
         while True:
             keys = pygame.key.get_pressed()
             if keys[pygame.K_UP]:
                 self.increase_speed()
             elif not keys[pygame.K_UP]:
                 self.decrease_speed()
             if keys[pygame.K_ESCAPE]:
                 print("got escape key")
                 sound.stop = True
                 sound.join(2)
                 break
             time.sleep(0.2)
             pygame.event.pump()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--segment-folder", dest='segment_folder', default='assets/sounds/ford')
    parser.add_argument("--speed-count", dest='speed_count', default=10, type=int)
    parser.add_argument("--input-audio", dest='input')
    parser.add_argument("--action", dest='action', help="can nbe prepare, test")
    return parser.parse_args()


def main():
    pygame.mixer.init()
    args = parse_args()
    sound = TEngineSound(max_speed=args.speed_count, segment_folder=args.segment_folder)
    if args.action == "test":
        sound.test_engine()
    elif args.action == "prepare":
        sound.create_sound_segments_from_engine_increasing_file(args.input, 2)
    else:
        raise Exception("unknown action")


if __name__ == '__main__':
    main()