# Merchant pickup

The pilot sees merchant name/location and order-line summary for its own assignment. `Confirm pickup` is enabled only when the server reports the merchant order as ready. The app posts the task's current version to `POST /api/v1/delivery-tasks/{task_id}/pickup`; the backend checks that the authenticated actor owns the active pilot assignment and that merchant preparation is ready. The app reloads authoritative task state after success or failure.

GPS geofence, QR/OTP pickup, package-count capture, pickup exception reasons, and merchant-side handover acknowledgement are not supported by the current API. Location alone never confirms pickup.
