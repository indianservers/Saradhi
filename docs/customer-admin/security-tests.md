# Customer administration security evidence

Focused PostgreSQL integration tests cover: customer-only directory listing under platform-admin authorization, city-filtered results, masked email, a real order in Customer 360, bounded order history and all eleven history tabs, masked-field CSV export with no-store, denial for an unprivileged identity, exact segment preview combining order count and latest opt-out evidence, customer-owned consent updates, verified-contact gates, idempotent replay, and database-enforced consent immutability. Tests do not yet cover every organization/city permutation, export link leakage, customer import conflicts, account restrictions, AI escalation, or campaign sends.

The new backend uses a database `customer.read` grant (added by migration `20261027_0019`) and filters non-global results through organization/city-scoped orders. Exports carry only masked contact values. Full adversarial security testing is still required before launch.
