package com.example.vanina_tesla

import android.animation.ValueAnimator
import android.content.Context
import android.media.AudioAttributes
import android.media.SoundPool
import android.os.Handler
import android.os.Looper
import android.view.animation.LinearInterpolator

class EngineSoundPlayer(
    context: Context,
    rawResId: Int,          // R.raw.stable
    startRawResId: Int      // R.raw.start
) {

    private val soundPool: SoundPool
    private val soundId: Int
    private val startSoundId: Int

    private var streamId: Int = 0
    @Volatile
    var isLoaded = false
        private set
    @Volatile
    var isStartLoaded = false
        private set

    private var currentPitch = 0.8f
    private var currentVol = 0.5f
    private var animator: ValueAnimator? = null
    private val mainHandler = Handler(Looper.getMainLooper())
    @Volatile
    var isMuted = true
        private set

    init {
        val audioAttributes = AudioAttributes.Builder()
            .setUsage(AudioAttributes.USAGE_GAME)
            .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
            .build()

        soundPool = SoundPool.Builder()
            .setMaxStreams(2) // Минимум 2 потока для одновременной/последовательной игры
            .setAudioAttributes(audioAttributes)
            .build()

        soundPool.setOnLoadCompleteListener(::onSoundLoaded)

        // Загружаем оба звуковых файла
        soundId = soundPool.load(context, rawResId, 1)
        startSoundId = soundPool.load(context, startRawResId, 1)
    }

    private fun onSoundLoaded(soundPool: SoundPool, sampleId: Int, status: Int) {
        if (status != 0) return

        if (sampleId == soundId) {
            isLoaded = true
            // Запускаем бесконечный цикл холостого хода с нулевой или текущей громкостью
            streamId = soundPool.play(soundId, currentVol, currentVol, 1, -1, currentPitch)
            adjustVolume()
        } else if (sampleId == startSoundId) {
            isStartLoaded = true
        }
    }

    private fun adjustVolume() {
        if (streamId != 0) {
            val vol = if (isMuted) 0f else currentVol
            soundPool.setVolume(streamId, vol, vol)
        }
    }

    /**
     * Включение / выключение звука.
     * При переходе из Muted (true) -> Unmuted (false) сначала играет звук старта.
     */
    fun setMuted(muted: Boolean) {
        mainHandler.post {
            val wasMuted = isMuted
            isMuted = muted

            if (wasMuted && !isMuted) {
                // Произошел переход из Muted -> Unmuted (Завод двигателя)
                if (isStartLoaded) {
                    // Проигрываем звук запуска 1 раз (loop = 0)
                    soundPool.play(startSoundId, currentVol, currentVol, 2, 0, 1.0f)
                }
                // Включаем основной звук мотора
                adjustVolume()
            } else if (isMuted) {
                // При заглушении мотора мгновенно сбрасываем громкость
                adjustVolume()
            }
        }
    }

    fun updateSpeed(speed: Float, durationMs: Long = 1000L) {
        if (!isLoaded || streamId == 0) return

        mainHandler.post {
            val clampedSpeed = speed.coerceIn(0f, 1f)

            val minPitch = 0.8f
            val maxPitch = 2.2f
            val targetPitch = minPitch + (clampedSpeed * (maxPitch - minPitch))

            val minVol = 0.5f
            val maxVol = 1.0f
            val targetVol = minVol + (clampedSpeed * (maxVol - minVol))

            val startPitch = currentPitch
            val startVol = currentVol

            animator?.cancel()
            animator = ValueAnimator.ofFloat(0f, 1f).apply {
                duration = durationMs
                interpolator = LinearInterpolator()
                addUpdateListener { animation ->
                    val fraction = animation.animatedValue as Float
                    currentPitch = startPitch + fraction * (targetPitch - startPitch)
                    currentVol = startVol + fraction * (targetVol - startVol)

                    soundPool.setRate(streamId, currentPitch)
                    adjustVolume()
                }
                start()
            }
        }
    }

    fun stop() {
        mainHandler.post {
            animator?.cancel()
            if (streamId != 0) {
                soundPool.stop(streamId)
            }
            soundPool.release()
        }
    }
}
