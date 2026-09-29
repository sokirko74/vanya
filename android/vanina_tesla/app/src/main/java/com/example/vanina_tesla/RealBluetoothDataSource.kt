package com.example.vanina_tesla

import android.Manifest
import android.bluetooth.BluetoothManager
import android.bluetooth.BluetoothSocket
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.ActivityCompat
import org.json.JSONException
import org.json.JSONObject
import java.io.InputStream
import java.util.UUID
import kotlin.concurrent.thread

class RealBluetoothDataSource(
    private val context: Context
) : BluetoothDataSource {

    private val deviceAddress = "20:18:12:03:27:38"
    private val btUuid: UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")

    private var bluetoothSocket: BluetoothSocket? = null
    private var onData: ((WheelchairData) -> Unit)? = null
    private var onLog: ((String) -> Unit)? = null

    override fun startListening(onData: (WheelchairData) -> Unit, onLog: (String) -> Unit) {
        this.onData = onData
        this.onLog = onLog
    }

    override fun connect() {
        startBluetoothConnection()
    }

    override fun stopListening() {
        closeSocket()
        onData = null
        onLog = null
    }

    private fun log(message: String) {
        onLog?.invoke(message)
    }

    private fun startBluetoothConnection() {
        log("Попытка подключения к $deviceAddress...")

        thread {
            try {
                val bluetoothManager = context.getSystemService(BluetoothManager::class.java)
                val adapter = bluetoothManager?.adapter

                if (adapter == null || !adapter.isEnabled) {
                    log("Ошибка: Bluetooth на телефоне выключен!")
                    return@thread
                }

                val device = adapter.getRemoteDevice(deviceAddress)

                if (ActivityCompat.checkSelfPermission(
                        context,
                        Manifest.permission.BLUETOOTH_SCAN
                    ) == PackageManager.PERMISSION_GRANTED ||
                    Build.VERSION.SDK_INT < Build.VERSION_CODES.S
                ) {
                    adapter.cancelDiscovery()
                }

                log("Создание сокета...")
                bluetoothSocket = device.createRfcommSocketToServiceRecord(btUuid)

                log("Соединение...")
                bluetoothSocket?.connect()

                log("Успешно подключено! Ожидание данных...")

                Thread.sleep(200)

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

                if (line.startsWith("{")) {
                    parseJson(line)
                } else {
                    log("👉 $line")
                }
            }
        } catch (e: Exception) {
            log("Соединение разорвано: ${e.message}")
            closeSocket()
        }
    }

    private fun parseJson(jsonString: String) {
        try {
            val json = JSONObject(jsonString)
            onData?.invoke(
                WheelchairData(
                    distance1 = json.optInt("dist1", -1),
                    distance2 = json.optInt("dist2", -1),
                    speed1 = json.optInt("speed1", 0),
                    speed2 = json.optInt("speed2", 0)
                )
            )
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
        bluetoothSocket = null
    }
}
