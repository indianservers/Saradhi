# Android release readiness

Three Flutter applications: customer, delivery pilot, merchant. Flutter/Dart/Android SDK were unavailable on this Windows runner, so no `flutter analyze`, tests, APK/AAB, package inspection or signing validation occurred. No release artifacts were produced.

Before release: verify application IDs, display names, version name/code, launcher/splash assets, target SDK, secure HTTPS, permissions and privacy disclosures; justify background location for pilot app, foreground service/notification behavior and notification permission; restrict Maps/Firebase keys; configure deep links/payment callbacks; provide privacy policy and data-safety form, store listing/screenshots and support contact. Run analyze, tests, release bundle build and device QA for all three apps. Use Play App Signing and secret-backed signing; never commit keystore/password. No Play upload occurred.
