# Pilot security and verification

The pilot workspace/profile and assignment read endpoints use `Actor.subject` to find the pilot; clients cannot choose another pilot ID. The assignment list includes only the authenticated pilot's offered/accepted/picked-up rows. Recipient address is omitted from the offer and disclosed after acceptance. Existing accept/pickup services still enforce assignment ownership and task state on the backend.

The real PostgreSQL integration scenario exercises two pilot identities racing for one task: exactly one offer succeeds, the other identity cannot accept the winner's assignment, the winner sees its own offer, the other pilot sees no assignment, and recipient address is withheld before then returned after acceptance. It also verifies the pilot earnings read returns an empty authoritative ledger for the fixture.

Not covered: OTP replay, photo proof storage, COD tampering, external maps, KYC documents, push/WebSocket channels, native permission UX, or platform build. No app security claim is inferred from hidden buttons.
