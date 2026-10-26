# Customer AI copilot

No customer CRM tools were added to the AI platform. Existing AI agents do not receive customer order histories, consent, or CRM exports through this feature. Any future customer metric tool must query bounded aggregates under the caller's `customer.read` scope, reject raw SQL and sensitive export requests, and never send campaign messages without an approved workflow.
