package com.example.vanina_tesla

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.view.Menu
import android.view.MenuItem
import android.view.View
import android.widget.Button
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.preference.PreferenceManager
import java.io.File
import kotlin.math.max


val LogFileName = "app_logs.txt"

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

    private val fileLogExecutor = java.util.concurrent.Executors.newSingleThreadExecutor()

    private fun rotateLogFile(){
        val logFile = File(filesDir, LogFileName)
        val maxSizeBytes = 10 * 1024 * 1024 // 10 МБ

        // Если файл превысил 1 МБ, делаем ротацию
        if (logFile.exists() && logFile.length() > maxSizeBytes) {
            val oldFile = File(filesDir, "$LogFileName.old")
            if (oldFile.exists()) oldFile.delete() // Удаляем совсем старый бэкап
            logFile.renameTo(oldFile)               // Текущий лог становится старым
        }
    }
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
            ::log
        )
        rotateLogFile();

        prefs = PreferenceManager.getDefaultSharedPreferences(this)

        bluetoothDataSource = dataSourceProvider(this)
        bluetoothDataSource.startListening(
            onData = { handleWheelchairData(it) },
            onLog = { log(it) }
        )

        btnConnect.setOnClickListener {
            if (checkPermissions()) {
                bluetoothDataSource.connect()
            } else {
                requestPermissions()
            }
        }
    }

    override fun onDestroy() {
        log("exit main activity")
        fileLogExecutor.shutdown() // Не забываем закрыть экзекутор при уничтожении Activity
        bluetoothDataSource.stopListening()
        enginePlayer.stop()
        beeper.release()
        super.onDestroy()
    }

    private fun log(message: String) {
        Log.d("WheelchairTest", message)

        // 1. Дописываем лог в файл (в фоновом потоке, чтобы не тормозить UI)
        // Дописываем лог в файл через единый фоновый поток
        fileLogExecutor.execute {
            try {
                val logFile = File(filesDir, LogFileName)
                val timestamp = java.text.SimpleDateFormat("HH:mm:ss.SSS", java.util.Locale.getDefault()).format(java.util.Date())
                logFile.appendText("[$timestamp] $message\n")
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }

        // 2. Вывод в UI
        runOnUiThread {
            tvLogs.append("$message\n")

            scrollView.post {
                scrollView.fullScroll(View.FOCUS_DOWN)
            }
        }
    }

    private fun one_parktonic(name: String, distance: Int, pitch: Int) {
        if (distance <= 8.0) {
            log("parktronic $name continuous")
            beeper.setContinuous(frequencyHz = pitch)
        } else if (distance < 50) {
            log("parktronic $name pulsed: distance $distance cm")
            beeper.setPulsed(intervalMs = distance.toLong() * 8, frequencyHz = pitch)
        }
    }

    private fun process_parktronics(wd: WheelchairData) {
        val validDistances = listOf(wd.distance1, wd.distance2).filter { it != -1 }
        val distCentiMeter = (validDistances.minOrNull() ?: 1000.0).toDouble()
        if (distCentiMeter >= 50) {
            log("all parktronic are silent")
            beeper.setSilent()
        }
        else {
            val G3 = 1480
            val C4 = 1975

            one_parktonic("left", wd.distance1, G3)
            one_parktonic("right", wd.distance2, C4)
        }
    }

    internal fun handleWheelchairData(wd: WheelchairData) {
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
            log("ignore_distance_2")
            wd.distance2 = -1
        }

        val effectiveSpeed = listOf(wd.speed1, wd.speed2).filter { it >= 0 }.maxOrNull() ?: 0
        if (effectiveSpeed <= 0) {
            enginePlayer.setMuted(true)
        } else {
            enginePlayer.setMuted(false)
        }

        log("P1=${wd.distance1}см, P2=${wd.distance2}см | S1=${wd.speed1}, S2=${wd.speed2}")

        process_parktronics(wd)
        val currentSpeed = max(effectiveSpeed, 0).toFloat() / 512.0F
        enginePlayer.updateSpeed(currentSpeed)
    }

    private fun checkPermissions(): Boolean {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            return ActivityCompat.checkSelfPermission(
                this,
                Manifest.permission.BLUETOOTH_CONNECT
            ) == PackageManager.PERMISSION_GRANTED
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
