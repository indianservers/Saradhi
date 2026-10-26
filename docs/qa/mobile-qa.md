# Flutter mobile QA

Apps inventoried: Customer, Merchant, Pilot. Each has a Flutter manifest, one principal Dart entry point, and a widget-test file. Flutter and Dart executables are absent from this environment (`flutter --version` could not run); no Flutter analyze, widget test, Android SDK build, APK permissions inspection, or screenshot run is claimed.

Source inspection found Razorpay Flutter usage in the customer app and external Google Maps deep link in the pilot app. Secure token storage, Android location/background permissions, notification permission prompts, deep links/payment callback handling, offline recovery, session expiration, app restart, accessibility/touch target, and overflow remain unverified. Android and iOS native project directories were not available for a device build. No iOS/macOS build is claimed.

Release blocker: install supported Flutter/Android SDK in CI/device lab, run analyze/tests and all three Android builds, inspect merged manifests and secrets/storage, and execute lifecycle/location/payment callback tests. iOS requires macOS/Xcode and remains untested.
