package com.quickbuddy.pilot_app

import android.Manifest
import android.content.pm.PackageManager
import android.content.Intent
import android.media.AudioAttributes
import android.media.Ringtone
import android.media.RingtoneManager
import android.os.Build
import android.view.WindowManager
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    companion object { var endVoiceCall: (() -> Unit)? = null }
    private var incomingTone: Ringtone? = null
    private var microphonePermissionResult: MethodChannel.Result? = null

    override fun configureFlutterEngine(engine: FlutterEngine) {
        super.configureFlutterEngine(engine)
        val channel = MethodChannel(engine.dartExecutor.binaryMessenger, "quickbuddy/calling")
        endVoiceCall = { channel.invokeMethod("endCall", null) }
        channel
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "requestMicrophone" -> {
                        val needed = mutableListOf<String>()
                        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) needed.add(Manifest.permission.RECORD_AUDIO)
                        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) needed.add(Manifest.permission.POST_NOTIFICATIONS)
                        if (needed.isEmpty()) result.success(true)
                        else if (microphonePermissionResult != null) result.error("permission_pending", "A permission request is already open", null)
                        else {
                            microphonePermissionResult = result
                            requestPermissions(needed.toTypedArray(), 2315)
                        }
                    }
                    "startCallService" -> {
                        try {
                            val intent = Intent(this, VoiceCallService::class.java)
                            if (Build.VERSION.SDK_INT >= 26) startForegroundService(intent) else startService(intent)
                            result.success(true)
                        } catch (_: Exception) { result.success(false) }
                    }
                    "stopCallService" -> { stopService(Intent(this, VoiceCallService::class.java)); result.success(null) }
                    "keepAwake" -> { window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON); result.success(null) }
                    "releaseAwake" -> { window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON); result.success(null) }
                    "ring" -> {
                        try {
                            if (incomingTone?.isPlaying != true) {
                                incomingTone = RingtoneManager.getRingtone(this,
                                    RingtoneManager.getDefaultUri(RingtoneManager.TYPE_RINGTONE))
                                incomingTone?.audioAttributes = AudioAttributes.Builder()
                                    .setUsage(AudioAttributes.USAGE_NOTIFICATION_RINGTONE)
                                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build()
                                if (Build.VERSION.SDK_INT >= 28) incomingTone?.isLooping = true
                                incomingTone?.play()
                            }
                            result.success(null)
                        } catch (_: Exception) {
                            result.error("ring_unavailable", "Call alert unavailable", null)
                        }
                    }
                    "stopRinging" -> { incomingTone?.stop(); incomingTone = null; result.success(null) }
                    else -> result.notImplemented()
                }
            }
    }

    override fun onRequestPermissionsResult(code: Int, permissions: Array<out String>, results: IntArray) {
        super.onRequestPermissionsResult(code, permissions, results)
        if (code == 2315) {
            microphonePermissionResult?.success(checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED)
            microphonePermissionResult = null
        }
    }

    override fun onDestroy() {
        stopService(Intent(this, VoiceCallService::class.java))
        endVoiceCall = null
        microphonePermissionResult?.error("activity_closed", "Microphone request cancelled", null)
        microphonePermissionResult = null
        incomingTone?.stop()
        incomingTone = null
        super.onDestroy()
    }
}
