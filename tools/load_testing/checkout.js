// Requires a dedicated TEST API and explicitly prepared test inventory/slots.
// No traffic is sent until setup verifies the API's test-only environment header.
import http from 'k6/http';
import { check, fail } from 'k6';
const average = 10000 / 86400;
const multiplier = Number(__ENV.PEAK_MULTIPLIER || 10);
const perMinute = Math.ceil(average * multiplier * 60);
export const options = {
  scenarios: { checkout: { executor: 'ramping-arrival-rate', startRate: 7,
    timeUnit: '1m', preAllocatedVUs: Number(__ENV.VUS || 50), maxVUs: Number(__ENV.MAX_VUS || 1000),
    stages: [{ target: perMinute, duration: '2m' }, { target: perMinute, duration: __ENV.DURATION || '10m' },
             { target: perMinute * Number(__ENV.BURST_MULTIPLIER || 10), duration: '1m' }] } },
  thresholds: { checks: ['rate>0.99'], http_req_failed: ['rate<0.01'] },
};
const base = __ENV.API_BASE_URL || 'http://127.0.0.1:8001';
export function setup() {
  if (!__ENV.TOKEN || !__ENV.BRANCH_ID || !__ENV.VARIANT_ID || !__ENV.WINDOW_ID || !__ENV.RUN_ID)
    fail('Supply TOKEN, BRANCH_ID, VARIANT_ID, WINDOW_ID and a unique RUN_ID from dedicated test fixtures');
  const response = http.get(`${base}/health/live`);
  if (response.headers['X-Quickbuddy-Environment'] !== 'test') fail('Refusing load against a non-test API');
}
export default function () {
  const params = { headers: { Authorization: `Bearer ${__ENV.TOKEN}`, 'Content-Type': 'application/json' } };
  const cart = http.post(`${base}/api/v1/carts`, null, params);
  if (!check(cart, { 'cart created': r => r.status === 201 })) return;
  const id = cart.json('id');
  const item = http.post(`${base}/api/v1/carts/${id}/items`, JSON.stringify({
    branch_id: __ENV.BRANCH_ID, variant_id: __ENV.VARIANT_ID, window_id: __ENV.WINDOW_ID,
    quantity: '1', delivery_method: 'pickup' }), params);
  if (!check(item, { 'item added': r => r.status === 201 })) return;
  const quote = http.post(`${base}/api/v1/carts/${id}/quote`, null, params);
  if (!check(quote, { 'quote created': r => r.status === 201 })) return;
  params.headers['Idempotency-Key'] = `${__ENV.RUN_ID}-${__VU}-${__ITER}`;
  const order = http.post(`${base}/api/v1/orders/confirm`, JSON.stringify({ quote_id: quote.json('id') }), params);
  check(order, { 'checkout confirmed': r => r.status === 201 });
}
