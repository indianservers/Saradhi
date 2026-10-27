package com.quickbuddy.customer_app

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder

class VoiceCallService : Service() {
    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == "end") {
            MainActivity.endVoiceCall?.invoke()
            stopSelf()
            return START_NOT_STICKY
        }
        try {
            val manager = getSystemService(NotificationManager::class.java)
            if (Build.VERSION.SDK_INT >= 26) manager.createNotificationChannel(
                NotificationChannel("voice_calls", "Active voice calls", NotificationManager.IMPORTANCE_LOW))
            val open = Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_REORDER_TO_FRONT or Intent.FLAG_ACTIVITY_SINGLE_TOP)
            val openIntent = PendingIntent.getActivity(this, 0, open, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
            val endIntent = PendingIntent.getService(this, 1,
                Intent(this, VoiceCallService::class.java).setAction("end"),
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
            val builder = if (Build.VERSION.SDK_INT >= 26) Notification.Builder(this, "voice_calls") else Notification.Builder(this)
            val notification = builder.setSmallIcon(android.R.drawable.sym_action_call)
                .setContentTitle("Quickbuddy voice call")
                .setContentText("Tap to return to your call")
                .setContentIntent(openIntent).setOngoing(true)
                .setCategory(Notification.CATEGORY_CALL)
                .addAction(Notification.Action.Builder(android.R.drawable.ic_menu_close_clear_cancel,
                    "End call", endIntent).build()).build()
            if (Build.VERSION.SDK_INT >= 29) startForeground(2315, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE)
            else startForeground(2315, notification)
        } catch (_: Exception) {
            MainActivity.endVoiceCall?.invoke()
            stopSelf()
        }
        return START_NOT_STICKY
    }

    override fun onTaskRemoved(rootIntent: Intent?) {
        MainActivity.endVoiceCall?.invoke()
        stopSelf()
        super.onTaskRemoved(rootIntent)
    }

    override fun onDestroy() {
        if (Build.VERSION.SDK_INT >= 24) stopForeground(STOP_FOREGROUND_REMOVE)
        else { @Suppress("DEPRECATION") stopForeground(true) }
        super.onDestroy()
    }
}
