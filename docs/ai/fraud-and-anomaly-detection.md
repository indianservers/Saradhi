# Risk signals and anomaly detection

`GET /api/v1/ai/risk/orders/{order_id}` and `/deliveries/{delivery_id}` emit review-only delay signals for long-pending merchant acceptance, long preparation state, and ready-but-unassigned deliveries. Signals include reason codes, rule version/provenance and a privacy-preserving subject digest in `intelligence.ai_risk_signals`.

Existing GPS ingestion already quarantines implausible jumps for review. These checks are not fraud findings. They never cancel an order, ban a user, withhold payout or accuse a pilot. Coupon, refund, incentive, collusion and payment anomaly models await governed labels and authorized case-review workflows.
