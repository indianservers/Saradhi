"""Explicitly invoked against locally running services; not an isolated unit test."""

import json

import httpx


def main():
    results = {}
    with httpx.Client(timeout=8, trust_env=False) as client:
        live = client.get("http://127.0.0.1:8000/health/live")
        assert live.status_code == 200
        assert live.json()["status"] == "ok"
        ready = client.get("http://127.0.0.1:8000/health/ready")
        assert ready.status_code in (200, 503)
        results["api"] = {
            "live": live.status_code,
            "ready": ready.status_code,
            "readiness": ready.json(),
        }
        me = client.get("http://127.0.0.1:8000/api/v1/me")
        assert me.status_code == 401
        assert me.json()["error"]["request_id"] == me.headers["X-Request-ID"]
        results["api"]["anonymous_identity"] = me.status_code
        for name, port in [
            ("company_admin", 3000),
            ("city_operations", 3001),
            ("support_console", 3002),
        ]:
            base = f"http://127.0.0.1:{port}"
            shell = client.get(base)
            assert shell.status_code == 200 and "quickbuddy" in shell.text
            login = client.get(base + "/login")
            assert login.status_code == 200
            denied = client.get(base + "/workspace")
            assert denied.status_code == 307 and denied.headers["location"] == "/login"
            invalid = client.get(base + "/workspace", headers={"Cookie": "qb_access=invalid"})
            assert invalid.status_code == 307
            assert invalid.headers["location"] == "/login?reason=access"
            results[name] = {
                "shell": shell.status_code,
                "login": login.status_code,
                "anonymous_workspace": denied.status_code,
                "invalid_token_workspace": invalid.status_code,
            }
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
