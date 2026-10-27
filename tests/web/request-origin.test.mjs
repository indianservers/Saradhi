import { test } from 'node:test';
import assert from 'node:assert/strict';
import { isSameOrigin } from '../../packages/web_design_system/src/request-origin.ts';

const cases = [
  ['normal local browser', 'http://localhost:3000', 'localhost:3000', true],
  ['Next normalized loopback URL', 'http://127.0.0.1:3000', '127.0.0.1:3000', true],
  ['different port', 'http://localhost:3001', 'localhost:3000', false],
  ['different scheme', 'https://localhost:3000', 'localhost:3000', false],
  ['foreign site', 'https://attacker.example', 'localhost:3000', false],
  ['subdomain is not same origin', 'http://sub.localhost:3000', 'localhost:3000', false],
  ['loopback alias cannot cross target Host', 'http://localhost:3000', '127.0.0.1:3000', false],
  ['missing origin', null, 'localhost:3000', false],
  ['opaque origin', 'null', 'localhost:3000', false],
  ['malformed origin', 'not a URL', 'localhost:3000', false],
  ['URL fallback without Host', 'http://localhost:3000', null, true],
  ['credentials cannot disguise foreign host', 'http://localhost:3000@evil.example', 'localhost:3000', false],
];
for (const [name, origin, host, expected] of cases) {
  test(name, () => {
    const headers = new Headers();
    if (origin) headers.set('origin', origin);
    if (host) headers.set('host', host);
    assert.equal(isSameOrigin(new Request('http://localhost:3000/api/session', {headers})), expected);
  });
}
