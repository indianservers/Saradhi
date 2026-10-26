# Merchant copilot

`POST /api/v1/ai/agents/merchant/query` requires an authorized branch and rechecks `ai.read` against its organization, city and branch. Evidence includes previous-24-hour non-cancelled merchant-order totals grouped by currency and currently unavailable stock-line count. It does not merge currencies or expose customer/order detail.

No action tools are enabled. The endpoint does not change price, stock, menu visibility, staff access or supplier orders. Branch analytics UI, demand-by-item forecasts, promotion suggestions and merchant approval flows remain future work.
