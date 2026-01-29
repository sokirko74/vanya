import sounddevice as sd
import soundfile as sf
import numpy as np

def main():
    DURATION = 3          # секунд
    SAMPLE_RATE = 16000    # ОБЯЗАТЕЛЬНО для CREPE
    CHANNELS = 1
    OUT_FILE = "recording.wav"

    print("🎤 Запись началась...")
    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32"
    )

    sd.wait()
    print("✅ Запись завершена")
    print(audio.shape)
    audio = audio[-2 * SAMPLE_RATE:]
    print(audio.shape)
    sf.write(OUT_FILE, audio, SAMPLE_RATE)
    print(f"💾 Сохранено в {OUT_FILE}")

if __name__ == "__main__":
    main()