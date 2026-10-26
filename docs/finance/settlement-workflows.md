# Settlement workflows

Settlement batches, lines, merchant/pilot payable records and payout request foundations exist in PostgreSQL. There is no Phase 8 calculation/review/approval/submission/reconciliation API or UI, and no bank payout integration. An internal approved record must never be shown as a completed transfer.

Required statuses are draft, calculated, reviewed, approved, submitted, confirmed, failed, and reconciliation required. Implement separate merchant and pilot schedules, approval separation, immutable batch lines, instruction references, provider/bank callbacks, and reconciliation before enabling payouts. Route/payout adapter flags are deliberately rejected by configuration validation.
