"""Expiring scoped checkout capabilities; never expose backend customer session tokens."""

import hashlib
import json
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager

from backend.integrations.telegram.catalog import ROOT


@contextmanager
def database():
    path = ROOT / ".local/telegram/checkout.sqlite3"
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.execute(
        "CREATE TABLE IF NOT EXISTS checkouts(hash TEXT PRIMARY KEY,chat INTEGER,"
        "order_id TEXT,intent TEXT,expires REAL)"
    )
    try:
        with db:
            yield db
    finally:
        db.close()


def create(chat, order_id, intent, mode):
    token = secrets.token_urlsafe(32)
    with database() as db:
        db.execute(
            "INSERT INTO checkouts VALUES (?,?,?,?,?)",
            (
                hashlib.sha256(token.encode()).hexdigest(),
                chat,
                order_id,
                json.dumps({**intent, "mode": mode}),
                time.time() + 900,
            ),
        )
    base = os.environ.get("TELEGRAM_CHECKOUT_BASE_URL", "http://127.0.0.1:8765").rstrip("/")
    return base + "/checkout/" + token


def lookup(token):
    with database() as db:
        row = db.execute(
            "SELECT chat,order_id,intent FROM checkouts WHERE hash=? AND expires>?",
            (hashlib.sha256(token.encode()).hexdigest(), time.time()),
        ).fetchone()
    return {"chat": row[0], "order_id": row[1], "intent": json.loads(row[2])} if row else None
