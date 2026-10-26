// Foundation smoke only. Does not measure order throughput or GPS processing capacity.
import http from 'k6/http';
import { check } from 'k6';
export const options = {
  scenarios: { baseline: { executor: 'constant-arrival-rate', rate: Number(__ENV.RPS || 20),
    timeUnit: '1s', duration: __ENV.DURATION || '60s', preAllocatedVUs: 20, maxVUs: 100 } },
  thresholds: { http_req_failed: ['rate<0.01'], http_req_duration: ['p(95)<300'] },
};
export default function () {
  const response = http.get(`${__ENV.API_BASE_URL || 'http://127.0.0.1:8000'}/health/live`);
  check(response, { 'live': r => r.status === 200 });
}
