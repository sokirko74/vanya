package com.example.vanina_tesla

import android.animation.ValueAnimator
import android.content.Context
import android.media.AudioAttributes
import android.media.SoundPool
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.animation.LinearInterpolator

import android.media.MediaMetadataRetriever
import android.net.Uri

private fun getRawResourceDurationMs(context: Context, rawResId: Int): Long {
    val retriever = MediaMetadataRetriever()
    return try {
        // Формируем URI ресурса res/raw/engine_start.wav
        val uri = Uri.parse("android.resource://${context.packageName}/$rawResId")
        retriever.setDataSource(context, uri)

        // Получаем длительность в миллисекундах
        val durationStr = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)
        durationStr?.toLongOrNull() ?: 1000L // 1000L как дефолтное значение, если не удалось распарсить
    } catch (e: Exception) {
        1000L
    } finally {
        retriever.release()
    }
}

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
    private var isStarting = false
    @Volatile
    var isMuted = true
        private set

    private val startSoundDurationMs: Long = getRawResourceDurationMs(context, startRawResId)

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
    private fun log(message: String) {
        Log.d("WheelchairTest", message)
    }
    private fun adjustVolume() {
        if (streamId != 0) {
            // Если звук замучен ИЛИ прямо сейчас идет запуск двигателя — громкость stable должна быть 0
            val vol = if (isMuted || isStarting) 0f else currentVol
            log("adjustVolume isMuted=$isMuted isStarting=$isStarting currentVol=$currentVol -> setVol=$vol")
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
                if (isStartLoaded) {
                    log("soundPool.play(startSoundId)")
                    isStarting = true // Включаем режим старта
                    soundPool.play(startSoundId, 1.0F, 1.0F, 2, 0, 1.0f)
                }

                // Убираем старые отложенные вызовы, если они были
                mainHandler.removeCallbacksAndMessages(null)

                mainHandler.postDelayed({
                    isStarting = false // Старт завершен
                    if (!isMuted) {
                        adjustVolume() // Вот теперь включаем stable!
                    }
                }, startSoundDurationMs)

            } else if (isMuted) {
                isStarting = false
                mainHandler.removeCallbacksAndMessages(null)
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
