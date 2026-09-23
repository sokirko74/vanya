package com.example.vanina_tesla

import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioTrack
import android.os.Handler
import android.os.Looper
import kotlin.math.sin

class Beeper(
    private val baseFrequencyHz: Int = 1000, // Базовая частота синусоиды
    private val sampleRate: Int = 44100
) {
    enum class Mode {
        SILENT,
        BEEPING_PULSED,
        BEEPING_CONTINUOUS
    }

    private var audioTrack: AudioTrack? = null
    private val handler = Handler(Looper.getMainLooper())

    @Volatile var currentMode: Mode = Mode.SILENT
        private set

    private var isBeepOn = false
    private var pulseIntervalMs: Long = 200

    private val pulseRunnable = object : Runnable {
        override fun run() {
            if (currentMode != Mode.BEEPING_PULSED) return

            if (isBeepOn) {
                stopNativeBeep()
                isBeepOn = false
                handler.postDelayed(this, pulseIntervalMs)
            } else {
                startNativeBeep()
                isBeepOn = true
                handler.postDelayed(this, pulseIntervalMs)
            }
        }
    }

    init {
        initAudioTrack()
    }

    private fun initAudioTrack() {
        val numSamples = sampleRate / 10 // 100 мс сэмпл
        val pcmBuffer = ShortArray(numSamples)

        for (i in 0 until numSamples) {
            val angle = 2.0 * Math.PI * i * baseFrequencyHz / sampleRate
            pcmBuffer[i] = (sin(angle) * (Short.MAX_VALUE / 2)).toInt().toShort()
        }

        val bufferSizeBytes = numSamples * 2

        audioTrack = AudioTrack.Builder()
            .setAudioAttributes(
                AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_ASSISTANCE_SONIFICATION)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                    .build()
            )
            .setAudioFormat(
                AudioFormat.Builder()
                    .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                    .setSampleRate(sampleRate)
                    .setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                    .build()
            )
            .setBufferSizeInBytes(bufferSizeBytes)
            .setTransferMode(AudioTrack.MODE_STATIC)
            .build().apply {
                write(pcmBuffer, 0, pcmBuffer.size)
                setLoopPoints(0, numSamples, -1)
            }
    }

    /**
     * Меняет высоты тона на лету
     */
    /**
     * Меняет высоту тона на лету
     */
    private fun applyFrequency(targetFrequencyHz: Int) {
        audioTrack?.let { track ->
            // Вычисляем новую скорость воспроизведения пропорционально целевой частоте.
            // Допустимый диапазон для Android Audio System: от 8000 Гц до 96000 Гц.
            val newPlaybackRate = (sampleRate.toDouble() * targetFrequencyHz / baseFrequencyHz)
                .toInt()
                .coerceIn(8000, 96000)

            track.playbackRate = newPlaybackRate
        }
    }

    /**
     * 1. Режим: Молчание
     */
    fun setSilent() {
        if (currentMode == Mode.SILENT) return
        currentMode = Mode.SILENT

        handler.removeCallbacks(pulseRunnable)
        stopNativeBeep()
    }

    /**
     * 2. Режим: Прерывистый писк
     * @param intervalMs Интервал между импульсами (мс)
     * @param frequencyHz Высота тона (Гц)
     */
    fun setPulsed(intervalMs: Long = 200, frequencyHz: Int = baseFrequencyHz) {
        this.pulseIntervalMs = intervalMs
        applyFrequency(frequencyHz)

        if (currentMode == Mode.BEEPING_PULSED) return
        currentMode = Mode.BEEPING_PULSED

        handler.removeCallbacks(pulseRunnable)
        stopNativeBeep()

        isBeepOn = false
        handler.post(pulseRunnable)
    }

    /**
     * 3. Режим: Непрерывный писк
     * @param frequencyHz Высота тона (Гц)
     */
    fun setContinuous(frequencyHz: Int = baseFrequencyHz) {
        applyFrequency(frequencyHz)

        if (currentMode == Mode.BEEPING_CONTINUOUS) return
        currentMode = Mode.BEEPING_CONTINUOUS

        handler.removeCallbacks(pulseRunnable)
        startNativeBeep()
    }

    private fun startNativeBeep() {
        audioTrack?.let { track ->
            if (track.state == AudioTrack.STATE_INITIALIZED && track.playState != AudioTrack.PLAYSTATE_PLAYING) {
                track.play()
            }
        }
    }

    private fun stopNativeBeep() {
        audioTrack?.let { track ->
            if (track.playState == AudioTrack.PLAYSTATE_PLAYING) {
                track.pause()
                track.setPlaybackHeadPosition(0)
            }
        }
    }

    fun release() {
        setSilent()
        audioTrack?.release()
        audioTrack = null
    }
}