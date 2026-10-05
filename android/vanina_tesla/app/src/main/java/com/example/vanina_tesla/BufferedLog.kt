package com.example.vanina_tesla

import android.content.Context
import android.os.Handler
import android.os.Looper
import android.util.Log
import timber.log.Timber
import java.io.BufferedWriter
import java.io.File
import java.io.FileWriter
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.ConcurrentLinkedQueue
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

const val LOG_FILE_NAME = "app_logs.txt"

class BufferedLog(
    private val context: Context,
    private val onUILog: (String) -> Unit = {}
) : Timber.DebugTree() {

    private val logQueue = ConcurrentLinkedQueue<String>()
    private val executor = Executors.newSingleThreadScheduledExecutor()
    private val mainHandler = Handler(Looper.getMainLooper())
    private val dateFormat = SimpleDateFormat("HH:mm:ss.SSS", Locale.getDefault())

    init {
        rotateLogFile()

        // Сбрасываем накопленные логи на диск раз в 1 секунду
        executor.scheduleWithFixedDelay({
            flushLogs()
        }, 1, 1, TimeUnit.SECONDS)
    }

    private fun rotateLogFile() {
        try {
            val logFile = File(context.filesDir, LOG_FILE_NAME)
            val maxSizeBytes = 20 * 1024 * 1024 // 20 МБ

            if (logFile.exists() && logFile.length() > maxSizeBytes) {
                val oldFile = File(context.filesDir, "$LOG_FILE_NAME.old")
                if (oldFile.exists()) oldFile.delete()
                logFile.renameTo(oldFile)
            }
        } catch (e: Exception) {
            Log.e("BufferedLog", "Error during log rotation", e)
        }
    }

    override fun log(priority: Int, tag: String?, message: String, t: Throwable?) {
        super.log(priority, tag, message, t) // Отправляет в обычный Logcat

        val timestamp = dateFormat.format(Date())
        val tagPrefix = if (tag != null) " [$tag]" else ""

        logQueue.add("[$timestamp]$tagPrefix: $message\n")
    }

    private fun flushLogs() {
        if (logQueue.isEmpty()) return

        rotateLogFile()

        val file = File(context.filesDir, LOG_FILE_NAME)
        val sb = StringBuilder()

        try {
            // Дозапись в конец файла (append = true)
            BufferedWriter(FileWriter(file, true)).use { writer ->
                while (logQueue.isNotEmpty()) {
                    val s = logQueue.poll() ?: break
                    writer.write(s)
                    sb.append(s)
                }
            }

            // Вызываем UI-коллбэк один раз со всей пачкой строк
            val batchText = sb.toString()
            if (batchText.isNotEmpty()) {
                mainHandler.post {
                    onUILog(batchText)
                }
            }
        } catch (e: Exception) {
            Log.e("BufferedLog", "Error flushing logs to file", e)
        }
    }
}
