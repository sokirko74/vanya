package com.example.vanina_tesla

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class JoystickCalibrationTest {

    @Test
    fun testDirectionConfigPositiveAxis() {
        // Forward: axis Y, neutralEdge = 550, maxEdge = 850
        val config = DirectionConfig(axis = 'Y', neutralEdge = 550, maxEdge = 850)

        // Inside deadzone
        assertEquals(0f, config.calculateSpeed(rawX = 512, rawY = 512), 0.001f)
        assertEquals(0f, config.calculateSpeed(rawX = 512, rawY = 550), 0.001f)

        // Halfway
        assertEquals(0.5f, config.calculateSpeed(rawX = 512, rawY = 700), 0.001f)

        // Full max and beyond
        assertEquals(1.0f, config.calculateSpeed(rawX = 512, rawY = 850), 0.001f)
        assertEquals(1.0f, config.calculateSpeed(rawX = 512, rawY = 900), 0.001f)
    }

    @Test
    fun testDirectionConfigNegativeAxis() {
        // Backward: axis Y, neutralEdge = 450, maxEdge = 150
        val config = DirectionConfig(axis = 'Y', neutralEdge = 450, maxEdge = 150)

        // Inside deadzone
        assertEquals(0f, config.calculateSpeed(rawX = 512, rawY = 512), 0.001f)
        assertEquals(0f, config.calculateSpeed(rawX = 512, rawY = 450), 0.001f)

        // Halfway
        assertEquals(0.5f, config.calculateSpeed(rawX = 512, rawY = 300), 0.001f)

        // Full max and beyond
        assertEquals(1.0f, config.calculateSpeed(rawX = 512, rawY = 150), 0.001f)
        assertEquals(1.0f, config.calculateSpeed(rawX = 512, rawY = 50), 0.001f)
    }

    @Test
    fun testJoystickCombinedSpeed() {
        val calib = JoystickCalibration(
            isCalibrated = true,
            neutralX = 500,
            neutralY = 500,
            forward = DirectionConfig('Y', neutralEdge = 550, maxEdge = 850),
            backward = DirectionConfig('Y', neutralEdge = 450, maxEdge = 150),
            right = DirectionConfig('X', neutralEdge = 550, maxEdge = 850),
            left = DirectionConfig('X', neutralEdge = 450, maxEdge = 150)
        )

        // At neutral: speed must be 0
        assertEquals(0f, calib.calculateSpeed(500, 500), 0.001f)
        assertEquals(0f, calib.calculateSpeed(520, 480), 0.001f)

        // Only forward full: speed = 1.0
        assertEquals(1.0f, calib.calculateSpeed(500, 850), 0.001f)

        // Only left full: speed = 1.0
        assertEquals(1.0f, calib.calculateSpeed(150, 500), 0.001f)

        // Diagonal: forward 0.5, right 0.5 -> sqrt(0.25 + 0.25) = sqrt(0.5) ≈ 0.707
        val diagSpeed = calib.calculateSpeed(700, 700)
        assertEquals(0.7071f, diagSpeed, 0.01f)
    }

    @Test
    fun testQuickZero() {
        val calib = JoystickCalibration(
            isCalibrated = true,
            neutralX = 500,
            neutralY = 500,
            forward = DirectionConfig('Y', neutralEdge = 550, maxEdge = 850),
            backward = DirectionConfig('Y', neutralEdge = 450, maxEdge = 150),
            right = DirectionConfig('X', neutralEdge = 550, maxEdge = 850),
            left = DirectionConfig('X', neutralEdge = 450, maxEdge = 150)
        )

        // Suppose next day at power on, neutral is measured as X = 520, Y = 490
        calib.quickZero(520, 490)

        assertEquals(520, calib.neutralX)
        assertEquals(490, calib.neutralY)

        // Forward (Y): deltaY = -10. neutralEdge: 550 - 10 = 540, max: 850 - 10 = 840
        assertEquals(540, calib.forward.neutralEdge)
        assertEquals(840, calib.forward.maxEdge)

        // Right (X): deltaX = +20. neutralEdge: 550 + 20 = 570, max: 850 + 20 = 870
        assertEquals(570, calib.right.neutralEdge)
        assertEquals(870, calib.right.maxEdge)

        // At the new neutral, speed must be 0
        assertEquals(0f, calib.calculateSpeed(520, 490), 0.001f)
    }
}
