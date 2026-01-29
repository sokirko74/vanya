import numpy as np
import sounddevice as sd
import crepe
import queue
import time

SAMPLE_RATE = 16000   # CREPE ожидает 16 kHz
FRAME_SIZE = 1024     # ~64 ms
audio_q = queue.Queue()

def audio_callback(indata, frames, time_info, status):
    if status:
        print(status)
    audio_q.put(indata.copy())

def main():
    stream = sd.InputStream(
        channels=1,
        samplerate=SAMPLE_RATE,
        blocksize=FRAME_SIZE,
        callback=audio_callback
    )

    with stream:
        print("🎤 Слушаю микрофон...")
        while True:
            audio = audio_q.get().flatten()

            # CREPE ожидает float32 в диапазоне [-1, 1]
            audio = audio.astype(np.float32)
            print(len(audio))
            # predict returns arrays over time
            print("run crepe.predict len(audio) = {} ...".format(len(audio)))
            _, frequency, confidence, _ = crepe.predict(
                audio,
                SAMPLE_RATE,
                viterbi=True,
                step_size=10,  # ms
                verbose=0
            )

            # берём последнюю оценку
            f0 = frequency[-1]
            conf = confidence[-1]
            print("conf = {} ...".format(conf))

            if conf > 0.8 and f0 > 0:
                print(f"🎵 {f0:7.1f} Hz  (conf={conf:.2f})")

if __name__ == "__main__":
    main()