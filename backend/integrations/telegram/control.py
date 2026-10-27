"""Loopback-only Telegram control room: python -m backend.integrations.telegram.control."""

import json
import os
import secrets
import sqlite3
import subprocess
import sys
import threading
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field, SecretStr
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.integrations.telegram.bot import ROOT, Store
from backend.integrations.telegram.catalog import Catalog, load_catalog, save_catalog
from backend.integrations.telegram.payments import credentials
from backend.integrations.telegram.runtime import process

LOCAL = ROOT / ".local" / "telegram"
LOCAL.mkdir(parents=True, exist_ok=True)
KEY = secrets.token_urlsafe(32)
LOCK = threading.Lock()
worker = None
output = None
ai_worker = None
ai_output = None
api_worker = None
api_output = None


def stop():
    global worker, output
    if worker and worker.poll() is None:
        worker.terminate()
        try:
            worker.wait(timeout=5)
        except subprocess.TimeoutExpired:
            worker.kill()
            worker.wait(timeout=5)
    worker = None
    if output:
        output.close()
        output = None


@asynccontextmanager
async def lifespan(app):
    yield
    stop()
    if ai_worker and ai_worker.poll() is None:
        ai_worker.terminate()
        ai_worker.wait(timeout=10)
    if ai_output:
        ai_output.close()
    if api_worker and api_worker.poll() is None:
        api_worker.terminate()
        api_worker.wait(timeout=10)
    if api_output:
        api_output.close()


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])


@app.middleware("http")
async def local_only(request: Request, call_next):
    if (
        request.method != "GET"
        and not request.url.path.startswith("/checkout/")
        and not secrets.compare_digest(request.headers.get("x-control-key", ""), KEY)
    ):
        from starlette.responses import JSONResponse

        return JSONResponse({"detail": "Reload the control page first."}, status_code=403)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.get("/", response_class=HTMLResponse)
def index():
    return (
        Path(__file__)
        .with_name("control.html")
        .read_text(encoding="utf-8")
        .replace("__CONTROL_KEY__", KEY)
    )


@app.post("/api/start")
def start_worker():
    global worker, output
    with LOCK:
        if worker is None or worker.poll() is not None:
            if output:
                output.close()
            output = (LOCAL / "control-worker.log").open("a", encoding="utf-8")
            worker = subprocess.Popen(
                [sys.executable, "-m", "backend.integrations.telegram.bot"],
                cwd=ROOT,
                stdout=output,
                stderr=output,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
    return {"running": worker.poll() is None}


@app.post("/api/stop")
def stop_worker():
    with LOCK:
        stop()
    return {"running": False}


def records(table, limit=80):
    path = LOCAL / "requests.sqlite3"
    if not path.exists():
        return []
    with sqlite3.connect(path) as db:
        db.row_factory = sqlite3.Row
        exists = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        if not exists:
            return []
        # Table names are fixed by the caller, never accepted from a request.
        return [
            dict(row)
            for row in db.execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT ?", (limit,))
        ]


@app.get("/api/status")
async def status():
    log = LOCAL / "control-worker.log"
    text = log.read_text(encoding="utf-8", errors="replace")[-6000:] if log.exists() else ""
    ai = {"ready": False, "error": "Not started"}
    try:
        async with httpx.AsyncClient(timeout=1) as client:
            response = await client.get("http://127.0.0.1:8766/health")
            ai = response.json()
    except (httpx.HTTPError, ValueError):
        pass
    return {
        "running": worker is not None and worker.poll() is None,
        "pid": worker.pid if worker and worker.poll() is None else None,
        "log": text,
        "events": records("events"),
        "requests": [{**row, "data": json.loads(row["data"])} for row in records("requests")],
        "ai": ai,
        "payment_test_configured": credentials() is not None,
        "catalog_demo": load_catalog().demo,
    }


class Simulation(BaseModel):
    session: str = Field(pattern=r"^[a-f0-9-]{36}$")
    text: str = Field(default="", max_length=500)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


@app.post("/api/simulate")
async def simulate(body: Simulation):
    folder = LOCAL / "simulator"
    folder.mkdir(exist_ok=True)
    store = Store(folder / f"{body.session}.sqlite3")
    try:
        number = store.db.execute("SELECT coalesce(max(id),0)+1 FROM updates").fetchone()[0]
        update = {
            "update_id": number,
            "message": {
                "chat": {"id": 1, "type": "private"},
                "text": body.text,
            },
        }
        if body.latitude is not None and body.longitude is not None:
            update["message"]["location"] = {
                "latitude": body.latitude,
                "longitude": body.longitude,
            }
        result = await process(update, store, sandbox=True)
        if result.pop("payment_action", None):
            result["text"] = (
                "Simulator: payment actions never contact Razorpay. Use Telegram for TEST checkout."
            )
        return result
    finally:
        store.db.close()


@app.get("/api/catalog")
def get_catalog():
    return load_catalog().model_dump(mode="json")


@app.post("/api/catalog")
def update_catalog(body: Catalog):
    from fastapi import HTTPException

    try:
        save_catalog(body.model_dump(mode="json"))
    except ValueError as error:
        raise HTTPException(422, str(error)) from None
    return {"saved": True}


@app.get("/api/card/{restaurant_id}/{dish_id}")
def card_image(restaurant_id: str, dish_id: str):
    from fastapi import HTTPException

    from backend.integrations.telegram.catalog import card
    from backend.integrations.telegram.media import render_card

    catalog = load_catalog()
    for restaurant in catalog.restaurants:
        if restaurant.id != restaurant_id:
            continue
        if dish_id == "restaurant":
            return Response(
                render_card(card(restaurant, demo=catalog.demo)), media_type="image/png"
            )
        for dish in restaurant.menu:
            if dish.id == dish_id:
                return Response(
                    render_card(card(restaurant, dish, catalog.demo)), media_type="image/png"
                )
    raise HTTPException(404, "Menu card not found")


@app.post("/api/ai/start")
def start_ai():
    global ai_worker, ai_output
    from fastapi import HTTPException

    executable = ROOT / ".local/telegram-ai-venv/Scripts/python.exe"
    if not executable.exists():
        raise HTTPException(503, "Install the isolated TensorFlow environment first.")
    with LOCK:
        if ai_worker is None or ai_worker.poll() is not None:
            if ai_output:
                ai_output.close()
            ai_output = (LOCAL / "language-model.log").open("a", encoding="utf-8")
            ai_worker = subprocess.Popen(
                [str(executable), "-m", "backend.integrations.telegram.language_server"],
                cwd=ROOT,
                stdout=ai_output,
                stderr=ai_output,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
    return {"starting": True}


@app.post("/api/brain/reload")
async def reload_dialogue_brain():
    from fastapi import HTTPException

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "http://127.0.0.1:8766/brain/reload",
                json={},
                headers={"X-Quickbuddy-Local-Request": "1"},
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError:
        raise HTTPException(
            503, "Dialogue brain unavailable; check training and evaluation first."
        ) from None


class PaymentKeys(BaseModel):
    key_id: str = Field(pattern=r"^rzp_test_[A-Za-z0-9]+$")
    key_secret: SecretStr


@app.post("/api/payment-keys")
def save_payment_keys(body: PaymentKeys):
    from fastapi import HTTPException

    secret = body.key_secret.get_secret_value()
    if not secret or not secret.isalnum():
        raise HTTPException(422, "Use a valid Razorpay TEST key secret.")
    path = ROOT / ".secrets/razorpay-test.env"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"RAZORPAY_KEY_ID={body.key_id}\nRAZORPAY_KEY_SECRET={secret}\n", encoding="utf-8"
    )
    if sys.platform == "win32":
        import getpass

        subprocess.run(
            ["icacls", str(path), "/inheritance:r", "/grant:r", getpass.getuser() + ":(F)"],
            capture_output=True,
            check=True,
        )
    if api_worker and api_worker.poll() is None:
        api_worker.terminate()
        api_worker.wait(timeout=10)
        start_backend()
    return {"saved": True, "mode": "test"}


class CustomerLogin(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: SecretStr
    create_account: bool = Field(default=False, alias="register")


@app.post("/api/link-account")
async def link_account(body: CustomerLogin):
    from fastapi import HTTPException

    from backend.integrations.telegram.accounts import Vault
    from backend.integrations.telegram.backend_client import API

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            if body.create_account:
                registration = await client.post(
                    API + "/auth/register",
                    json={"email": body.email, "password": body.password.get_secret_value()},
                )
                if not registration.is_success:
                    raise HTTPException(
                        422,
                        "Registration failed. Use a unique email "
                        "and a password of at least 12 characters.",
                    )
            response = await client.post(
                API + "/auth/login",
                json={"email": body.email, "password": body.password.get_secret_value()},
            )
        if not response.is_success:
            raise HTTPException(
                401, "Customer sign-in failed. Check credentials and API availability."
            )
        vault = Vault()
        try:
            code = vault.pair(response.json())
        finally:
            vault.close()
        return {"command": "Link " + code, "expires_seconds": 300}
    except httpx.HTTPError:
        raise HTTPException(
            503, "Backend is unavailable. Start the Quickbuddy API first."
        ) from None


@app.post("/api/backend/start")
def start_backend():
    global api_worker, api_output
    with LOCK:
        if api_worker is None or api_worker.poll() is not None:
            if api_output:
                api_output.close()
            api_output = (LOCAL / "backend.log").open("a", encoding="utf-8")
            from dotenv import dotenv_values

            environment = os.environ.copy()
            test_keys = dotenv_values(ROOT / ".secrets/razorpay-test.env")
            if test_keys.get("RAZORPAY_KEY_ID", "").startswith("rzp_test_") and test_keys.get(
                "RAZORPAY_KEY_SECRET"
            ):
                environment.update(
                    {
                        "RAZORPAY_ENABLED": "true",
                        "RAZORPAY_MODE": "test",
                        "RAZORPAY_KEY_ID": test_keys["RAZORPAY_KEY_ID"],
                        "RAZORPAY_KEY_SECRET": test_keys["RAZORPAY_KEY_SECRET"],
                    }
                )
            api_worker = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "backend.api.app.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8001",
                    "--no-access-log",
                ],
                cwd=ROOT,
                stdout=api_output,
                stderr=api_output,
                env=environment,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
    return {"starting": True, "api_url": "http://127.0.0.1:8001/api/v1"}


@app.get("/checkout/{token}", response_class=HTMLResponse)
def checkout_page(token: str):
    from fastapi import HTTPException

    from backend.integrations.telegram.checkout_sessions import lookup

    session = lookup(token)
    if not session:
        raise HTTPException(404, "Checkout expired. Return to Telegram for a new checkout link.")
    intent = session["intent"]
    options = {
        "key": intent["key_id"],
        "order_id": intent["provider_order_id"],
        "amount": intent["amount_minor"],
        "currency": intent["currency"],
        "name": "Quickbuddy",
    }
    # Escape script markup; customer session tokens stay server-side.
    options_json = json.dumps(options).replace("<", "\\u003c")
    mode = "TEST" if intent["mode"] == "test" else "LIVE"
    template = Path(__file__).with_name("checkout.html").read_text(encoding="utf-8")
    return template.replace("__MODE__", mode).replace("__OPTIONS__", options_json)


class CheckoutVerification(BaseModel):
    razorpay_order_id: str = Field(pattern=r"^order_[A-Za-z0-9]+$")
    razorpay_payment_id: str = Field(pattern=r"^pay_[A-Za-z0-9]+$")
    razorpay_signature: str = Field(pattern=r"^[A-Fa-f0-9]{64}$")


@app.post("/checkout/{token}/verify")
async def checkout_verify(token: str, body: CheckoutVerification):
    from fastapi import HTTPException

    from backend.integrations.telegram.accounts import Vault
    from backend.integrations.telegram.backend_client import Backend, BackendError
    from backend.integrations.telegram.checkout_sessions import lookup

    session = lookup(token)
    if not session or session["intent"]["provider_order_id"] != body.razorpay_order_id:
        raise HTTPException(404, "Checkout session invalid or expired.")
    vault = Vault()
    backend = Backend(session["chat"], vault)
    try:
        await backend.call(
            "POST",
            "/payments/razorpay/verify",
            {
                "order_id": body.razorpay_order_id,
                "payment_id": body.razorpay_payment_id,
                "signature": body.razorpay_signature,
            },
        )
        payment = await backend.call("GET", f"/orders/{session['order_id']}/payment")
        return {
            "message": "Payment verified."
            if payment["status"] == "confirmed"
            else "Provider verification received; awaiting confirmed payment status."
        }
    except (BackendError, httpx.HTTPError):
        raise HTTPException(409, "Payment unverified. Check Telegram order status.") from None
    finally:
        await backend.client.aclose()
        vault.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8765, access_log=False)
