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

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        tvLogs = findViewById(R.id.tvLogs)
        btnConnect = findViewById(R.id.btnConnect)
        scrollView = findViewById(R.id.scrollView)
        enginePlayer = EngineSoundPlayer(
            this,
            R.raw.stable, R.raw.engine_start
        )
        enginePlayer.setMuted(true)

        prefs = PreferenceManager.getDefaultSharedPreferences(this)
        val v1 = prefs.getBoolean("ignore_distance_2", false)
        val v2 = prefs.getBoolean("ignore_speed_2", false)
        log("$v1 $v2")

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
        bluetoothDataSource.stopListening()
        enginePlayer.stop()
        beeper.release()
        super.onDestroy()
    }

    private fun log(message: String) {
        runOnUiThread {
            tvLogs.append("$message\n")

            scrollView.post {
                scrollView.fullScroll(View.FOCUS_DOWN)
            }
        }
    }

    private fun parktronic(wd: WheelchairData) {
        val validDistances = listOf(wd.distance1, wd.distance2).filter { it != -1 }
        val distCentiMeter = (validDistances.minOrNull() ?: 1000.0).toDouble()

        val G3 = 1480
        val C4 = 1975

        if (distCentiMeter <= 8.0) {
            log("parktronic continuous")
            beeper.setContinuous(frequencyHz = C4)
        } else if (distCentiMeter < 50) {
            log("parktronic pulsed: distance ${distCentiMeter} cm")
            beeper.setPulsed(intervalMs = distCentiMeter.toLong() * 8, frequencyHz = G3)
        } else {
            beeper.setSilent()
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

        parktronic(wd)
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
