# Bulk customer import

Customer import is **not enabled**. The central Phase 12.A engine currently accepts branch CSV only. This phase does not create users, login credentials, verified contact methods, or overwrite existing identity records from spreadsheets. XLSX parsing, duplicate candidate review, consent provenance, invitation/verification, and a resumable worker are absent. Do not upload customer lists through the branch import screen.

A future implementation must stage PII with retention/encryption controls, normalize contacts, identify country/city, review uncertain matches, preserve source provenance, and create only unverified invitation candidates. It must never import passwords or imply marketing consent.
