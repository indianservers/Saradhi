# Bulk catalogue operations

The existing catalogue supports organization products, variants, and branch-specific prices/availability through individual APIs. Phase 5.A does not add CSV/XLSX upload/export, templates, dry runs, row error reports, 500-row batching, catalogue revisions, publication scheduling, or rollback.

Any future importer should parse in bounded batches, validate the full file before an all-or-nothing write (or clearly opt into partial success), audit row outcomes, and neutralize spreadsheet formula prefixes on export. Uploaded workbooks must be treated as data and never evaluated as macros or formulas. No bulk import is available in the merchant app today.
