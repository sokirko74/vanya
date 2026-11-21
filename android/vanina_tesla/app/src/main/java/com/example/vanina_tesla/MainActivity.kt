package com.example.vanina_tesla

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
import android.view.View
import android.widget.Button
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.preference.PreferenceManager
import kotlin.math.max
import timber.log.Timber
import android.os.Handler
import android.os.Looper
import kotlin.system.exitProcess


data class WheelchairData(
    var distance1: Int = -1,
    var distance2: Int = -1,
    var speed1: Int = 0,
    var speed2: Int = 0,
    var rawX: Int = -1,
    var rawY: Int = -1
)

fun readCoef(prefs: SharedPreferences, coefName: String): Float {
    val s = prefs.getString(coefName, "1.0") ?: "1.0"
    return s.toFloatOrNull() ?: 1.0f
}

class MainActivity : AppCompatActivity() {

    private lateinit var tvLogs: TextView
    private lateinit var btnConnect: Button
    private lateinit var btnCalibrate: Button
    private lateinit var btnQuickZero: Button
    private lateinit var scrollView: ScrollView
    private val beeper = Beeper()

    internal lateinit var enginePlayer: EngineSoundPlayer
    internal lateinit var bluetoothDataSource: BluetoothDataSource
    private lateinit var prefs: SharedPreferences
    private lateinit var joystickCalibration: JoystickCalibration

    private lateinit var btnEngineMute: Button
    private val watchdogHandler = Handler(Looper.getMainLooper())
    private val watchdogRunnable = Runnable {
        Timber.d("Watchdog: No data received for 1.5s! Muting sounds.")
        enginePlayer.setMuted(true)
        beeper.setSilent()
    }
    private var isUserMuted = false

    private lateinit var btnExit: Button

    private lateinit var tvDistance1: TextView
    private lateinit var tvDistance2: TextView
    private lateinit var tvSpeed: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        tvLogs = findViewById(R.id.tvLogs)
        tvDistance1 = findViewById(R.id.tvParktronic1)
        tvDistance2 = findViewById(R.id.tvParktronic2)
        tvSpeed = findViewById(R.id.tvSpeed)
        btnConnect = findViewById(R.id.btnConnect)
        scrollView = findViewById(R.id.scrollView)
        enginePlayer = EngineSoundPlayer(
            this,
            R.raw.stable,
            R.raw.engine_start,
            { Timber.d(it)}
        )

        prefs = PreferenceManager.getDefaultSharedPreferences(this)
        joystickCalibration = JoystickCalibration.loadFromPrefs(prefs)

        bluetoothDataSource = dataSourceProvider(this)
        activeDataSource = bluetoothDataSource

        Timber.plant(BufferedLog(applicationContext, ::log_ui))

        bluetoothDataSource.startListening(
            onData = { handleWheelchairData(it) },
            onLog = { Timber.d(it) }
        )

        btnConnect.setOnClickListener {
            if (checkPermissions()) {
                bluetoothDataSource.connect()
            } else {
                requestPermissions()
            }
        }
        btnEngineMute = findViewById(R.id.btnEngineMute)

        btnCalibrate = findViewById(R.id.btnCalibrate)
        btnCalibrate.setOnClickListener {
            val intent = Intent(this, CalibrationActivity::class.java)
            startActivity(intent)
        }

        btnQuickZero = findViewById(R.id.btnQuickZero)
        btnQuickZero.setOnClickListener {
            val last = lastWheelchairData
            if (last != null && last.rawX >= 0 && last.rawY >= 0) {
                joystickCalibration.quickZero(last.rawX, last.rawY)
                joystickCalibration.saveToPrefs(prefs)
                Toast.makeText(this, "Нейтраль откалибрована: X=${last.rawX}, Y=${last.rawY}", Toast.LENGTH_SHORT).show()
                Timber.d("Quick zero applied: X=${last.rawX}, Y=${last.rawY}")
            } else {
                Toast.makeText(this, "Нет данных от джойстика!", Toast.LENGTH_SHORT).show()
            }
        }

        // 1. Подписываем UI на изменения из EngineSoundPlayer
        enginePlayer.onMuteStateChanged = { isMuted ->
            updateMuteButtonUi(isMuted)
        }

        // 2. Обработка ручного клика по кнопке
        btnEngineMute.setOnClickListener {
            // Переключаем пользовательский флаг при клике
            isUserMuted = !isUserMuted

            if (!isUserMuted) {
                resetWatchdogTimer()
            }

            // Сразу обновляем плеер: если пользователь замутил — выключаем,
            // если размутил — включаем (если машина в этот момент едет)
            enginePlayer.setMuted(isUserMuted)
        }
        
        // Инициализируем начальное состояние кнопки
        updateMuteButtonUi(enginePlayer.isMuted)

        btnExit = findViewById(R.id.btnExit)
        btnExit.setOnClickListener {
            exitAppGracefully()
        }

        Timber.d("start vanina_tesla application: MainActivity.OnCreate")
    }

    override fun onResume() {
        super.onResume()
        joystickCalibration = JoystickCalibration.loadFromPrefs(prefs)
    }

    private fun exitAppGracefully() {
        Timber.d("User clicked Exit button")

        // 1. Принудительно сбрасываем буфер логов на диск,
        // раз уж мы контролируем момент выхода.
        (Timber.forest().firstOrNull { it is BufferedLog } as? BufferedLog)?.flushNow()

        // 2. Закрываем текущую активность (вызовется onDestroy)
        finishAffinity() // Закрывает эту и все связанные активности в стеке

        // 3. Убиваем системный процесс приложения, чтобы оно гарантированно
        // выгрузилось из памяти и не висело в фоне.
        exitProcess(0)
    }

    private fun resetWatchdogTimer() {
        watchdogHandler.removeCallbacks(watchdogRunnable)
        watchdogHandler.postDelayed(watchdogRunnable, 15000) // 15 секунд таймаут
    }

    override fun onDestroy() {
        Timber.d("exit main activity")
        (Timber.forest().firstOrNull { it is BufferedLog } as? BufferedLog)?.flushNow()
        watchdogHandler.removeCallbacks(watchdogRunnable)
        if (activeDataSource == bluetoothDataSource) {
            activeDataSource = null
        }
        bluetoothDataSource.stopListening()
        enginePlayer.stop()
        beeper.release()
        super.onDestroy()
    }

    private fun log_ui(message: String) {
        // 2. Вывод в UI
        runOnUiThread {
            tvLogs.append("$message\n")

            scrollView.post {
                scrollView.fullScroll(View.FOCUS_DOWN)
            }
        }
    }

    private fun one_parktonic(name: String, distance: Int, pitch: Int) {
        if ((distance in 0..8)) {
            Timber.d("parktronic $name continuous")
            beeper.setContinuous(frequencyHz = pitch)
        } else if (distance < 50) {
            Timber.d("parktronic $name pulsed: distance $distance cm")
            beeper.setPulsed(intervalMs = distance.toLong() * 8, frequencyHz = pitch)
        }
    }

    private fun process_parktronics(wd: WheelchairData) {
        val validDistances = listOf(wd.distance1, wd.distance2).filter { it != -1 }
        tvDistance1.text = "${wd.distance1}"
        tvDistance2.text = "${wd.distance2}"

        val distCentiMeter = validDistances.minOrNull() ?: 1000
        if (distCentiMeter >= 50) {
            Timber.d("all parktronic are silent")
            beeper.setSilent()
        }
        else {
            val G3 = 1480
            val C4 = 1975

            // Приоритет отдаем ближнему датчику
            if (wd.distance1 in 0 until wd.distance2 || wd.distance2 == -1) {
                one_parktonic("left", wd.distance1, G3)
            } else if (wd.distance2 in 0 until wd.distance1 || wd.distance1 == -1) {
                one_parktonic("right", wd.distance2, C4)
            } else {
                one_parktonic("left", wd.distance1, G3)
            }
        }
    }

    internal fun handleWheelchairData(wd: WheelchairData) {
        // Сбрасываем таймер watchdog при каждом приходе данных
        resetWatchdogTimer()

        lastWheelchairData = wd
        onWheelchairDataReceived?.invoke(wd)

        if (prefs.getBoolean("disable_engine_sound", false)) {
            wd.speed1 = -1
            wd.speed2 = -1
        }
        if (prefs.getBoolean("ignore_speed_1", false)) {
            wd.speed1 = -1
        }
        if (prefs.getBoolean("ignore_speed_2", false)) {
            wd.speed2 = -1
        }
        if (prefs.getBoolean("ignore_distance_1", false)) {
            wd.distance1 = -1
        }
        if (prefs.getBoolean("ignore_distance_2", false)) {
            Timber.d("ignore_distance_2")
            wd.distance2 = -1
        }
        val debugSpeed = prefs.getString("debug_speed", "")

        val effectiveSpeed: Int = if (prefs.getBoolean("disable_engine_sound", false)) {
            0
        } else if (wd.rawX >= 0 && wd.rawY >= 0) {
            val normSpeed = joystickCalibration.calculateSpeed(wd.rawX, wd.rawY)
            (normSpeed * 512f).toInt()
        } else {
            val effectiveSpeed_pre = (listOf(wd.speed1, wd.speed2).filter { it >= 0 }.maxOrNull() ?: 0).toInt()
            if (effectiveSpeed_pre <= 0) {
                0
            } else {
                val speedSlope = readCoef(prefs, "speed_slope_coef")
                val speedIntercept = readCoef(prefs, "speed_intercept_coef")
                (speedSlope * effectiveSpeed_pre.toFloat() + speedIntercept).toInt()
            }
        }

        // Звук глушится, если машина стоит ИЛИ если пользователь выключил звук вручную.
        // Если машина едет И пользователь не заглушил звук с кнопки — включаем его.
        if (effectiveSpeed <= 0 || isUserMuted) {
            enginePlayer.setMuted(true)
        } else {
            enginePlayer.setMuted(false)
        }

        Timber.d("P1=${wd.distance1}см, P2=${wd.distance2}см | RawX=${wd.rawX}, RawY=${wd.rawY} | S1=${wd.speed1}, S2=${wd.speed2}, speed=$effectiveSpeed")

        process_parktronics(wd)
        val currentSpeed = max(effectiveSpeed, 0).toFloat() / 512.0F
        tvSpeed.text = "$effectiveSpeed"
        enginePlayer.updateSpeed(currentSpeed)
    }

    private fun checkPermissions(): Boolean {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val connect = ActivityCompat.checkSelfPermission(
                this, Manifest.permission.BLUETOOTH_CONNECT
            ) == PackageManager.PERMISSION_GRANTED
            val scan = ActivityCompat.checkSelfPermission(
                this, Manifest.permission.BLUETOOTH_SCAN
            ) == PackageManager.PERMISSION_GRANTED
            return connect && scan
        }
        return true
    }

    private fun requestPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.BLUETOOTH_CONNECT, Manifest.permission.BLUETOOTH_SCAN),
                1
            )
        }
    }

    private fun updateMuteButtonUi(isMuted: Boolean) {
        if (isMuted) {
            btnEngineMute.text = "Звук мотора: ВЫКЛ"
        } else {
            btnEngineMute.text = "Звук мотора: ВКЛ"
        }
    }


    override fun onCreateOptionsMenu(menu: Menu?): Boolean {
        menuInflater.inflate(R.menu.main_menu, menu)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            R.id.action_settings -> {
                val intent = Intent(this, SettingsActivity::class.java)
                startActivity(intent)
                true
            }
            R.id.action_calibrate -> {
                val intent = Intent(this, CalibrationActivity::class.java)
                startActivity(intent)
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }

    companion object {
        var dataSourceProvider: (Context) -> BluetoothDataSource = { context ->
            RealBluetoothDataSource(context)
        }
        var activeDataSource: BluetoothDataSource? = null
        var onWheelchairDataReceived: ((WheelchairData) -> Unit)? = null
        var lastWheelchairData: WheelchairData? = null
    }
}
