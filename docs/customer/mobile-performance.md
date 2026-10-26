# Customer mobile performance review

Date: 2026-10-26.

## Measured results

No cold/warm start, time-to-content, frame, image-decode, memory, search-latency or checkout-latency measurements were collected. Flutter/Dart, Android SDK and a representative Android device/emulator are unavailable. A 60 FPS claim is not supported.

## Source-level observations

- Home requests public branches first and launches address, order and recommendation requests asynchronously; nearby section has a skeleton.
- Merchant and catalogue requests are bounded/paginated; catalogue search debounces 300 ms and cancels stale requests.
- Horizontal discovery/recommendation rails use lazy `ListView` builders. Merchant screens map local WebP package assets.
- Tracking polls at 15 seconds with an overlap guard and timer disposal.
- Current customer screens are implemented in a large `main.dart` file. Per-feature state isolation and API/client separation are follow-up architecture work; no broad rewrite was made.

## Device measurement plan

On representative low/mid-range Android, profile release mode and record cold start, warm start, first useful merchant content, list scroll frame timings, image decode/cache memory, debounced search response, cart mutation response, quote-to-confirm latency, tracking jank and peak memory. Repeat at small, medium and large viewports and with slow/lost network. Save device/model/build mode and raw profile outputs beside the results. Until then, performance is **not measured**.
