# Location privacy

Location submissions require authenticated pilot identity and explicit versioned consent. Consent history is append-only. Only assigned active tasks expose fresh pilot coordinates to the order owner; phone numbers are omitted. City and merchant APIs are scoped. GPS samples expire according to configured retention and use limited fields. Consent revocation disables availability and attempts Redis cache cleanup.

Sensitive location access auditing, export controls, device binding, TLS deployment, secure key management, and jurisdiction-specific retention/legal review remain deployment requirements. This local test validates selected access paths, not a full privacy certification.
