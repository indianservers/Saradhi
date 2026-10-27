# Role × permission matrix (implemented catalog)

Source: `identity.roles` / `identity.role_permissions`, seeded by `backend/migrations/versions/20261026_0002_roles.py` and extended by migrations 0010, 0018, 0019, 0021. `✓` means grant exists in the catalog, not that every endpoint has been exercised. Endpoint enforcement is only PASS where cited tests executed.

| Implemented role | geo.write | merchant.write | kitchen.manage | merchant.approve | merchant.export | catalog.write | inventory.read | inventory.write | dispatch.write | pilot.verify | finance.read | finance.write | finance.configure | support.write | audit.read | organization.members | customer.read | ai.read | ai.manage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| platform_super_admin | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| company_admin | — | ✓ | — | ✓ | ✓ | ✓ | ✓ | — | ✓ | — | — | — | — | — | ✓ | ✓ | ✓ | ✓ | — |
| country_manager | — | — | — | ✓ | — | — | — | — | ✓ | — | — | — | — | — | ✓ | — | — | ✓ | — |
| city_manager | — | — | — | ✓ | ✓ | — | — | — | ✓ | — | — | — | — | — | ✓ | — | ✓ | ✓ | — |
| city_operator | — | — | — | — | — | — | ✓ | — | ✓ | — | — | — | — | — | — | — | — | ✓ | — |
| zone_manager | — | — | — | — | — | — | — | — | ✓ | — | — | — | — | — | — | — | — | ✓ | — |
| merchant_owner | — | ✓ | ✓ | — | — | ✓ | ✓ | ✓ | ✓ | — | — | — | — | — | ✓ | ✓ | — | ✓ | — |
| branch_manager | — | ✓ | ✓ | — | — | ✓ | ✓ | ✓ | ✓ | — | — | — | — | — | — | — | — | ✓ | — |
| kitchen_operator | — | — | ✓ | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| delivery_fleet_manager | — | — | — | — | — | — | — | — | ✓ | — | — | — | — | — | — | — | — | — | — |
| delivery_pilot | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| support_agent | — | — | — | — | — | — | — | — | — | — | — | — | — | ✓ | — | — | — | — | — |
| finance_manager | — | — | — | — | — | — | — | — | — | — | ✓ | ✓ | — | — | ✓ | — | — | — | — |
| customer | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

`ai.read`, `ai.manage`, and `customer.read` were migration-derived grants; customer.read is granted to platform super admin, company admin, and city manager. `merchant.export` is granted to platform super admin, company admin, city manager. `—` means no catalog grant. “Create/edit/approve/delete/assign/refund/settle/configure” are endpoint-specific actions; the coarse permission catalog does not provide a distinct grant for every action.

## Evidence and gaps

- **PASS, exercised paths:** customer order ownership and lifecycle, merchant branch/order flows, pilot entity/location scope, city manager/operator city scope, finance approval queue scope, support ticket claim/reply/resolve and ownership. See integration suite, especially `test_vertical_slice.py`, `test_reliability.py`, `test_admin_support.py`, `test_finance_approval_queue.py`.
- **NOT RUN:** direct enforcement for every permission/action and every one of the 14 roles; UI navigation is not authorization evidence.
- **Resolved in security hardening:** migration `20261027_0021` replaces `kitchen_operator`'s `merchant.write` and `inventory.read` grants with branch-scoped `kitchen.manage`. `test_security_hardening.py` verifies permitted kitchen work and denial of cross-branch, merchant administration, inventory, and role escalation.

Requested labels absent from catalog (not fabricated): Financial Auditor, Merchant Approval Officer, Pilot Approval Officer, Marketing Administrator, Reporting Analyst, Dispatcher, Fleet Supervisor, Operations Viewer, Restaurant Administrator, Organization Manager, Kitchen Manager, Kitchen Staff (catalog name is `kitchen_operator`), Catalogue Editor, Inventory Manager, Merchant Finance Viewer, Corporate Customer, Corporate Account Administrator, Support Administrator, Support Manager, Refund Reviewer, Refund Approver. Some responsibilities may be represented by current roles, but no equivalence is assumed.
