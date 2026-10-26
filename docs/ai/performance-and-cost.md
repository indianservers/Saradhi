# AI performance and cost

AI endpoint usage is limited to 20 requests per authenticated user per Redis minute, with deterministic fallback when Redis is unavailable. The gateway has an eight-request in-process semaphore, configurable request timeout capped at 30 seconds, output cap up to 1,200 tokens, and bounded evidence size. Provider response latency and fallback status are returned and retained in inference metadata.

No live provider credentials were configured, so no external latency, token use, cost, cache hit rate, CPU/memory load or provider availability measurement exists. Existing Phase 2.C dispatch smoke timings are not fleet capacity benchmarks. Checkout, payment and dispatch transactions do not call the LLM gateway.
