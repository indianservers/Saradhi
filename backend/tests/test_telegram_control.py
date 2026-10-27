import uuid

from fastapi.testclient import TestClient

from backend.integrations.telegram import control


def test_control_protection_and_simulator_isolation(tmp_path, monkeypatch):
    monkeypatch.setattr(control, "LOCAL", tmp_path)
    with TestClient(control.app) as client:
        assert client.get("/").status_code == 200
        assert client.post("/api/start").status_code == 403
        headers = {"x-control-key": control.KEY}
        session = str(uuid.uuid4())
        for text in [
            "/start",
            "Food",
            "Biryani",
            "Select demo_deccan/chicken",
            "2",
            "Pickup",
            "Submit request",
        ]:
            result = client.post(
                "/api/simulate", headers=headers, json={"session": session, "text": text}
            )
            assert result.status_code == 200
        assert "saved" in result.json()["text"]
        assert client.get("/api/status").json()["requests"] == []
        assert not (tmp_path / "requests.sqlite3").exists()
        assert (
            client.post(
                "/api/simulate", headers=headers, json={"session": "../escape", "text": "/start"}
            ).status_code
            == 422
        )
        assert client.get("/", headers={"host": "untrusted.example"}).status_code == 400
