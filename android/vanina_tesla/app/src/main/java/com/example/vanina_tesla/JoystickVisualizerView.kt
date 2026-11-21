package com.example.vanina_tesla

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.DashPathEffect
import android.graphics.Paint
import android.graphics.Path
import android.util.AttributeSet
import android.view.View
import kotlin.math.min

enum class HighlightDirection {
    NONE,
    NEUTRAL,
    FORWARD,
    RIGHT,
    BACKWARD,
    LEFT
}

class JoystickVisualizerView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : View(context, attrs, defStyleAttr) {

    private var rawX: Int = 512
    private var rawY: Int = 512
    private var neutralX: Int = 512
    private var neutralY: Int = 512
    private var deadzoneX: Int = 30
    private var deadzoneY: Int = 30
    private var activeDirection: HighlightDirection = HighlightDirection.NONE

    private val bgPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#F5F5F5")
        style = Paint.Style.FILL
    }

    private val borderPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#BDBDBD")
        style = Paint.Style.STROKE
        strokeWidth = 3f
    }

    private val axisPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#9E9E9E")
        style = Paint.Style.STROKE
        strokeWidth = 2f
    }

    private val deadzonePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#FF9800")
        style = Paint.Style.STROKE
        strokeWidth = 3f
        pathEffect = DashPathEffect(floatArrayOf(10f, 10f), 0f)
    }

    private val pointPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#E91E63")
        style = Paint.Style.FILL
    }

    private val pointStrokePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.WHITE
        style = Paint.Style.STROKE
        strokeWidth = 4f
    }

    private val arrowPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#4CAF50")
        style = Paint.Style.FILL_AND_STROKE
        strokeWidth = 6f
    }

    fun setPosition(x: Int, y: Int) {
        rawX = x.coerceIn(0, 1023)
        rawY = y.coerceIn(0, 1023)
        invalidate()
    }

    fun setNeutral(nx: Int, ny: Int, dzX: Int, dzY: Int) {
        neutralX = nx
        neutralY = ny
        deadzoneX = dzX
        deadzoneY = dzY
        invalidate()
    }

    fun setHighlightDirection(direction: HighlightDirection) {
        activeDirection = direction
        invalidate()
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)

        val w = width.toFloat()
        val h = height.toFloat()
        val cx = w / 2f
        val cy = h / 2f
        val radius = (min(w, h) / 2f) - 16f
        if (radius <= 0) return

        // 1. Фон круг
        canvas.drawCircle(cx, cy, radius, bgPaint)
        canvas.drawCircle(cx, cy, radius, borderPaint)

        // 2. Оси
        canvas.drawLine(cx - radius, cy, cx + radius, cy, axisPaint)
        canvas.drawLine(cx, cy - radius, cx, cy + radius, axisPaint)

        // 3. Зона нейтрали вокруг центра
        val dzRadius = (deadzoneX.coerceAtLeast(deadzoneY) / 512f) * radius
        canvas.drawCircle(cx, cy, dzRadius.coerceIn(10f, radius * 0.8f), deadzonePaint)

        // 4. Стрелка направления
        drawDirectionArrow(canvas, cx, cy, radius)

        // 5. Текущая точка джойстика
        // Преобразуем (rawX, rawY) 0..1023 в экранные координаты
        // 512 соответствует cx, cy
        val normX = (rawX - 512f) / 512f // [-1..1]
        // В экране Y направлен вниз, но если в покое 512, покажем смещение
        val normY = (rawY - 512f) / 512f

        val ptX = (cx + normX * (radius - 20f)).coerceIn(cx - radius + 15f, cx + radius - 15f)
        val ptY = (cy + normY * (radius - 20f)).coerceIn(cy - radius + 15f, cy + radius - 15f)

        canvas.drawCircle(ptX, ptY, 20f, pointPaint)
        canvas.drawCircle(ptX, ptY, 20f, pointStrokePaint)
    }

    private fun drawDirectionArrow(canvas: Canvas, cx: Float, cy: Float, radius: Float) {
        val arrowSize = 30f
        val margin = 35f
        val path = Path()

        when (activeDirection) {
            HighlightDirection.FORWARD -> {
                // Стрелка ВВЕРХ
                val tipY = cy - radius + margin
                path.moveTo(cx, tipY)
                path.lineTo(cx - arrowSize, tipY + arrowSize)
                path.lineTo(cx + arrowSize, tipY + arrowSize)
                path.close()
                canvas.drawPath(path, arrowPaint)
            }
            HighlightDirection.RIGHT -> {
                // Стрелка ВПРАВО
                val tipX = cx + radius - margin
                path.moveTo(tipX, cy)
                path.lineTo(tipX - arrowSize, cy - arrowSize)
                path.lineTo(tipX - arrowSize, cy + arrowSize)
                path.close()
                canvas.drawPath(path, arrowPaint)
            }
            HighlightDirection.BACKWARD -> {
                // Стрелка ВНИЗ
                val tipY = cy + radius - margin
                path.moveTo(cx, tipY)
                path.lineTo(cx - arrowSize, tipY - arrowSize)
                path.lineTo(cx + arrowSize, tipY - arrowSize)
                path.close()
                canvas.drawPath(path, arrowPaint)
            }
            HighlightDirection.LEFT -> {
                // Стрелка ВЛЕВО
                val tipX = cx - radius + margin
                path.moveTo(tipX, cy)
                path.lineTo(tipX + arrowSize, cy - arrowSize)
                path.lineTo(tipX + arrowSize, cy + arrowSize)
                path.close()
                canvas.drawPath(path, arrowPaint)
            }
            HighlightDirection.NEUTRAL -> {
                // Кружок в центре
                canvas.drawCircle(cx, cy, 14f, arrowPaint)
            }
            HighlightDirection.NONE -> {}
        }
    }
}
