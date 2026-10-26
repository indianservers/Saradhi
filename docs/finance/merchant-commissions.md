# Merchant commissions

The repository contains typed commission-policy/rule records, but the checkout and settlement paths do not yet select a policy by country/city/category/merchant/branch precedence, snapshot an effective rule on every merchant order, or calculate and post commission liabilities.

Required before activation: explicit precedence and tie-breaking, effective-date interval validation, fixed/percentage/minimum/maximum behavior, funding-source treatment, policy preview, approval for high-impact changes, immutable order snapshots, and regression tests proving historical orders do not change when a new policy is effective.
