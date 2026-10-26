# Loyalty and referrals

Customer 360 reads the existing `engagement.loyalty_accounts`, immutable `loyalty_transactions`, referral programs and referrals. This is a read-only view. No new points, reversals, referral rewards, tiers, earn/redeem rules or cash-like wallet operations were added. A future write flow must use the existing idempotency key and movement ledger, enforce reward eligibility and audit maker/checker decisions.
