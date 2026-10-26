# Approval workflow boundaries

Existing single branch review and finance refund maker-checker decisions remain the authoritative approvals. The new importer creates only pending branches and never approves them. No “approve all” endpoint exists. Bulk decisions for merchant KYC, commission changes, settlement batches or high-risk changes must show per-record eligibility, require a distinct authorized checker where policy requires, recheck under lock and report each result.
