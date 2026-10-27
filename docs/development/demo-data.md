# Local demo data

Populate the isolated local development database with synthetic records for the customer,
restaurant, grocery, delivery pilot, support, geography, catalogue, inventory, and order flows:

```powershell
./.venv/Scripts/python.exe -m backend.scripts.seed_demo_data
```

The command accepts only `APP_ENV=development` and PostgreSQL `quickbuddy_dev` at
`127.0.0.1:5433` (or an equivalent loopback name). It does not touch `quickbuddy_test`, any
remote database, production services, real payment providers, SMS, or third-party APIs. It uses
the API's authenticated registration and business operations for the demo records. A repeated
run verifies the existing demo set and does not duplicate or rewrite it. If an earlier run was
interrupted, the command detects the partial seed and stops for inspection rather than guessing
which records to repair.

The script creates these local-only login identities:

| Role | Email |
| --- | --- |
| Platform demo administrator | `demo.admin@example.test` |
| Customer | `demo.customer@example.test` |
| Second customer | `demo.customer2@example.test` |
| Restaurant owner | `demo.restaurant@example.test` |
| Grocery owner | `demo.market@example.test` |
| Delivery pilot | `demo.pilot@example.test` |
| Support agent | `demo.support@example.test` |

Passwords are randomly generated and stored in ignored `.secrets/quickbuddy-demo-accounts.json`;
the script never prints them. Keep that file private and do not copy the demo identities or
credentials into staging or production. The demo administrator and support agent have broad
local-only permissions by design.

The sample order is pickup and has no payment intent. Payment, payout, messaging, and live
delivery integrations remain disabled; the seed does not simulate provider settlement or
real-time GPS movement.
