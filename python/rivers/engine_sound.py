from pyaudio_wrapper import PyAudioStreamWrapper
from engine_state import TEngineState
import json
import os

import librosa
import numpy as np
from collections import namedtuple
from typing import List


IncreaseProps = namedtuple('IncreaseProps', ['frame_rate', 'volume'])


class TEngineSound:
    def __init__(self, log, engine_folder, limit_speed, sounds):
        self.log = log
        self.sounds = sounds
        props_file = os.path.join(engine_folder, "audio_props.json")
        props = dict()
        if os.path.exists(props_file):
            with open (props_file) as inp:
                props = json.load(inp)
        stable_file_path = os.path.join(engine_folder, props.get('stable', 'stable.wav'))
        self.start_sound_file_path = None
        if 'start' in props:
            self.start_sound_file_path = os.path.join(engine_folder, props['start'])
        if 'idle' in props:
            idle_sound_file_path = os.path.join(engine_folder, props['idle'])
            self._idle_engine_sound, self.idle_frame_rate = librosa.load(idle_sound_file_path)
        else:
            self.idle_sound_file_path = None
            self._idle_engine_sound = None
            self.idle_frame_rate = None

        self._engine_sound, self.orig_frame_rate = librosa.load(stable_file_path)
        self._engine_sound = self._engine_sound * props.get('init_volume_coef', 1.0)
        self._stable_speed_cache = dict()
        self._increasing_engine_sound = None
        self._increase_engine_props: List[IncreaseProps] = list()
        self._decreasing_engine_sound = None
        self._max_speed = 10
        self.log.info("limit_speed = {}, Length {} is {} ms ".format(
            limit_speed, stable_file_path, len(self._engine_sound)))
        self.idle_speed = 1.0
        self.limit_max_speed = limit_speed
        self._engine_state = TEngineState.engine_stable
        self._current_speed = 0
        self._create_increasing_and_decreasing()
        self._play_stream = None
        self._save_prev_speed_debug = 0

    def set_idling_state(self):
        self._current_speed = self.idle_speed
        self._create_sound(self.idle_speed)

    def start_play_stream(self):
        self.log.debug('start engine sound')
        self._play_stream = PyAudioStreamWrapper(self, self.orig_frame_rate)
        self.set_idling_state()
        self._play_stream.start_stream()

    def get_state(self):
        return self._engine_state

    def get_current_speed(self):
        return round(self._current_speed, 2)

    def stop_engine(self):
        if self._play_stream is not None and self._play_stream.is_alive():
            self._play_stream.stop = True
            self._play_stream.join(2)
            self._play_stream = None
        self._current_speed = 0

    def _speed_to_frame_index(self, speed):
        l = len(self._increasing_engine_sound)
        index =  int((speed - 1) * l / self.limit_max_speed)
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
        end_index = int((self.limit_max_speed - 1) * len(incr_segm) / self._max_speed) + 1
        self._increase_engine_props = self._increase_engine_props[:end_index]
        self._increasing_engine_sound = np.array(incr_segm[:end_index], dtype=np.float32)
        self._decreasing_engine_sound = np.ascontiguousarray(np.flip(self._increasing_engine_sound))
        assert len(self._increasing_engine_sound) == len(self._increasing_engine_sound)

    def _get_idle_sound(self):
        if self._idle_engine_sound is not None:
            return self._idle_engine_sound
        else:
            return self._engine_sound

    def _create_stable_at_speed(self, speed):
        if speed == self.idle_speed:
            return self._get_idle_sound()
        cached_frames = self._stable_speed_cache.get(speed)
        if cached_frames is not None:
            return cached_frames
        segm = self._engine_sound[:]
        volume = self._get_volume_at_speed(speed)
        segm = segm * volume
        frame_rate = self._get_frame_rate_at_speed(speed)
        segm = librosa.resample(y=segm, orig_sr=self.orig_frame_rate, target_sr=frame_rate)
        self.log.debug("_create_stable speed = {}, volume={}, time rate ={} ".format(
            speed, volume, frame_rate))
        self._stable_speed_cache[speed] = segm
        return segm

    def _get_increasing_at_speed(self, speed):
        index = self._speed_to_frame_index(speed)
        p = self._increase_engine_props[index]
        self.log.debug("_get_increasing_at_speed speed = {}, index={}, frame_rate={}".format(speed, index, p.frame_rate))
        return self._increasing_engine_sound[index:]

    def _get_decreasing_at_speed(self, speed):
        index = len(self._decreasing_engine_sound) - self._speed_to_frame_index(speed)
        if index >= len(self._increase_engine_props):
            index = len(self._increase_engine_props) - 1
        p = self._increase_engine_props[index]
        self.log.debug("_get_increasing_at_speed speed = {}, index={}, frame_rate={}".format(
            speed, index, p.frame_rate))
        return self._decreasing_engine_sound[index:]

    def _create_sound(self, speed):
        try:
            if self._engine_state == TEngineState.engine_stable:
                if self._idle_engine_sound is not None:
                    s = self._get_idle_sound()
                else:
                    s = self._create_stable_at_speed(speed)
            elif self._engine_state == TEngineState.engine_increase:
                s = self._get_increasing_at_speed(speed)
            else:
                s = self._get_decreasing_at_speed(speed)
            self._play_stream.set_audio_buffer(s)
        except IndexError as exp:
            self.log.debug("unknown exception {}, speed = {}, fix me in 2024".format(exp, speed))

    def _can_increase(self):
        return self._current_speed < self.limit_max_speed

    def _can_decrease(self):
        return self._current_speed > self.idle_speed

    def _stabilize_speed(self):
        if self._engine_state != TEngineState.engine_stable:
            self.log.debug("switch to stable state")
            self._engine_state = TEngineState.engine_stable
            self._create_sound(self._current_speed)

    def increase_speed(self):
        if self._can_increase():
            if self._engine_state != TEngineState.engine_increase:
                self._engine_state = TEngineState.engine_increase
                self.log.debug("switch to increasing state")
                self._create_sound(self._current_speed)

    def decrease_speed(self):
        if self._can_decrease():
            if self._engine_state != TEngineState.engine_decrease:
                self._engine_state = TEngineState.engine_decrease
                self.log.debug("switch to decreasing state")
                self._create_sound(self._current_speed)

    def update_speed(self):
        if self._engine_state == TEngineState.engine_stable:
            return
        left_frames = len(self._play_stream.get_audio_buffer())
        all_frames = len(self._increase_engine_props)
        self._current_speed = (self.limit_max_speed - self.idle_speed) * (all_frames - left_frames) / all_frames + self.idle_speed
        if self._save_prev_speed_debug != self._current_speed:
            self.log.debug('change engine speed from {} to {}'.format(self._save_prev_speed_debug, self._current_speed))
        self._save_prev_speed_debug = self._current_speed

    def get_new_frames(self):
        if self._engine_state == TEngineState.engine_increase:
            self._engine_state = TEngineState.engine_stable
            self._current_speed = self.limit_max_speed
            return self._create_stable_at_speed(self.limit_max_speed)
        elif self._engine_state == TEngineState.engine_decrease:
            self._engine_state = TEngineState.engine_stable
            self._current_speed = self.idle_speed
            return self._create_stable_at_speed(self.idle_speed)
        else:
            return self._create_stable_at_speed(self._current_speed)

