"""Bounded, synthetic, local ASGI/PostgreSQL workload; never production traffic."""

import asyncio
import json
from pathlib import Path
from time import perf_counter

from httpx import ASGITransport, AsyncClient

from tests.integration.helpers import checkout, world


async def test_mixed_app_load_preserves_cart_and_role_invariants(api):
    client, app = api
    state = await world(client, app, 1)
    customer, shop = state["customer"], state["shops"][0]
    _, _, order, _ = await checkout(client, customer, [shop])
    evidence = {
        "scope": "Local ASGI + PostgreSQL; synthetic fixtures; excludes network/carrier capacity",
        "profiles": [],
    }
    for concurrency, journeys in [(1, 12), (10, 60), (30, 120)]:
        # Separate modeled networks per profile; retain all real API protections.
        workload = AsyncClient(
            transport=ASGITransport(app=app, client=(f"127.88.0.{concurrency}", 123)),
            base_url="http://test",
        )
        gate = asyncio.Semaphore(concurrency)
        timings, failures = [], []
        route_timings = {}

        async def request(
            method,
            path,
            expected,
            timings=timings,
            failures=failures,
            workload=workload,
            route_timings=route_timings,
            **kwargs,
        ):
            started = perf_counter()
            response = await workload.request(method, "/api/v1" + path, **kwargs)
            duration = (perf_counter() - started) * 1000
            timings.append(duration)
            family = (
                "tracking"
                if path.endswith("/tracking")
                else "company_dispatch"
                if "/operations/" in path
                else "merchant_queue"
                if path.startswith("/merchant/")
                else "catalog"
                if path.startswith("/catalog/")
                else "cart_read"
                if method == "GET"
                else "cart_write"
            )
            route_timings.setdefault(family, []).append(duration)
            if response.status_code != expected:
                failures.append(
                    {
                        "method": method,
                        "path": path.split("?")[0],
                        "expected": expected,
                        "actual": response.status_code,
                    }
                )
            assert response.status_code == expected, response.text
            return response

        async def journey(index, gate=gate, request=request):
            async with gate:
                headers = customer["headers"]
                cart = await request("POST", "/carts", 201, headers=headers)
                cid = cart.json()["id"]
                await request(
                    "POST",
                    f"/carts/{cid}/items",
                    201,
                    headers=headers,
                    json={
                        "branch_id": shop["branch"]["id"],
                        "variant_id": shop["variant"]["id"],
                        "window_id": shop["window"]["id"],
                        "quantity": str(1 + index % 5),
                    },
                )
                rows = await request("GET", f"/carts/{cid}/items", 200, headers=headers)
                assert len(rows.json()["items"]) == 1
                line = rows.json()["items"][0]
                assert float(line["quantity"]) == 1 + index % 5
                await request("DELETE", f"/carts/{cid}/items/{line['id']}", 204, headers=headers)
                empty = await request("GET", f"/carts/{cid}/items", 200, headers=headers)
                assert empty.json()["items"] == []
                await request(
                    "GET",
                    f"/merchant/branches/{shop['branch']['id']}/orders",
                    200,
                    headers=shop["merchant"]["headers"],
                )
                await request(
                    "GET",
                    f"/catalog/products?branch_id={shop['branch']['id']}",
                    200,
                    headers=headers,
                )

                await request("GET", f"/orders/{order['id']}/tracking", 200, headers=headers)
                await request(
                    "GET",
                    f"/operations/cities/{state['city']['id']}/dispatch",
                    200,
                    headers=state["admin"]["headers"],
                )

        started = perf_counter()
        try:
            outcomes = await asyncio.gather(
                *(journey(index) for index in range(journeys)), return_exceptions=True
            )
            assert not any(isinstance(result, BaseException) for result in outcomes), str(failures)
        finally:
            await workload.aclose()
        elapsed = perf_counter() - started
        ordered = sorted(timings)

        def percentile(fraction, ordered=ordered):
            return round(ordered[min(len(ordered) - 1, int((len(ordered) - 1) * fraction))], 2)

        evidence["profiles"].append(
            {
                "concurrency": concurrency,
                "journeys": journeys,
                "requests": len(timings),
                "failures": failures,
                "route_latency_ms": {
                    family: {
                        "samples": len(samples),
                        "p50": round(sorted(samples)[len(samples) // 2], 2),
                        "p95": round(sorted(samples)[int((len(samples) - 1) * 0.95)], 2),
                    }
                    for family, samples in route_timings.items()
                },
                "elapsed_seconds": round(elapsed, 3),
                "requests_per_second": round(len(timings) / elapsed, 2),
                "latency_ms": {
                    "p50": percentile(0.5),
                    "p95": percentile(0.95),
                    "p99": percentile(0.99),
                },
            }
        )
    target = Path(".local/qa/app-stress.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
