# Multi-category checkout

The shared cart can group line items into merchant orders under one parent order and snapshots the confirmed quote. It currently requires one currency. Each product is revalidated for branch ownership, stock, current price, merchant hours, window, category and fulfillment at quote/checkout. Regulated and unsupported tax/option/variable-weight cases are rejected.

Different per-merchant delivery addresses/windows, category compatibility rules, independent merchant tax/discount/commission calculations and partial capture/refund settlement are not complete. Do not merge incompatible parcel or regulated flows into ordinary checkout.
