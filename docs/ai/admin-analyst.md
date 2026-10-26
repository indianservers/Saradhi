# Company admin analyst

`POST /api/v1/ai/agents/admin/query` requires an organization and current `finance.read` scope. The current report groups payment-intent counts and amounts by currency and status, sourced from authoritative payment intents associated with the organization. It explicitly labels these as payment activity, not recognized revenue or ledger balances.

The assistant cannot post journals, approve refunds/settlements, change bank details or request global data outside the caller's scope. City/category analytics and executive UI are not included yet.
