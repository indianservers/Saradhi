# Quickbuddy Customer App
Flutter customer client with discovery, authentication, saved addresses, cart, checkout, order history, tracking and support. Uses the shared API and secure token storage.

Android, iOS and web platform runners are included. If runners are missing in another checkout, install Flutter and run:
`./tools/dev.ps1 flutter-init -App customer_app`

The initializer generates runners in a temporary folder and copies only missing platform files;
it preserves main.dart, pubspec.yaml and tests. Requires Flutter supporting Dart >=3.9.
Then `./tools/dev.ps1 mobile -App customer_app` (web, port 8080/8081/8082), or from this folder:
`flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000` for Android emulator.
Build: `flutter build web`; test: `flutter test`; lint: `flutter analyze`.
Supply `--dart-define=APP_ENV=production --dart-define=API_BASE_URL=https://api.example.com` for release.
Before device release configure Keychain/Keystore and Android backup exclusion per flutter_secure_storage;
production HTTPS only, no broad cleartext exception. ARB business translations arrive with screens.

## Physical Android QA

Start the local API and seed demo data as described in `docs/development/demo-data.md`.
Use `adb -s <serial> reverse tcp:8000 tcp:8000` to reach the local API over USB.
From this app directory, run:

```powershell
flutter test integration_test/device_flows_test.dart -d <serial> --dart-define-from-file=../../.secrets/device-customer.json
```

The ignored JSON file must provide `API_BASE_URL` (`http://127.0.0.1:8000`),
`QA_EMAIL`, and `QA_PASSWORD` for a synthetic local account. Never commit it or use real
customer credentials. The test changes that account's cart. It checks checkout's disabled
payment state in the default local configuration; it does not make a real payment.
For this Windows Java installation, a short process-local `TEMP`/`TMP` directory avoids
Java's loopback socket failure when the Windows temporary path uses a short user name.
Debug builds allow local HTTP; release builds do not opt into cleartext traffic.

`integration_test/account_actions_test.dart` also creates synthetic saved addresses and
support requests, and checks address management and logout.
`integration_test/sandbox_checkout_test.dart` requires a separate local backend with
`SANDBOX_PAYMENTS_ENABLED=true` and a generated `SANDBOX_WEBHOOK_SECRET` of at least
32 characters. Point its private defines file at that backend. It places a synthetic
pickup order, verifies the simulated payment, and checks that the consumed cart is cleared.
Keep Razorpay disabled for this test.

In-app audio calling is available for active assigned deliveries. See
[calling setup and background limits](../../docs/customer/in-app-calling.md).
