# Global search

An unrestricted global search is not available. Search requires resource-specific indexes and explicit authorization filters for orders, customers, merchants, incidents, and tickets. The current APIs do not define such a contract, so the console does not simulate search across loaded tables or leak records across scopes.

Future search should authorize before returning results, apply per-resource scope, minimize personal data, audit sensitive lookups, and use cursor pagination. Search results should deep-link only to detail routes that repeat the same backend authorization checks.
