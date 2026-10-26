# Model gateway

Configure `AI_PROVIDER=disabled|openai_compatible|local`, `AI_BASE_URL`, `AI_MODEL`, optional `AI_API_KEY`, `AI_TIMEOUT_SECONDS` and `AI_MAX_OUTPUT_TOKENS`. Defaults require no credentials and return a deterministic summary of verified evidence. Production-enabled endpoints must use HTTPS. The operator is responsible for selecting an approved provider endpoint.

The gateway sends only a bounded question and an allowlisted evidence object. Common email, phone and street-address patterns are redacted; evidence keys for addresses, phone, email, secrets and payment tokens are dropped. Merchant/customer descriptions and message bodies are not retrieved. Retrieved values are labeled untrusted in the system instruction. No model has tools to call after inference.

Calls have a 30-second absolute configuration ceiling, an eight-request in-process concurrency bound, an output-token cap and a Redis-backed per-user request limit. Provider timeout, transport error, invalid response and unavailable Redis cause deterministic fallback. Cost attribution by provider usage is not yet persisted; cost caps need provider-specific pricing and account configuration.
