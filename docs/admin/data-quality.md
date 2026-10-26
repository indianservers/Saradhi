# Data quality status

Current importer checks CSV shape/UTF-8/bounds, required values, UUIDs, coordinate ranges, active city, brand scope, duplicate external references and possible same-name branch candidates. Similar names are warnings, not automatic matches. Existing database uniqueness/check constraints remain in force.

No general duplicate center, cross-entity matching, orphan report or merge workflow exists. Never merge customer identities or legal organizations based only on similarity. A future merge must lock and preserve order/ledger foreign references, have a verified match decision and append audit evidence.
