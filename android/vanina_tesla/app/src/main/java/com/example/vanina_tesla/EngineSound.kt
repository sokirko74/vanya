package com.example.vanina_tesla

import android.animation.ValueAnimator
import android.content.Context
import android.media.AudioAttributes
import android.media.SoundPool
import android.os.Handler
import android.os.Looper
import android.view.animation.LinearInterpolator

class EngineSoundPlayer(context: Context, rawResId: Int) {

    private val soundPool: SoundPool
    private val soundId: Int
    private var streamId: Int = 0
    private var isLoaded = false
    private var currentPitch = 0.8f
    private var currentVol = 0.5f
    private var animator: ValueAnimator? = null
    private val mainHandler = Handler(Looper.getMainLooper())
    private var isMuted = true
    init {
        val audioAttributes = AudioAttributes.Builder()
            .setUsage(AudioAttributes.USAGE_GAME)
            .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
            .build()

        soundPool = SoundPool.Builder()
            .setMaxStreams(1)
            .setAudioAttributes(audioAttributes)
            .build()

        // Загружаем stable.wav из папки res/raw/
        soundId = soundPool.load(context, rawResId, 1)

        soundPool.setOnLoadCompleteListener { _, sampleId, status ->
            if (status == 0 && sampleId == soundId) {
                isLoaded = true
                startEngine()
            }
        }
    }

    private fun adjustVolume() {
        val vol = if (isMuted) 0f else currentVol
        soundPool.setVolume(streamId, vol, vol)
    }
    private fun startEngine() {
        if (!isLoaded) return
        // Запускаем зацикленное воспроизведение (-1 = бесконечный цикл)
        // rate = 0.8f (базовая частота холостого хода)
        streamId = soundPool.play(soundId, currentVol, currentVol, 1, -1, currentPitch)
        adjustVolume()
    }

    /**
     * Вызывать при изменении положения джойстика/скорости.
     * @param speed Значение от 0.0f (нейтраль) до 1.0f (полный газ)
     */
    fun updateSpeed(speed: Float, durationMs: Long = 1000L) {
        if (!isLoaded || streamId == 0) return

        mainHandler.post {
            val clampedSpeed = speed.coerceIn(0f, 1f)

            // 1. Изменяем Pitch (высоту тона / скорость проигрывания):
            // 0.0 -> 0.8x (басовитый холостой ход)
            // 1.0 -> 2.2x (высокие обороты)
            val minPitch = 0.8f
            val maxPitch = 2.2f
            //val currentPitch = minPitch + (clampedSpeed * (maxPitch - minPitch))
            val targetPitch = minPitch + (clampedSpeed * (maxPitch - minPitch))

            // 2. Изменяем Громкость (под нагрузкой мотор звучит громче):
            val minVol = 0.5f
            val maxVol = 1.0f
            //val currentVol = minVol + (clampedSpeed * (maxVol - minVol))
            val targetVol = minVol + (clampedSpeed * (maxVol - minVol))

            // Применяем настройки к играющему потоку в реальном времени
            //soundPool.setRate(streamId, currentPitch)
            //soundPool.setVolume(streamId, currentVol, currentVol)
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
    fun setMuted(muted: Boolean) {
        mainHandler.post {
            isMuted = muted
            if (streamId != 0) {
                val vol = if (isMuted) 0f else currentVol
                soundPool.setVolume(streamId, vol, vol)
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


