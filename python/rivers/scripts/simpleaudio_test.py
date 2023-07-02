import simpleaudio
import os
import time

from pydub import AudioSegment
import  pydub.playback


def play_simple_audio(sound):
    return  simpleaudio.play_buffer(
        sound.raw_data,
        num_channels=sound.channels,
        bytes_per_sample=sound.sample_width,
        sample_rate=sound.frame_rate
    )

def main():
    file_path = os.path.join(os.path.dirname(__file__), '../assets/sounds/engine_increase.wav')
    sound = AudioSegment.from_file(file_path, format="wav")[3000:6000]
    play_obj = play_simple_audio(sound)
    play_obj.wait_done()
    play_obj = play_simple_audio(sound.reverse())
    play_obj.wait_done()

    # wave_obj = simpleaudio.WaveObject.from_wave_file(file_path)
    # play_obj = wave_obj.play()
    # time.sleep(2)
    # play_obj.stop()

    # snd = pygame.mixer.Sound(file_path)
    # l = snd.get_length()
    # snd.play(start=10.5)
    # pygame.mixer.music.load(file_path)
    # pygame.mixer.music.play()
    # time.sleep(2)
    # pygame.mixer.music.pause()
    # pygame.mixer.music.set_pos(20.0)
    # pygame.mixer.music.play(start=10.5`)
    #time.sleep(5)


if __name__ == '__main__':
    main()