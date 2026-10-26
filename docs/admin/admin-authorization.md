# Admin authorization

The browser receives HTTP-only session cookies from the app's auth routes. The server proxy uses a strict route allowlist, same-origin checks for writes, JSON content-type and body-size checks, and forwards the access token to the API. It does not let the browser choose an arbitrary upstream URL.

Every sensitive API decision uses current database role assignments and organization/city/branch scope. Finance organization discovery is limited to finance-read assignments plus active memberships; platform super admin listing is global. The frontend is not an authorization boundary. Missing or revoked backend permission must fail closed.
