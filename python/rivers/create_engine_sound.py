#https://wav-library.net/avto-ford-escort-uskorenie-bystroe-zvuk

import os
import argparse
from pydub import AudioSegment


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-audio", dest='input')
    parser.add_argument("--duration", dest='duration', type=int, default=20)
    parser.add_argument("--increase-decrease-segment", dest='id_segment', type=int, default=2)
    parser.add_argument("--output-folder", dest='output_folder')
    return parser.parse_args()


def split_engine(input, segment_time):
    if input.endswith('.wav'):
        format = 'wav'
        song = AudioSegment.from_wav(input)
    elif input.endswith('.mp3'):
        format = 'mp3'
        song = AudioSegment.from_mp3(input)
    elif input.endswith('.ogg'):
        format = 'ogg'
        song = AudioSegment.from_ogg(input)
    assert song is not None
    print("format = {}".format(format))
    for speed in range(10):
        offset = segment_time * speed
        increase_path = "speed_{}_{}.{}".format(speed, speed+1, format)
        decrease_path = "speed_{}_{}.{}".format(speed + 1, speed, format)
        segment = song[offset*1000:(offset+segment_time)*1000]
        segment.export(increase_path, format=format)
        reverse_segment = segment.reverse().set_channels(1)
        reverse_segment.export(decrease_path, format=format)
        stable = (segment[-1500:] + reverse_segment[:1500]) * 10
        stable = stable.set_channels(1)
        stable.export('speed_{}_{}.{}'.format(speed+1, speed+1, format), format=format)


def main():
    args = parse_args()
    assert os.path.exists(args.input)
    input = os.path.abspath(args.input)

    if not os.path.exists(args.output_folder):
        print("create {}".format(args.output_folder))
        os.mkdir(args.output_folder)
    os.chdir(args.output_folder)

    split_engine(input, args.id_segment)
    print ("all done")

#rm -rf assets/sounds/ford; python3 create_engine_sound.py  --input assets/sounds/engine_increase.wav --output-folder assets/sounds/ford/
if __name__ == "__main__":
    main()
