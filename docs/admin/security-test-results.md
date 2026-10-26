# Security test results

## Implemented controls

- Three workspace route groups require verified backend roles; the root pages redirect into protected workspaces.
- Login tokens are set as HTTP-only, SameSite=Lax cookies; logout revokes the refresh session when possible and always clears local cookies.
- Backend proxy routes use exact path/method allowlists, require a session, reject cross-origin mutations, cap JSON request bodies, and disable caching.
- Dispatch and incident APIs continue to enforce database-backed city scope. Ticket claims use row locks; only the current assignee may read conversation content, reply, or resolve.
- Support queue/read/claim/resolve actions write audit records. List responses omit customer IDs and contacts.

## Executed checks

- PostgreSQL integration test for customer/agent access, claim conflict, conversation access, reply, and resolution: passed.
- Organization-scoped agent cannot see an unscoped customer's ticket: passed.
- City operator's authorized-city list excludes another city and the dispatch API rejects that city: passed.
- Existing pagination/fresh migration assertion updated to head revision `20261026_0014`: passed.
- Full backend and PostgreSQL integration suite after migration `20261026_0015`: 74 passed, 1 dependency deprecation warning.

This is not a complete OWASP assessment. Cross-city denial, browser CSRF, session expiry/revocation behavior in a real browser, websocket auth, exports, and the other Phase 7 security scenarios still need dedicated tests.
