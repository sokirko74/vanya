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
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.preference.PreferenceManager
import kotlin.math.max
import timber.log.Timber
import android.os.Handler
import android.os.Looper
import kotlin.system.exitProcess


data class WheelchairData(
    var distance1: Int,
    var distance2: Int,
    var speed1: Int,
    var speed2: Int
)

class MainActivity : AppCompatActivity() {

    private lateinit var tvLogs: TextView
    private lateinit var btnConnect: Button
    private lateinit var scrollView: ScrollView
    private val beeper = Beeper()

    internal lateinit var enginePlayer: EngineSoundPlayer
    internal lateinit var bluetoothDataSource: BluetoothDataSource
    private lateinit var prefs: SharedPreferences

    private lateinit var btnEngineMute: Button
    private val watchdogHandler = Handler(Looper.getMainLooper())
    private val watchdogRunnable = Runnable {
        Timber.d("Watchdog: No data received for 1.5s! Muting sounds.")
        enginePlayer.setMuted(true)
        beeper.setSilent()
    }
    private var isUserMuted = false

    private lateinit var btnExit: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        tvLogs = findViewById(R.id.tvLogs)
        btnConnect = findViewById(R.id.btnConnect)
        scrollView = findViewById(R.id.scrollView)
        enginePlayer = EngineSoundPlayer(
            this,
            R.raw.stable,
            R.raw.engine_start,
            { Timber.d(it)}
        )

        prefs = PreferenceManager.getDefaultSharedPreferences(this)

        bluetoothDataSource = dataSourceProvider(this)

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

        val coefString = prefs.getString("speed_coef", "1.0") ?: "1.0"
        val effectiveSpeed_pre = (listOf(wd.speed1, wd.speed2).filter { it >= 0 }.maxOrNull() ?: 0).toInt()
        val effectiveSpeed = ((coefString.toFloatOrNull() ?: 1.0f) * effectiveSpeed_pre.toFloat()).toInt()

        // Звук глушится, если машина стоит ИЛИ если пользователь выключил звук вручную.
        // Если машина едет И пользователь не заглушил звук с кнопки — включаем его.
        if (effectiveSpeed <= 0 || isUserMuted) {
            enginePlayer.setMuted(true)
        } else {
            enginePlayer.setMuted(false)
        }

        Timber.d("P1=${wd.distance1}см, P2=${wd.distance2}см | S1=${wd.speed1}, S2=${wd.speed2}, ds=$debugSpeed ")

        process_parktronics(wd)
        val currentSpeed = max(effectiveSpeed, 0).toFloat() / 512.0F
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
            else -> super.onOptionsItemSelected(item)
        }

    }

    companion object {
        var dataSourceProvider: (Context) -> BluetoothDataSource = { context ->
            RealBluetoothDataSource(context)
        }
    }
}
