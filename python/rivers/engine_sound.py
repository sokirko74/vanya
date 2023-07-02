import json
import os
import enum
import pyaudio
import  librosa
import numpy as np
from collections import namedtuple
from typing import List


class TEngineState(enum.Enum):
    engine_increase = 1
    engine_decrease = 2
    engine_stable = 3


<<<<<<< HEAD
IncreaseProps = namedtuple('IncreaseProps', ['frame_rate', 'volume'])


class TEngineSound:
    def __init__(self, log, engine_folder, limit_speed):
        self.log = log
        props_file = os.path.join(engine_folder, "audio_props.json")
        props = dict()
        if os.path.exists(props_file):
            with open (props_file) as inp:
                props = json.load(inp)
        stable_file_path = os.path.join(engine_folder, props.get('stable', 'stable.wav'))
        self._engine_sound, self.orig_frame_rate = librosa.load(stable_file_path)
        self._engine_sound = self._engine_sound * props.get('init_volume_coef', 1.0)
        self._increasing_engine_sound = None
        self._increase_engine_props: List[IncreaseProps] = list()
        self._decreasing_engine_sound = None
        self._max_speed = 10
        self.log.info("Length {} is {} ms ".format(stable_file_path, len(self._engine_sound)))
        self._limit_max_speed = limit_speed
        self._limit_min_speed = 1.0
        self._engine_state = TEngineState.engine_stable
        self._current_speed = 0
        self._speed_delta = 0.3
        self._pyaudio = pyaudio.PyAudio()
        self._create_increasing_and_decreasing()
        self._audio_buffer = None
        self._play_stream = None

    def set_idling_state(self):
        self._current_speed = self._limit_min_speed
        self._audio_buffer = self._create_stable_at_speed(self._limit_min_speed)

    def start_play_stream(self):
        self.log.debug('start engine sound')
        self.set_idling_state()
        self._play_stream = self._pyaudio.open(
                            format=pyaudio.paFloat32,
                            channels=1,
                            rate=self.orig_frame_rate,
                            output=True,
                            stream_callback=self._gen_audio_callback
                        )

    def get_state(self):
        return self._engine_state

    def get_current_speed(self):
        return round(self._current_speed, 2)
=======
class TOneSpeedSound:
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
        return os.path.join(TOneSpeedSound.segment_folder, 'speed_{}_{}.wav'.format(start_speed, last_speed))

    def __init__(self, start_speed, last_speed):
        self.start_speed = start_speed
        self.last_speed = last_speed
        filename = TOneSpeedSound.get_file_name(self.start_speed, self.last_speed)
        self._sound = pygame.mixer.Sound(filename)
        self.filename = filename

    def get_mixer_sound(self):
        return self._sound


class TEngineSound(threading.Thread):
    def __init__(self, logger, max_speed, segment_folder, max_volume=None):
        TOneSpeedSound.segment_folder = segment_folder
        threading.Thread.__init__(self)
        self.logger = logger
        self.daemon = True
        self.max_speed = max_speed
        self.sounds = dict()
        self.stop = False
        self.channel = pygame.mixer.Channel(0)
        self.max_volume = max_volume
        if self.max_volume is not None:
            self.channel.set_volume(self.max_volume)
        self.mixer_sound_to_info = dict()

    def load_sounds(self):
        for i in range(self.max_speed):
            self.sounds[(i, i+1)] = TOneSpeedSound(i, i + 1)
            self.sounds[(i+1, i)] = TOneSpeedSound(i + 1, i)
            self.sounds[(i + 1, i + 1)] = TOneSpeedSound(i + 1, i + 1)

    def start_engine(self):
        self.load_sounds()
        self.start()

    def get_sound_info(self):
        snd = self.channel.get_sound()
        info = self.mixer_sound_to_info.get(snd)
        if info is not None:
            return info
        else:
            if snd is not None:
                self.logger.error("unknown sound in queue")
            return None

    def get_state(self):
        if not self.channel.get_busy():
            return TEngineState.engine_stable
        snd = self.get_sound_info()
        if snd is not None:
            return snd.get_state()
        else:
            return TEngineState.engine_stable

    def is_working(self):
        return self.channel.get_busy()

    def get_current_speed(self):
        if not self.is_working():
            return 0
        info = self.get_sound_info()
        if info is not None:
            spd = info.get_speed()
            #self.logger.info('current speed = {}'.format(spd))
            return spd
        else:
            return 0
>>>>>>> 2ba354f50e1d3ddc26025b49d97e3acfc3794426

    def stop_engine(self):
        if self._play_stream is not None:
            self._play_stream.close()
        self._current_speed = 0

    def _speed_to_frame_index(self, speed):
        l = len(self._increasing_engine_sound)
        index =  int((speed - 1) * l  / self._limit_max_speed)
        if index >= l:
            return l - 1
        return index

    def _get_volume_at_speed(self, speed):
        return self._increase_engine_props[self._speed_to_frame_index(speed)].volume

    def _get_frame_rate_at_speed(self, speed):
        index = self._speed_to_frame_index(speed)
        assert  index < len(self._increase_engine_props)
        return self._increase_engine_props[index].frame_rate

<<<<<<< HEAD
    def _create_increasing_and_decreasing(self):
        incr_segm = list()
        stable = self._engine_sound
        curr_frame_rate = self.orig_frame_rate
        curr_volume = 1.0
        i = 0
        self._increase_engine_props.clear()
        while i < len(stable):
            if (i % 1000) == 0:
                new_frame_rate = int(curr_frame_rate * 0.99)
                curr_volume = curr_volume * 1.01
                stable = librosa.resample(y=stable[i:], orig_sr=curr_frame_rate, target_sr=new_frame_rate)
                curr_frame_rate = new_frame_rate
                i = 0
            incr_segm.append(stable[i] * curr_volume)
            self._increase_engine_props.append(IncreaseProps(curr_frame_rate, curr_volume))
            i += 1
        end_index = int((self._limit_max_speed - 1) * len(incr_segm)  / self._max_speed) + 1
        self._increase_engine_props = self._increase_engine_props[:end_index]
        incr_segm = incr_segm[:end_index]
        self._increasing_engine_sound = np.array(incr_segm, dtype=np.float32)
        self._decreasing_engine_sound = np.ascontiguousarray(np.flip(self._increasing_engine_sound))

    def _create_stable_at_speed(self, speed):
        segm = self._engine_sound[:]
        volume = self._get_volume_at_speed(speed)
        segm = segm * volume
        frame_rate = self._get_frame_rate_at_speed(speed)
        segm = librosa.resample(y=segm, orig_sr=self.orig_frame_rate, target_sr=frame_rate)
        self.log.debug("_create_stable speed = {}, volume={}, time rate ={} ".format(
            speed, volume, frame_rate))
        return segm

    def _get_increasing_at_speed(self, speed):
        index = self._speed_to_frame_index(speed)
        p = self._increase_engine_props[index]
        self.log.debug("_get_increasing_at_speed speed = {}, index={}, frame_rate={}".format(speed, index, p.frame_rate))
        return self._increasing_engine_sound[index:]

    def _get_decreasing_at_speed(self, speed):
        index = len(self._decreasing_engine_sound) - self._speed_to_frame_index(speed)
        p = self._increase_engine_props[index]
        self.log.debug("_get_increasing_at_speed speed = {}, index={}, frame_rate={}".format(
            speed, index, p.frame_rate))
        return self._decreasing_engine_sound[index:]

    def _create_sound(self, speed):
        if self._engine_state == TEngineState.engine_stable:
            return self._create_stable_at_speed(speed)
        elif self._engine_state == TEngineState.engine_increase:
            return self._get_increasing_at_speed(speed)
=======
    def queue_sound(self, snd: TOneSpeedSound):
        self.logger.info("queue sound {} {} ".format(snd.start_speed, snd.last_speed))
        #_snd = pygame.mixer.Sound(snd)
        self.channel.queue(snd.get_mixer_sound())
        self.mixer_sound_to_info[snd.get_mixer_sound()] = snd

    def play_sound(self, snd: TOneSpeedSound):
        self.logger.debug("play sound {} {} ".format(snd.start_speed, snd.last_speed))
        self.channel.play(snd.get_mixer_sound())
        self.mixer_sound_to_info[snd.get_mixer_sound()] = snd

    def queue_sound_after(self, snd: TOneSpeedSound):
        state = snd.get_state()
        speed = snd.get_speed()
        #self.logger.debug("state = {}".format(state))
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
>>>>>>> 2ba354f50e1d3ddc26025b49d97e3acfc3794426
        else:
            return self._get_decreasing_at_speed(speed)

<<<<<<< HEAD
    def _gen_audio_callback(self, in_data, frame_count, time_info, status):
#        self.log.debug("gen_audio_callback speed={}".format(self._current_speed))
        if self._current_speed == 0:
            return np.zeros( (frame_count,), dtype=np.float32)
        if len(self._audio_buffer) < frame_count:
            if self._engine_state == TEngineState.engine_increase:
                self._engine_state = TEngineState.engine_stable
                s = self._create_stable_at_speed(self._limit_max_speed)
                self._current_speed = self._limit_max_speed
            elif self._engine_state == TEngineState.engine_decrease:
                self._engine_state = TEngineState.engine_stable
                s = self._create_stable_at_speed(self._limit_min_speed)
                self._current_speed = self._limit_min_speed
            else:
                s = self._create_stable_at_speed(self._current_speed)
            self._audio_buffer = np.append(self._audio_buffer, s)
=======
    def run(self):
        while not self.stop:
            if self.channel.get_busy():
                snd = self.get_sound_info()
                if snd is not None:
                    #self.logger.debug('now playing {}'.format(snd.filename))
                    if self.channel.get_queue() is None:
                        self.queue_sound_after(snd)
>>>>>>> 2ba354f50e1d3ddc26025b49d97e3acfc3794426

        buf = self._audio_buffer[:frame_count]
        self._audio_buffer = self._audio_buffer[frame_count:]
        return buf,pyaudio.paContinue

    def _can_increase(self):
        return self._current_speed < self._limit_max_speed

    def _can_decrease(self):
        return self._current_speed > self._limit_min_speed

    def stabilize_speed(self):
        if self._engine_state != TEngineState.engine_stable:
            self._engine_state = TEngineState.engine_stable
            self._audio_buffer = self._create_sound(self._current_speed)

    def increase_speed(self):
<<<<<<< HEAD
        if self._can_increase():
            if self._engine_state != TEngineState.engine_increase:
                self._engine_state = TEngineState.engine_increase
                self._audio_buffer = self._create_sound(self._current_speed)
            self._current_speed = min(self._limit_max_speed, self._current_speed + self._speed_delta)
            self.log.debug("increase speed to {}".format(self._current_speed))

    def decrease_speed(self):
        if self._can_decrease():
            if self._engine_state != TEngineState.engine_decrease:
                self._engine_state = TEngineState.engine_decrease
                self._audio_buffer = self._create_sound(self._current_speed)
            self._current_speed = max(self._limit_min_speed, self._current_speed - self._speed_delta)
            self.log.debug("decrease speed to {}".format(self._current_speed))
=======
        if self.get_state() != TEngineState.engine_increase:
            speed = self.get_current_speed()
            self.logger.debug("speed = {}".format(speed))
            self.load_sounds()
            if speed != self.max_speed:
                self.play_sound(self.get_increase_sound(speed))

    def decrease_speed(self):
        if self.is_working():

            if self.get_state() != TEngineState.engine_decrease:
                speed = self.get_current_speed()
                if speed > 0:
                    self.play_sound(self.get_decrease_sound(speed-1))

    def create_sound_segments_from_engine_increasing_file(self, input, segment_time):
        if not os.path.exists(TOneSpeedSound.segment_folder):
            self.logger.debug("create {}".format(TOneSpeedSound.segment_folder))
            os.mkdir(TOneSpeedSound.segment_folder)

        format = 'wav'
        assert input.endswith(format)
        song = AudioSegment.from_wav(input)
        assert self.max_speed * segment_time < song.duration_seconds
        for speed in range(self.max_speed):
            offset = segment_time * speed
            increasing = song[offset*1000:(offset+segment_time)*1000]
            increasing.export(TOneSpeedSound.get_file_name(speed, speed + 1), format=format)
            decreasing = increasing.reverse().set_channels(1)
            decreasing.export(TOneSpeedSound.get_file_name(speed + 1, speed), format=format)
            stable = (increasing[-1500:] + decreasing[:1500]) * 10
            stable = stable.set_channels(1)
            stable.export(TOneSpeedSound.get_file_name(speed + 1, speed + 1), format=format)
        self.logger.info("all done")

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
                self.logger.debug("got escape key")
                self.stop = True
                self.join(2)
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
    from utils.logging_wrapper import setup_logging
    logger = setup_logging("test_sound")

    pygame.mixer.init()
    args = parse_args()
    sound = TEngineSound(logger, max_speed=args.speed_count, segment_folder=args.segment_folder)
    if args.action == "test":
        sound.test_engine()
    elif args.action == "prepare":
        sound.create_sound_segments_from_engine_increasing_file(args.input, 2)
    else:
        raise Exception("unknown action")


if __name__ == '__main__':
    main()

>>>>>>> 2ba354f50e1d3ddc26025b49d97e3acfc3794426
