# Customer accessibility and localization review

Date: 2026-10-26.

## Source inspection

The app uses Material widgets/theme, semantic labels for category and merchant tiles, tooltips for cart/quantity controls, form validators, visible error/retry states and ellipsis handling on selected merchant/address titles. Date/time formatting uses Flutter `MaterialLocalizations` after parsing backend timestamps to local time.

## Not verified / incomplete

No screen-reader, keyboard/focus, contrast, target-size, large text, dark mode or small/large viewport run was possible without Flutter. Some noninteractive images/cards and status text may need explicit semantics. Input coordinates do not have client-side latitude/longitude bounds checks; backend validation is authoritative. Touch-target and dynamic-font overflow review remains open.

Localization is not implemented as Flutter localization resources. Visible strings are mostly hardcoded English. Hindi and Telugu, currency locale formatting, RTL/focus-order review and translated UI are outstanding. Merchant/product names should remain backend-provided until an approved translation source exists.

Do not treat source-level semantics as an accessibility conformance result. Validate using TalkBack and large text on device before release.
