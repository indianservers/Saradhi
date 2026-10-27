# In-app customer and delivery-partner calling

The customer can use **Call delivery partner** on order tracking. The assigned partner
can use **Call customer** on the pickup/delivery screen. Both sides receive an incoming
call screen with Answer and Decline. Calls include mute, speaker/earpiece, and End call.
Phone numbers are not exchanged. Audio uses WebRTC; the API carries signaling only.

Calling is limited to the active, accepted assignment for a delivery in `assigned` or
`picked_up` state. Unrelated users, offered/rejected assignments, cancelled orders,
and finished deliveries cannot initiate or continue a call. Each participant can have
one live call. Unanswered calls expire after 45 seconds; accepted calls have a 30-minute
limit. The API rechecks assignment ownership during signaling. Sign-out, hang-up,
removing the app task, or repeated connection failure releases the microphone.

## Current availability

Incoming calls currently require the recipient app to be open and connected. Incoming
ringing polls while the app is in the foreground. Closed-app ringing needs a separate
FCM/APNs and native incoming-call integration.

On Android, user-started or answered calls use a microphone foreground service with
an ongoing call notification. An active call can continue while using maps, switching
apps, or locking the screen. Return to the call or end it from the notification.
Microphone permission is required; notification permission makes the ongoing control
visible in the notification drawer. The service is not started automatically at boot
and does not restart a terminated call. Removing the app task ends its call.

Other platforms currently end calls on app suspension. No calls are recorded.

## Deployment

Run database migrations before starting the new API. `CALLING_ENABLED=false` disables
calling. Development/test builds can connect directly on a reachable network using
the configured STUN servers. Reliable calls across mobile networks need a TURN relay;
see the [WebRTC TURN guide](https://webrtc.org/getting-started/turn-server).

Set `CALL_TURN_URLS` to a JSON array of your `turn:`/`turns:` URLs and configure
`CALL_TURN_SECRET` with a server-only shared secret of at least 32 characters. The
TURN server must support time-limited REST/HMAC credentials, as provided by coturn's
`use-auth-secret` mode. Clients receive per-user credentials valid for one hour;
the shared secret never reaches the apps. Staging/production calling remains
unavailable until TURN URLs are configured. Production API traffic requires HTTPS.

The API removes signaling when a call ends or when it detects expiry/revocation.
A minute-by-minute cleanup also purges expired signaling and call metadata older
than seven days. No SDP, ICE candidates, credentials, or audio enter application logs.

## Validation

`tests/integration/test_voice_calls.py` uses real local PostgreSQL to exercise both
directions, participant authorization, busy races, decline, expiry, reassignment,
audio-only signaling validation, and signaling cleanup. Shared Flutter tests cover
incoming decline and microphone denial before ringing the other participant.

For device QA, run `python -m tools.qa_voice_fixture` against the authorized local
`TEST_DATABASE_URL`. It only accepts `quickbuddy_test` on loopback, creates synthetic
records, and saves private device defines under ignored `.secrets`. Run the
`integration_test/voice_call_test.dart` file in both apps concurrently against that
test API. The test checks actual sent/received audio packet counters in both call
directions, mute, speaker switching, and hang-up. A successful transport check does
not measure perceived speech quality or prove connectivity across every carrier.

Latest local validation: 15 backend checks and six Flutter tests passed; both Android
debug builds compile. The Android foreground microphone service was observed running.
The direct emulator-to-browser test received and answered a call but timed out before
audio connected. Physical two-device audio verification is pending USB reconnection;
no successful bidirectional audio transport result is claimed.
