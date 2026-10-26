# Role and permission matrix

The app gates are convenience boundaries; backend permissions remain decisive.

| Role | Admin app route | Backend capability used here |
| --- | --- | --- |
| `platform_super_admin` | Company, city operations, support | Existing dispatch/fleet/incident checks; model registry; support operations |
| `company_admin` | Company administration | City-scoped dispatch/fleet/incident permission only where current assignments permit; existing merchant branch browse is read-only |
| `city_manager` | City operations | `dispatch.write` within assigned city; incident operations |
| `city_operator` | City operations | Explicit city-only `dispatch.write` assignment; incident operations |
| `support_agent` | Support console | `support.write`; claimed ticket ownership and support scope |

The web app accepts the backend `/me` role set only after successful token verification. The backend checks active database assignments and scope on each protected operation. This does not implement role assignment/delegation, country/zone scope administration, or a complete permission matrix UI. See `backend/migrations/versions/20261026_0002_roles.py` for seeded roles and permissions.
