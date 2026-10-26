# Pilot registration and onboarding

The current API supports account registration/login and `POST /api/v1/pilots` with an active city ID. The app now supports email/password account registration/login, restores the shared session, loads active cities, and creates a pilot profile using the selected city. Server verification remains required before availability can be enabled.

The underlying API does not collect full name, phone, date of birth, address, photo, vehicle eligibility, licence, insurance, identity documents, emergency contact, payout details, or additional-information review. The UI states this limitation; it does not improvise document or bank-data storage. Company staff retain the existing server-side pilot verification authority.

SMS OTP and biometric unlock are not configured for this client. The shared networking interceptor handles access-token refresh and clears invalid sessions.
