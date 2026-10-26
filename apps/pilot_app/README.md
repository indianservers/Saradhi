# Quickbuddy Pilot App
Flutter source bootstrap: Riverpod, GoRouter, shared theme, Dio, secure token-store contract,
English/Hindi framework localization and environment defines. No user data or business logic.

BLOCKED locally: Flutter/Dart SDK and Android tools are unavailable. Platform runners and
lockfiles have not been generated or built. Install SDK explicitly, then from root run:
`./tools/dev.ps1 flutter-init -App pilot_app`

The initializer generates runners in a temporary folder and copies only missing platform files;
it preserves main.dart, pubspec.yaml and tests. Requires Flutter supporting Dart >=3.9.
Then `./tools/dev.ps1 mobile -App pilot_app` (web, port 8080/8081/8082), or from this folder:
`flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000` for Android emulator.
Build: `flutter build web`; test: `flutter test`; lint: `flutter analyze`.
Supply `--dart-define=APP_ENV=production --dart-define=API_BASE_URL=https://api.example.com` for release.
Before device release configure Keychain/Keystore and Android backup exclusion per flutter_secure_storage;
production HTTPS only, no broad cleartext exception. ARB business translations arrive with screens.
