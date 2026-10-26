# Cross-app end-to-end coverage

The backend integration suite exercises real API-backed PostgreSQL workflows, but does not automate all six user interfaces in one end-to-end journey. No Playwright config or browser E2E test suite was found. Web apps were typechecked and production-built; Flutter apps were not built because Flutter/Dart is absent.

| Journey | Current evidence | Result |
|---|---|---|
| Standard food checkout/order | Real API integration flow and checkout concurrency tests | Backend covered; UI journey not run |
| Multi-restaurant checkout/allocation | Existing integration checkout and child-order flows | Partial; three delivery task UI journey not run |
| Scheduled delivery | Recurring plan creates review-required occurrence only; no automatic order/charge | Partial; end-user scheduled delivery not complete |
| Grocery picking | Inventory/batch tests exist | Partial; full picker and pilot UI flow not run |
| Parcel | No complete parcel journey evidenced | Not run |
| Merchant onboarding/approval | Admin/merchant APIs exist, but full app journey not evidenced | Not run end-to-end |
| Pilot onboarding/approval | Pilot verification and assignment API tests exist | Partial; mobile workflow not run |
| Support complaint/resolution | API support workflow integration test passes | Backend covered; browser journey not run |
| Partial rejection/refund | API finance/refund tests cover selected flows | Partial; multi-merchant ledger end-to-end not run |
| Two-city isolation | Selected scoped API integration tests | Partial; complete UI/export/subscription matrix not run |

Browser screenshot capture, desktop/tablet visual comparison, session expiration, and target mockup comparison were not performed. `Target UI` assets were inventoried but not visually compared.
