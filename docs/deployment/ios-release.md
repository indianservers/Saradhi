# iOS release readiness

Blocked: this Windows environment has no macOS/Xcode, so no iOS compilation, simulator/device QA, signing or archive was performed. No claim of successful iOS build.

On an approved macOS runner, inspect all three bundle IDs, display names, permission purpose strings, background location entitlement only for justified pilot tracking, notifications, maps, privacy manifests, App Transport Security, secure storage, deep links/payment callbacks, icons and launch screens. Confirm location handling and customer-facing disclosures with legal/privacy review. Test signing/provisioning via protected credentials and archive each scheme. Do not submit to App Store Connect without explicit approval.
