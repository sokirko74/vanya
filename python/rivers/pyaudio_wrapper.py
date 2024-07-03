import time
import threading
import numpy as np
import pyaudio


class PyAudioStreamWrapper(threading.Thread):
    def __init__(self, parent, frame_rate, frames_per_buffer=4096):
        super().__init__()
        self._parent = parent
        self._pyaudio = pyaudio.PyAudio()
        self._audio_buffer = None
        self._frame_rate = frame_rate
        self.stop = False
        self.frames_per_buffer = frames_per_buffer

    def start_stream(self):
        self.start()

    def set_audio_buffer(self, buffer):
        self._audio_buffer = buffer

    def get_audio_buffer(self):
        return self._audio_buffer

    def pop_frames(self, frame_count):
        buf = self._audio_buffer[:frame_count]
        self._audio_buffer = self._audio_buffer[frame_count:]
        return buf

    def _gen_audio_callback(self, in_data, frame_count, time_info, status):
        if self._parent.get_current_speed() == 0:
            return np.zeros( (frame_count,), dtype=np.float32)
        elif len(self.get_audio_buffer()) < frame_count:
            s = self._parent.get_new_frames()
            self._audio_buffer = np.append(self._audio_buffer, s)
        return self.pop_frames(frame_count), pyaudio.paContinue

    def run(self):
        play_stream = self._pyaudio.open(
                            format=pyaudio.paFloat32,
                            channels=1,
                            rate=self._frame_rate,
                            output=True,
                            stream_callback=self._gen_audio_callback,
                            frames_per_buffer=self.frames_per_buffer
                        )
        while not self.stop and play_stream.is_active():
            self._parent.update_speed()
            time.sleep(0.1)

        play_stream.close()

