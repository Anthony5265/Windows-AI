package com.windowsai

import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import android.os.Bundle
import android.app.Activity
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import java.net.HttpURLConnection
import java.net.URL

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        createChannel()
    }

    private fun createChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel("default", "Default", NotificationManager.IMPORTANCE_DEFAULT)
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }

    fun showNotification(message: String) {
        val builder = NotificationCompat.Builder(this, "default")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle("Windows AI")
            .setContentText(message)
        NotificationManagerCompat.from(this).notify(1, builder.build())
    }

    fun pair(deviceId: String, callback: (String?) -> Unit) {
        Thread {
            try {
                val url = URL("http://localhost:3000/api/mobile/pair")
                val conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.setRequestProperty("Content-Type", "application/json")
                conn.doOutput = true
                val body = "{\"deviceId\":\"$deviceId\"}"
                conn.outputStream.use { it.write(body.toByteArray()) }
                val response = conn.inputStream.bufferedReader().use { it.readText() }
                val token = Regex("\"token\":\"(.*?)\"").find(response)?.groupValues?.get(1)
                callback(token)
            } catch (e: Exception) {
                callback(null)
            }
        }.start()
    }

    fun sendCommand(token: String, action: String) {
        Thread {
            try {
                val url = URL("http://localhost:3000/api/mobile/command")
                val conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.setRequestProperty("Content-Type", "application/json")
                conn.doOutput = true
                val body = "{\"token\":\"$token\",\"action\":\"$action\"}"
                conn.outputStream.use { it.write(body.toByteArray()) }
                conn.inputStream.close()
            } catch (_: Exception) {}
        }.start()
    }
}
