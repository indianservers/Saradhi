# Customer segmentation

`POST /api/v1/admin/customer-segments/preview` accepts one city and up to ten typed conditions with AND/OR grouping. The allowlist is status, order count, gross purchase value, dormant days, and latest explicit marketing consent by channel. It returns an exact current count and normalized definition without exposing customer rows. SQL fields/operators are selected by backend code; raw SQL is not accepted. Preview actions are audited and run under the caller's city/organization permissions.

The Company Admin has a small minimum-orders/dormant-days preview form. Definitions are not saved, so there is no live membership history, schedule, queue, or event-driven refresh. Category, subscription, coupon redemption and zone fields are not currently available as segment conditions; saved audience exports are intentionally not included.
