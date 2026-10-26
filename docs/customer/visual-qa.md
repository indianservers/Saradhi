# Customer visual QA

The app retains the Phase 3 Quickbuddy palette, shared `QuickbuddyApp`, `QbBrand`, `QbPanel`, `QbSectionTitle`, `QbPrimaryButton` and related design-system components. The target UI reference crops are under `docs/ui/reference-crops/`.

This environment has no Flutter or Dart executable, Android SDK, or iOS/macOS toolchain. As a result no widget screenshot, pixel comparison, analyzer output, Android build, or iOS build can be produced here. The current UI has been refocused on functional API states; device-level responsiveness and visual comparison remain required on a Flutter-enabled machine.

The app deliberately uses explicit loading/error/empty states and provider-limit notices in place of fabricated merchant, menu, address, payment or tracking data.
