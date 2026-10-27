import Flutter
import UIKit
import AudioToolbox
import AVFoundation

@main
@objc class AppDelegate: FlutterAppDelegate, FlutterImplicitEngineDelegate {
  override func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
  ) -> Bool {
    return super.application(application, didFinishLaunchingWithOptions: launchOptions)
  }

  func didInitializeImplicitFlutterEngine(_ engineBridge: FlutterImplicitEngineBridge) {
    GeneratedPluginRegistrant.register(with: engineBridge.pluginRegistry)
    if let registrar = engineBridge.pluginRegistry.registrar(forPlugin: "QuickbuddyCalling") {
      let channel = FlutterMethodChannel(name: "quickbuddy/calling", binaryMessenger: registrar.messenger())
      channel.setMethodCallHandler { call, result in
        if call.method == "requestMicrophone" {
          AVAudioSession.sharedInstance().requestRecordPermission { allowed in
            DispatchQueue.main.async { result(allowed) }
          }
        } else if call.method == "keepAwake" {
          UIApplication.shared.isIdleTimerDisabled = true
          result(nil)
        } else if call.method == "releaseAwake" {
          UIApplication.shared.isIdleTimerDisabled = false
          result(nil)
        } else if call.method == "ring" {
          AudioServicesPlayAlertSound(SystemSoundID(1005))
          result(nil)
        } else if call.method == "stopRinging" {
          result(nil)
        } else {
          result(FlutterMethodNotImplemented)
        }
      }
    }
  }
}
