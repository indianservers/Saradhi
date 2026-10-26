# Contract authority
FastAPI OpenAPI is authoritative. Run `python -m backend.scripts.export_openapi`, then
`npm run contracts`. Generated schema.d.ts is consumed by openapi-fetch; do not hand edit.
No response shapes are repeated in the six apps.

Dart toolchain (blocked until Java and Dart are installed):
Use pinned OpenAPI Generator CLI 7.17.0 via
`java -jar tools/openapi-generator-cli-7.17.0.jar generate -i packages/api_contracts/openapi.json -g dart-dio -o packages/dart_api_client --additional-properties=pubName=quickbuddy_api,serializationLibrary=json_serializable`.
Download the pinned jar from Maven Central and verify its published checksum before use. Requires Java 11+.
Then run `dart pub get` and `dart run build_runner build --delete-conflicting-outputs`
inside packages/dart_api_client; keep the generated client and its lockfile together.
The `dart-dio` and `json_serializable` options are described in the
[official generator documentation](https://openapi-generator.tech/docs/generators/dart-dio/).
Use the [official JAR installation instructions](https://openapi-generator.tech/docs/installation/)
with the pinned version above. This toolchain has been documented, not executed locally.
Add generated client as path dependency of flutter_networking and inject createTransport's Dio;
do not manually implement health/identity response models. No Dart API response consumers exist yet.

Conventions: /api/v1; X-Request-ID; RFC3339 UTC timestamps; cursor pagination with opaque
next_cursor and bounded limit (1..100) for future collections; stable error envelope.
Money: integer minor units encoded as decimal strings with ISO currency and explicit scale,
or exact Decimal at calculation boundaries; never IEEE floating point. Currency rounding
and zero/three-decimal currencies must be specified in Phase 2. Tokens are supplied through
TokenProvider/TokenStore; no embedded signing secrets or token persistence in localStorage.
