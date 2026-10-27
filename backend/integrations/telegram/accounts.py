"""Encrypted local account vault and short-lived, one-use Telegram pairing codes."""

import hashlib
import json
import os
import secrets
import sqlite3
import time

from cryptography.fernet import Fernet

from backend.integrations.telegram.catalog import ROOT


class Vault:
    def __init__(self, root=ROOT):
        folder = root / ".secrets"
        folder.mkdir(exist_ok=True)
        key = folder / "telegram-accounts.key"
        try:
            with key.open("xb") as stream:
                stream.write(Fernet.generate_key())
            if os.name == "nt":
                import getpass
                import subprocess

                subprocess.run(
                    ["icacls", str(key), "/inheritance:r", "/grant:r", getpass.getuser() + ":(F)"],
                    check=True,
                    capture_output=True,
                )
        except FileExistsError:
            pass
        self.cipher = Fernet(key.read_bytes())
        folder = root / ".local/telegram"
        folder.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(folder / "accounts.sqlite3")
        self.db.executescript(
            "CREATE TABLE IF NOT EXISTS accounts(chat INTEGER PRIMARY KEY,value BLOB); "
            "CREATE TABLE IF NOT EXISTS codes(hash TEXT PRIMARY KEY,value BLOB,expires REAL);"
        )

    def pair(self, tokens):
        code = secrets.token_hex(6)
        with self.db:
            self.db.execute("DELETE FROM codes WHERE expires<?", (time.time(),))
            self.db.execute(
                "INSERT INTO codes VALUES (?,?,?)",
                (
                    hashlib.sha256(code.encode()).hexdigest(),
                    self.cipher.encrypt(json.dumps(tokens).encode()),
                    time.time() + 300,
                ),
            )
        return code

    def redeem(self, chat, code):
        with self.db:
            row = self.db.execute(
                "DELETE FROM codes WHERE hash=? AND expires>? RETURNING value",
                (hashlib.sha256(code.encode()).hexdigest(), time.time()),
            ).fetchone()
            if not row:
                return False
            self.db.execute("INSERT OR REPLACE INTO accounts VALUES (?,?)", (chat, row[0]))
        return True

    def get(self, chat):
        row = self.db.execute("SELECT value FROM accounts WHERE chat=?", (chat,)).fetchone()
        return json.loads(self.cipher.decrypt(row[0])) if row else None

    def save(self, chat, tokens):
        with self.db:
            self.db.execute(
                "INSERT OR REPLACE INTO accounts VALUES (?,?)",
                (chat, self.cipher.encrypt(json.dumps(tokens).encode())),
            )

    def close(self):
        self.db.close()
