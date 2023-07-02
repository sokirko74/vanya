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
        else:
            return self._get_decreasing_at_speed(speed)

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
