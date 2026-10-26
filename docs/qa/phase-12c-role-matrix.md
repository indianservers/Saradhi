# Phase 12.C role test matrix

Role catalog count: **14**. Roles with directly exercised role-specific backend authorization paths in this run: **5 seeded roles** (`platform_super_admin`, `city_manager`, `city_operator`, `support_agent`, `finance_manager`), plus baseline `customer` ownership/auth paths. This is six role identities/contexts; it is not all-role login coverage. Pilot entity ownership paths were exercised without establishing a `delivery_pilot` role assignment. The remaining 8 seeded roles were NOT RUN as role-specific login/permission matrices.

| Role | Auth/login as role | API functional/permission evidence | UI login/navigation | Overall |
|---|---|---|---|---|
| platform_super_admin | PASS, test fixture | PASS, geography/admin setup and integrated workflows | NOT RUN | Partial |
| company_admin | NOT RUN | NOT RUN as assigned role | BLOCKED | NOT RUN |
| country_manager | NOT RUN | NOT RUN | BLOCKED | NOT RUN |
| city_manager | PASS, scoped assignment | PASS, city-scoped workflow | BLOCKED | Partial |
| city_operator | PASS, city-scoped assignment | PASS, allowed/denied city fleet scope | BLOCKED | Partial |
| zone_manager | NOT RUN | NOT RUN | BLOCKED | NOT RUN |
| merchant_owner | NOT RUN as role; owner resource flows exercised | PASS, merchant ownership flows, not role grant coverage | BLOCKED | Partial |
| branch_manager | NOT RUN | NOT RUN as assigned role | BLOCKED | NOT RUN |
| kitchen_operator | NOT RUN | NOT RUN | BLOCKED | NOT RUN |
| delivery_fleet_manager | NOT RUN | NOT RUN | BLOCKED | NOT RUN |
| delivery_pilot | NOT RUN as role; pilot entity endpoints exercised | Partial, pilot ownership/scope | BLOCKED | Partial |
| support_agent | PASS | PASS, ticket scope/ownership | BLOCKED | Partial |
| finance_manager | PASS, organization scope | PASS, finance queue scope | BLOCKED | Partial |
| customer | PASS, generated identity | PASS, customer-owned workflows and denial tests | BLOCKED | Partial |

Web route shell HTTP checks are not authenticated UI tests. See [role-permission-matrix.md](role-permission-matrix.md) for the full catalog and route enforcement evidence.
