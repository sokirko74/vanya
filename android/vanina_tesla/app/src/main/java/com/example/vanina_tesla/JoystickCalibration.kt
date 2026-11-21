package com.example.vanina_tesla

import android.content.SharedPreferences
import kotlin.math.sqrt

/**
 * Конфигурация для одного направления движения джойстика.
 * @param axis Ось джойстика ('X' или 'Y')
 * @param neutralEdge Граница нейтрали (порог срабатывания, за пределами которого скорость > 0)
 * @param maxEdge Значение АЦП при максимальном физическом отклонении джойстика (скорость = 1.0)
 */
data class DirectionConfig(
    val axis: Char = 'Y',
    val neutralEdge: Int = 542,
    val maxEdge: Int = 850
) {
    /**
     * Вычисляет скорость для данного направления в диапазоне [0.0..1.0].
     */
    fun calculateSpeed(rawX: Int, rawY: Int): Float {
        val v = if (axis == 'X') rawX else rawY
        return if (maxEdge > neutralEdge) {
            // Движение увеличивает значение АЦП
            when {
                v <= neutralEdge -> 0f
                v >= maxEdge -> 1f
                else -> (v - neutralEdge).toFloat() / (maxEdge - neutralEdge).toFloat()
            }
        } else if (maxEdge < neutralEdge) {
            // Движение уменьшает значение АЦП
            when {
                v >= neutralEdge -> 0f
                v <= maxEdge -> 1f
                else -> (neutralEdge - v).toFloat() / (neutralEdge - maxEdge).toFloat()
            }
        } else {
            0f
        }
    }
}

/**
 * Хранилище настроек калибровки джойстика для всех 4 направлений.
 */
data class JoystickCalibration(
    var isCalibrated: Boolean = false,
    var neutralX: Int = 512,
    var neutralY: Int = 512,
    var deadzoneX: Int = 30,
    var deadzoneY: Int = 30,
    var forward: DirectionConfig = DirectionConfig('Y', 542, 850),
    var right: DirectionConfig = DirectionConfig('X', 542, 850),
    var backward: DirectionConfig = DirectionConfig('Y', 482, 150),
    var left: DirectionConfig = DirectionConfig('X', 482, 150)
) {
    /**
     * Вычисляет результирующую скорость коляски от 0.0 до 1.0 на основе (rawX, rawY).
     */
    fun calculateSpeed(rawX: Int, rawY: Int): Float {
        if (rawX < 0 || rawY < 0) return 0f

        val sFwd = forward.calculateSpeed(rawX, rawY)
        val sBwd = backward.calculateSpeed(rawX, rawY)
        val sRight = right.calculateSpeed(rawX, rawY)
        val sLeft = left.calculateSpeed(rawX, rawY)

        val sLongitudinal = maxOf(sFwd, sBwd)
        val sLateral = maxOf(sRight, sLeft)

        // Векторная длина (эвклидова норма), чтобы при движении по диагонали (вперед+вбок)
        // скорость оставалась плавной и не превышала 1.0
        val combined = sqrt(sLongitudinal * sLongitudinal + sLateral * sLateral)
        return combined.coerceIn(0f, 1f)
    }

    /**
     * Быстрый сброс нейтрали (Quick Zero).
     * Сдвигает центр и все границы на величину смещения покоя при включении,
     * сохраняя измеренный размах (ход) джойстика.
     */
    fun quickZero(currentRawX: Int, currentRawY: Int) {
        if (currentRawX < 0 || currentRawY < 0) return
        val deltaX = currentRawX - neutralX
        val deltaY = currentRawY - neutralY

        neutralX = currentRawX
        neutralY = currentRawY

        forward = shiftConfig(forward, deltaX, deltaY)
        right = shiftConfig(right, deltaX, deltaY)
        backward = shiftConfig(backward, deltaX, deltaY)
        left = shiftConfig(left, deltaX, deltaY)
    }

    private fun shiftConfig(config: DirectionConfig, deltaX: Int, deltaY: Int): DirectionConfig {
        val shift = if (config.axis == 'X') deltaX else deltaY
        return config.copy(
            neutralEdge = config.neutralEdge + shift,
            maxEdge = config.maxEdge + shift
        )
    }

    fun saveToPrefs(prefs: SharedPreferences) {
        prefs.edit().apply {
            putBoolean("joystick_is_calibrated", isCalibrated)
            putInt("joystick_neutral_x", neutralX)
            putInt("joystick_neutral_y", neutralY)
            putInt("joystick_deadzone_x", deadzoneX)
            putInt("joystick_deadzone_y", deadzoneY)

            putString("joystick_fwd_axis", forward.axis.toString())
            putInt("joystick_fwd_neutral", forward.neutralEdge)
            putInt("joystick_fwd_max", forward.maxEdge)

            putString("joystick_right_axis", right.axis.toString())
            putInt("joystick_right_neutral", right.neutralEdge)
            putInt("joystick_right_max", right.maxEdge)

            putString("joystick_bwd_axis", backward.axis.toString())
            putInt("joystick_bwd_neutral", backward.neutralEdge)
            putInt("joystick_bwd_max", backward.maxEdge)

            putString("joystick_left_axis", left.axis.toString())
            putInt("joystick_left_neutral", left.neutralEdge)
            putInt("joystick_left_max", left.maxEdge)
            apply()
        }
    }

    companion object {
        fun loadFromPrefs(prefs: SharedPreferences): JoystickCalibration {
            val isCalibrated = prefs.getBoolean("joystick_is_calibrated", false)
            val neutralX = prefs.getInt("joystick_neutral_x", 512)
            val neutralY = prefs.getInt("joystick_neutral_y", 512)
            val deadzoneX = prefs.getInt("joystick_deadzone_x", 30)
            val deadzoneY = prefs.getInt("joystick_deadzone_y", 30)

            val fwdAxis = (prefs.getString("joystick_fwd_axis", "Y") ?: "Y").firstOrNull() ?: 'Y'
            val fwdNeutral = prefs.getInt("joystick_fwd_neutral", neutralY + deadzoneY)
            val fwdMax = prefs.getInt("joystick_fwd_max", 850)

            val rightAxis = (prefs.getString("joystick_right_axis", "X") ?: "X").firstOrNull() ?: 'X'
            val rightNeutral = prefs.getInt("joystick_right_neutral", neutralX + deadzoneX)
            val rightMax = prefs.getInt("joystick_right_max", 850)

            val bwdAxis = (prefs.getString("joystick_bwd_axis", "Y") ?: "Y").firstOrNull() ?: 'Y'
            val bwdNeutral = prefs.getInt("joystick_bwd_neutral", neutralY - deadzoneY)
            val bwdMax = prefs.getInt("joystick_bwd_max", 150)

            val leftAxis = (prefs.getString("joystick_left_axis", "X") ?: "X").firstOrNull() ?: 'X'
            val leftNeutral = prefs.getInt("joystick_left_neutral", neutralX - deadzoneX)
            val leftMax = prefs.getInt("joystick_left_max", 150)

            return JoystickCalibration(
                isCalibrated = isCalibrated,
                neutralX = neutralX,
                neutralY = neutralY,
                deadzoneX = deadzoneX,
                deadzoneY = deadzoneY,
                forward = DirectionConfig(fwdAxis, fwdNeutral, fwdMax),
                right = DirectionConfig(rightAxis, rightNeutral, rightMax),
                backward = DirectionConfig(bwdAxis, bwdNeutral, bwdMax),
                left = DirectionConfig(leftAxis, leftNeutral, leftMax)
            )
        }
    }
}
