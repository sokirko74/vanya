package com.example.vanina_tesla

import android.os.Bundle
import android.os.CountDownTimer
import android.view.View
import android.widget.Button
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.preference.PreferenceManager
import kotlin.math.abs
import kotlin.math.roundToInt

class CalibrationActivity : AppCompatActivity() {

    enum class CalibStep {
        READY,
        NEUTRAL,
        FORWARD_MOVE,
        FORWARD_RETURN,
        RIGHT_MOVE,
        RIGHT_RETURN,
        BACKWARD_MOVE,
        BACKWARD_RETURN,
        LEFT_MOVE,
        DONE
    }

    private lateinit var tvStepTitle: TextView
    private lateinit var tvInstruction: TextView
    private lateinit var tvCountdown: TextView
    private lateinit var progressBarStep: ProgressBar
    private lateinit var joystickVisualizer: JoystickVisualizerView
    private lateinit var tvRawCoordinates: TextView
    private lateinit var tvResults: TextView
    private lateinit var btnAction: Button
    private lateinit var btnCancel: Button

    private var currentStep = CalibStep.READY
    private var timer: CountDownTimer? = null

    private var latestRawX = -1
    private var latestRawY = -1
    private val stepSamples = mutableListOf<Pair<Int, Int>>()

    private var neutralX = 512
    private var neutralY = 512
    private var deadzoneX = 30
    private var deadzoneY = 30

    private var forwardConfig = DirectionConfig('Y', 542, 850)
    private var rightConfig = DirectionConfig('X', 542, 850)
    private var backwardConfig = DirectionConfig('Y', 482, 150)
    private var leftConfig = DirectionConfig('X', 482, 150)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_calibration)

        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        title = "Балансировка джойстика"

        tvStepTitle = findViewById(R.id.tvStepTitle)
        tvInstruction = findViewById(R.id.tvInstruction)
        tvCountdown = findViewById(R.id.tvCountdown)
        progressBarStep = findViewById(R.id.progressBarStep)
        joystickVisualizer = findViewById(R.id.joystickVisualizer)
        tvRawCoordinates = findViewById(R.id.tvRawCoordinates)
        tvResults = findViewById(R.id.tvResults)
        btnAction = findViewById(R.id.btnAction)
        btnCancel = findViewById(R.id.btnCancel)

        val prefs = PreferenceManager.getDefaultSharedPreferences(this)
        val existing = JoystickCalibration.loadFromPrefs(prefs)
        neutralX = existing.neutralX
        neutralY = existing.neutralY
        deadzoneX = existing.deadzoneX
        deadzoneY = existing.deadzoneY
        forwardConfig = existing.forward
        rightConfig = existing.right
        backwardConfig = existing.backward
        leftConfig = existing.left
        joystickVisualizer.setNeutral(neutralX, neutralY, deadzoneX, deadzoneY)

        btnAction.setOnClickListener {
            when (currentStep) {
                CalibStep.READY -> startStep(CalibStep.NEUTRAL)
                CalibStep.DONE -> saveAndExit()
                else -> {}
            }
        }

        btnCancel.setOnClickListener {
            when (currentStep) {
                CalibStep.READY -> finish()
                CalibStep.DONE -> {
                    currentStep = CalibStep.READY
                    updateUiForStep(CalibStep.READY)
                }
                else -> {
                    timer?.cancel()
                    currentStep = CalibStep.READY
                    updateUiForStep(CalibStep.READY)
                    Toast.makeText(this, "Калибровка отменена", Toast.LENGTH_SHORT).show()
                }
            }
        }

        updateUiForStep(CalibStep.READY)
    }

    override fun onResume() {
        super.onResume()
        MainActivity.onWheelchairDataReceived = { wd ->
            runOnUiThread {
                latestRawX = wd.rawX
                latestRawY = wd.rawY
                joystickVisualizer.setPosition(wd.rawX, wd.rawY)
                tvRawCoordinates.text = "Сырые координаты: X = ${wd.rawX} | Y = ${wd.rawY}"
            }
        }
    }

    override fun onPause() {
        super.onPause()
        MainActivity.onWheelchairDataReceived = null
        timer?.cancel()
    }

    override fun onSupportNavigateUp(): Boolean {
        onBackPressedDispatcher.onBackPressed()
        return true
    }

    private fun startStep(step: CalibStep) {
        currentStep = step
        stepSamples.clear()
        updateUiForStep(step)

        timer?.cancel()
        timer = object : CountDownTimer(5000, 100) {
            override fun onTick(millisUntilFinished: Long) {
                val secLeft = (millisUntilFinished / 1000) + 1
                tvCountdown.text = "$secLeft"
                val progress = ((5000 - millisUntilFinished) / 100).toInt()
                progressBarStep.progress = progress

                if (latestRawX >= 0 && latestRawY >= 0) {
                    stepSamples.add(Pair(latestRawX, latestRawY))
                }
            }

            override fun onFinish() {
                progressBarStep.progress = 50
                handleStepFinished(step)
            }
        }.start()
    }

    private fun handleStepFinished(step: CalibStep) {
        if (stepSamples.isEmpty()) {
            Toast.makeText(this, "Внимание: нет данных от джойстика! Проверьте Bluetooth.", Toast.LENGTH_LONG).show()
            currentStep = CalibStep.READY
            updateUiForStep(CalibStep.READY)
            return
        }

        when (step) {
            CalibStep.NEUTRAL -> {
                neutralX = stepSamples.map { it.first }.average().roundToInt()
                neutralY = stepSamples.map { it.second }.average().roundToInt()
                val jitterX = stepSamples.maxOf { abs(it.first - neutralX) }
                val jitterY = stepSamples.maxOf { abs(it.second - neutralY) }
                deadzoneX = maxOf(jitterX + 15, 30)
                deadzoneY = maxOf(jitterY + 15, 30)
                joystickVisualizer.setNeutral(neutralX, neutralY, deadzoneX, deadzoneY)
                startStep(CalibStep.FORWARD_MOVE)
            }
            CalibStep.FORWARD_MOVE -> {
                forwardConfig = calculateDirectionConfig(stepSamples)
                startStep(CalibStep.FORWARD_RETURN)
            }
            CalibStep.FORWARD_RETURN -> {
                startStep(CalibStep.RIGHT_MOVE)
            }
            CalibStep.RIGHT_MOVE -> {
                rightConfig = calculateDirectionConfig(stepSamples)
                startStep(CalibStep.RIGHT_RETURN)
            }
            CalibStep.RIGHT_RETURN -> {
                startStep(CalibStep.BACKWARD_MOVE)
            }
            CalibStep.BACKWARD_MOVE -> {
                backwardConfig = calculateDirectionConfig(stepSamples)
                startStep(CalibStep.BACKWARD_RETURN)
            }
            CalibStep.BACKWARD_RETURN -> {
                startStep(CalibStep.LEFT_MOVE)
            }
            CalibStep.LEFT_MOVE -> {
                leftConfig = calculateDirectionConfig(stepSamples)
                currentStep = CalibStep.DONE
                updateUiForStep(CalibStep.DONE)
            }
            else -> {}
        }
    }

    private fun calculateDirectionConfig(samples: List<Pair<Int, Int>>): DirectionConfig {
        val maxDevX = samples.maxOf { abs(it.first - neutralX) }
        val maxDevY = samples.maxOf { abs(it.second - neutralY) }

        return if (maxDevY >= maxDevX) {
            val peakSampleY = samples.maxByOrNull { abs(it.second - neutralY) }?.second ?: neutralY
            val isPositive = peakSampleY >= neutralY
            val neutralEdge = if (isPositive) neutralY + deadzoneY else neutralY - deadzoneY
            val maxEdge = if (isPositive) samples.maxOf { it.second } else samples.minOf { it.second }
            DirectionConfig('Y', neutralEdge, maxEdge)
        } else {
            val peakSampleX = samples.maxByOrNull { abs(it.first - neutralX) }?.first ?: neutralX
            val isPositive = peakSampleX >= neutralX
            val neutralEdge = if (isPositive) neutralX + deadzoneX else neutralX - deadzoneX
            val maxEdge = if (isPositive) samples.maxOf { it.first } else samples.minOf { it.first }
            DirectionConfig('X', neutralEdge, maxEdge)
        }
    }

    private fun updateUiForStep(step: CalibStep) {
        when (step) {
            CalibStep.READY -> {
                tvStepTitle.text = "Мастер балансировки джойстика"
                tvInstruction.text = "Установите джойстик в центр и нажмите 'Начать'.\nШаги по 5 секунд: нейтраль, вперед, пауза, вправо, пауза, назад, пауза, влево."
                tvCountdown.visibility = View.GONE
                progressBarStep.visibility = View.GONE
                tvResults.visibility = View.GONE
                btnAction.visibility = View.VISIBLE
                btnAction.text = "Начать"
                btnCancel.text = "Закрыть"
                joystickVisualizer.setHighlightDirection(HighlightDirection.NONE)
            }
            CalibStep.NEUTRAL -> {
                tvStepTitle.text = "Шаг 1 из 5: Нейтраль"
                tvInstruction.text = "НЕ трогайте джойстик!\nИдет измерение точки покоя и зоны шума..."
                tvCountdown.visibility = View.VISIBLE
                progressBarStep.visibility = View.VISIBLE
                tvResults.visibility = View.GONE
                btnAction.visibility = View.GONE
                btnCancel.text = "Отмена"
                joystickVisualizer.setHighlightDirection(HighlightDirection.NEUTRAL)
            }
            CalibStep.FORWARD_MOVE -> {
                tvStepTitle.text = "Шаг 2 из 5: Вперед"
                tvInstruction.text = "Плавно доведите джойстик ВПЕРЕД до упора и удерживайте."
                tvCountdown.visibility = View.VISIBLE
                progressBarStep.visibility = View.VISIBLE
                tvResults.visibility = View.GONE
                btnAction.visibility = View.GONE
                btnCancel.text = "Отмена"
                joystickVisualizer.setHighlightDirection(HighlightDirection.FORWARD)
            }
            CalibStep.FORWARD_RETURN -> {
                tvStepTitle.text = "Возврат в нейтраль"
                tvInstruction.text = "Верните джойстик в центр и отпустите. Пауза 5 сек..."
                tvCountdown.visibility = View.VISIBLE
                progressBarStep.visibility = View.VISIBLE
                tvResults.visibility = View.GONE
                btnAction.visibility = View.GONE
                btnCancel.text = "Отмена"
                joystickVisualizer.setHighlightDirection(HighlightDirection.NEUTRAL)
            }
            CalibStep.RIGHT_MOVE -> {
                tvStepTitle.text = "Шаг 3 из 5: Вправо"
                tvInstruction.text = "Плавно доведите джойстик ВПРАВО до упора и удерживайте."
                tvCountdown.visibility = View.VISIBLE
                progressBarStep.visibility = View.VISIBLE
                tvResults.visibility = View.GONE
                btnAction.visibility = View.GONE
                btnCancel.text = "Отмена"
                joystickVisualizer.setHighlightDirection(HighlightDirection.RIGHT)
            }
            CalibStep.RIGHT_RETURN -> {
                tvStepTitle.text = "Возврат в нейтраль"
                tvInstruction.text = "Верните джойстик в центр и отпустите. Пауза 5 сек..."
                tvCountdown.visibility = View.VISIBLE
                progressBarStep.visibility = View.VISIBLE
                tvResults.visibility = View.GONE
                btnAction.visibility = View.GONE
                btnCancel.text = "Отмена"
                joystickVisualizer.setHighlightDirection(HighlightDirection.NEUTRAL)
            }
            CalibStep.BACKWARD_MOVE -> {
                tvStepTitle.text = "Шаг 4 из 5: Назад"
                tvInstruction.text = "Плавно доведите джойстик НАЗАД до упора и удерживайте."
                tvCountdown.visibility = View.VISIBLE
                progressBarStep.visibility = View.VISIBLE
                tvResults.visibility = View.GONE
                btnAction.visibility = View.GONE
                btnCancel.text = "Отмена"
                joystickVisualizer.setHighlightDirection(HighlightDirection.BACKWARD)
            }
            CalibStep.BACKWARD_RETURN -> {
                tvStepTitle.text = "Возврат в нейтраль"
                tvInstruction.text = "Верните джойстик в центр и отпустите. Пауза 5 сек..."
                tvCountdown.visibility = View.VISIBLE
                progressBarStep.visibility = View.VISIBLE
                tvResults.visibility = View.GONE
                btnAction.visibility = View.GONE
                btnCancel.text = "Отмена"
                joystickVisualizer.setHighlightDirection(HighlightDirection.NEUTRAL)
            }
            CalibStep.LEFT_MOVE -> {
                tvStepTitle.text = "Шаг 5 из 5: Влево"
                tvInstruction.text = "Плавно доведите джойстик ВЛЕВО до упора и удерживайте."
                tvCountdown.visibility = View.VISIBLE
                progressBarStep.visibility = View.VISIBLE
                tvResults.visibility = View.GONE
                btnAction.visibility = View.GONE
                btnCancel.text = "Отмена"
                joystickVisualizer.setHighlightDirection(HighlightDirection.LEFT)
            }
            CalibStep.DONE -> {
                tvStepTitle.text = "Калибровка завершена!"
                tvInstruction.text = "Проверьте полученные параметры и нажмите 'Сохранить'."
                tvCountdown.visibility = View.GONE
                progressBarStep.visibility = View.GONE
                tvResults.visibility = View.VISIBLE
                tvResults.text = buildString {
                    appendLine("Центр: X=$neutralX, Y=$neutralY (зона покоя: ±$deadzoneX / ±$deadzoneY)")
                    appendLine("Вперед: ось ${forwardConfig.axis}, нейтраль=${forwardConfig.neutralEdge}, макс=${forwardConfig.maxEdge}")
                    appendLine("Вправо: ось ${rightConfig.axis}, нейтраль=${rightConfig.neutralEdge}, макс=${rightConfig.maxEdge}")
                    appendLine("Назад:  ось ${backwardConfig.axis}, нейтраль=${backwardConfig.neutralEdge}, макс=${backwardConfig.maxEdge}")
                    appendLine("Влево:  ось ${leftConfig.axis}, нейтраль=${leftConfig.neutralEdge}, макс=${leftConfig.maxEdge}")
                }
                btnAction.visibility = View.VISIBLE
                btnAction.text = "Сохранить и применить"
                btnCancel.text = "Повторить"
                joystickVisualizer.setHighlightDirection(HighlightDirection.NONE)
            }
        }
    }

    private fun saveAndExit() {
        val prefs = PreferenceManager.getDefaultSharedPreferences(this)
        val calib = JoystickCalibration(
            isCalibrated = true,
            neutralX = neutralX,
            neutralY = neutralY,
            deadzoneX = deadzoneX,
            deadzoneY = deadzoneY,
            forward = forwardConfig,
            right = rightConfig,
            backward = backwardConfig,
            left = leftConfig
        )
        calib.saveToPrefs(prefs)
        Toast.makeText(this, "Калибровка сохранена!", Toast.LENGTH_SHORT).show()
        finish()
    }
}
