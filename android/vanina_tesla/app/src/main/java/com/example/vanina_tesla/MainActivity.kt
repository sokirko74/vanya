package com.example.vanina_tesla

import android.Manifest
import android.bluetooth.BluetoothManager
import android.bluetooth.BluetoothSocket
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import org.json.JSONException
import org.json.JSONObject
import java.io.InputStream
import java.util.UUID
import kotlin.concurrent.thread
import kotlin.math.max
import android.content.SharedPreferences
import androidx.preference.PreferenceManager
import android.view.Menu
import android.view.MenuItem
import android.content.Intent


data class WheelchairData(
    var distance1: Int,
    var distance2: Int,
    var speed1: Int,
    var speed2: Int
)
class MainActivity : AppCompatActivity() {

    private val DEVICE_ADDRESS = "20:18:12:03:27:38"
    private val BT_UUID: UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")

    private lateinit var tvLogs: TextView
    private lateinit var btnConnect: Button
    private lateinit var scrollView: ScrollView
    private var bluetoothSocket: BluetoothSocket? = null
    private val beeper = Beeper()

    private lateinit var enginePlayer: EngineSoundPlayer
    private lateinit var prefs: SharedPreferences

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        tvLogs = findViewById(R.id.tvLogs)
        btnConnect = findViewById(R.id.btnConnect)
        scrollView = findViewById(R.id.scrollView)
        enginePlayer = EngineSoundPlayer(this, R.raw.stable)
        enginePlayer.setMuted(true)

        prefs = PreferenceManager.getDefaultSharedPreferences(this)
        val v1 = prefs.getBoolean("ignore_distance_2", false)
        val v2 = prefs.getBoolean("ignore_speed_2", false)
        log("$v1 $v2")
        btnConnect.setOnClickListener {
            if (checkPermissions()) {
                startBluetoothConnection()
            } else {
                requestPermissions()
            }
        }
    }

    private fun log(message: String) {
        runOnUiThread {
            tvLogs.append("$message\n")

            scrollView.post {
                scrollView.fullScroll(View.FOCUS_DOWN)
            }
        }

    }

    private fun startBluetoothConnection() {
        log("Попытка подключения к $DEVICE_ADDRESS...")

        thread {
            try {
                val bluetoothManager = getSystemService(BluetoothManager::class.java)
                val adapter = bluetoothManager?.adapter

                if (adapter == null || !adapter.isEnabled) {
                    log("Ошибка: Bluetooth на телефоне выключен!")
                    return@thread
                }

                val device = adapter.getRemoteDevice(DEVICE_ADDRESS)

                if (ActivityCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_SCAN) == PackageManager.PERMISSION_GRANTED || Build.VERSION.SDK_INT < Build.VERSION_CODES.S) {
                    adapter.cancelDiscovery()
                }

                log("Создание сокета...")
                bluetoothSocket = device.createRfcommSocketToServiceRecord(BT_UUID)

                log("Соединение...")
                bluetoothSocket?.connect()

                log("Успешно подключено! Ожидание данных...")

                // Даем 200 мс, чтобы накопленные байты долетели до буфера Android
                Thread.sleep(200)

                // --- Очистка накопившегося буфера (забываем старые сообщения) ---
                log("пробуем прочитать старые сообщения...")
                val inputStream = bluetoothSocket!!.inputStream
                while (inputStream.available() > 300) {
                    val bytesToSkip = inputStream.available()
                    if (bytesToSkip > 0) {
                        inputStream.skip(bytesToSkip.toLong())
                        log("Пропущено устаревших байт: $bytesToSkip")
                    }
                }
                readData(bluetoothSocket!!.inputStream)

            } catch (e: Exception) {
                log("Ошибка подключения: ${e.message}")
                closeSocket()
            }
        }
    }

    private fun readData(inputStream: InputStream) {
        val reader = inputStream.bufferedReader(Charsets.US_ASCII)

        try {
            while (true) {
                val line = reader.readLine()?.trim() ?: break
                if (line.isEmpty()) continue

                // Проверяем, начинается ли строка с '{'
                if (line.startsWith("{")) {
                    parseAndHandleJson(line)
                } else {
                    // Обычное текстовое сообщение
                    log("👉 $line")
                }
            }
        } catch (e: Exception) {
            log("Соединение разорвано: ${e.message}")
            closeSocket()
        }
    }

    private fun parktronic(wd: WheelchairData) {
        // Выбираем минимальную корректную дистанцию из двух датчиков
        val validDistances = listOf(wd.distance1, wd.distance2).filter { it != -1 }
        val distCentiMeter = (validDistances.minOrNull() ?: 1000.0).toDouble()

        val G3 = 1480
        val C4 = 1975

        if (distCentiMeter <= 8.0) {
            log("parktronic continuous")
            beeper.setContinuous(frequencyHz = C4)
        }
        else if (distCentiMeter < 50) {
            log("parktronic pulsed: distance ${distCentiMeter} cm")
            beeper.setPulsed(intervalMs = distCentiMeter.toLong() * 8, frequencyHz = G3)
        } else {
            beeper.setSilent() // Тишина, если далеко
        }
    }
    private fun parseAndHandleJson(jsonString: String) {
        try {
            val json = JSONObject(jsonString)

            // Извлекаем поля из JSON (названия ключей должны совпадать с теми, что шлет Arduino)
            val wd = WheelchairData(
                distance1 = json.optInt("dist1", -1),
                distance2 = json.optInt("dist2", -1),
                speed1 = json.optInt("speed1", 0),
                speed2 = json.optInt("speed2", 0))

            if (prefs.getBoolean("disable_engine_sound", false)) {
                wd.speed1 = -1;
                wd.speed2 = -1;
            }
            if (prefs.getBoolean("ignore_speed_1", false)) {
                wd.speed1 = -1;
            }
            if (prefs.getBoolean("ignore_speed_2", false)) {
                wd.speed2 = -1;
            }
            if (prefs.getBoolean("ignore_distance_1", false)) {

                wd.distance1 = -1;
            }
            if (prefs.getBoolean("ignore_distance_2", false)) {
                log("ignore_distance_2");
                wd.distance2 = -1;
            }

            if (wd.speed1 == -1 && wd.speed2 == -1) {
                enginePlayer.setMuted(true)
            } else {
                enginePlayer.setMuted(false)
            }

            // Выводим успешно распарсенные данные в лог
            log("P1=${wd.distance1}см, P2=${wd.distance2}см | S1=${wd.speed1}, S2=${wd.speed2}")

            parktronic(wd)
            val currentSpeed = max(wd.speed1, wd.speed2).toFloat() / 512.0F
            enginePlayer.updateSpeed(currentSpeed)

        } catch (e: JSONException) {
            log("⚠️ Ошибка парсинга JSON: ${e.localizedMessage} | Исходная строка: \"$jsonString\"")
        }
    }
    private fun closeSocket() {
        try {
            bluetoothSocket?.close()
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun checkPermissions(): Boolean {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            return ActivityCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_CONNECT) == PackageManager.PERMISSION_GRANTED
        }
        return true
    }

    private fun requestPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.BLUETOOTH_CONNECT, Manifest.permission.BLUETOOTH_SCAN), 1)
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
}
