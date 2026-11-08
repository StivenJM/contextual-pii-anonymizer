"""Local archive with transactional completion and capability-scoped withdrawal.

The file contains raw research data. Encryption/access control at the filesystem
and backup layers are deployment requirements, not guarantees made by SQLite.
"""

import hashlib
import json
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from app.research.errors import ResearchError
from app.research.schemas import CompleteSession, StartSession


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class CaptureStore:
    def __init__(self, path: Path, retention_days: int):
        self.path = path
        self.retention_days = retention_days
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS research_sessions (
                    session_id TEXT PRIMARY KEY, token_hash TEXT NOT NULL,
                    metadata TEXT NOT NULL, expires_at REAL NOT NULL,
                    receipt_id TEXT UNIQUE, payload_hash TEXT, payload TEXT
                )
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA secure_delete = ON")
            with db:
                yield db
        finally:
            db.close()

    def check(self) -> None:
        with self.connect() as db:
            db.execute("SELECT 1").fetchone()

    def start(self, body: StartSession) -> dict:
        session_id = str(body.session_id)
        token_hash = digest(body.upload_token)
        metadata = json.dumps(
            body.model_dump(mode="json", exclude={"upload_token"}), sort_keys=True
        )
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            current = db.execute(
                "SELECT * FROM research_sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            if current:
                if (
                    current["expires_at"] <= time.time()
                    or current["metadata"] != metadata
                    or not secrets.compare_digest(current["token_hash"], token_hash)
                ):
                    raise ResearchError(409, "Session ID already used")
            else:
                db.execute(
                    "INSERT INTO research_sessions"
                    "(session_id, token_hash, metadata, expires_at) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        session_id,
                        token_hash,
                        metadata,
                        time.time() + self.retention_days * 86400,
                    ),
                )
        return {"session_id": session_id, "protocol_version": body.protocol_version}

    def authorized(self, db, session_id: str, token: str):
        row = db.execute(
            "SELECT * FROM research_sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        if (
            row is None
            or row["expires_at"] <= time.time()
            or not secrets.compare_digest(row["token_hash"], digest(token))
        ):
            raise ResearchError(404, "Session unavailable")
        return row

    def complete(self, session_id: str, token: str, body: CompleteSession) -> dict:
        payload = json.dumps(
            body.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        payload_hash = digest(payload)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = self.authorized(db, session_id, token)
            if row["receipt_id"]:
                if row["payload_hash"] != payload_hash:
                    raise ResearchError(
                        409, "Session already saved with different content"
                    )
                receipt = row["receipt_id"]
            else:
                receipt = secrets.token_urlsafe(24)
                db.execute(
                    "UPDATE research_sessions SET receipt_id = ?, payload_hash = ?, "
                    "payload = ? WHERE session_id = ?",
                    (receipt, payload_hash, payload, session_id),
                )
        # Reached only after the transaction committed successfully.
        return {"receipt_id": receipt, "event_count": len(body.events)}

    def export(self, receipt: str) -> dict:
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM research_sessions "
                "WHERE receipt_id = ? AND expires_at > ?",
                (receipt, time.time()),
            ).fetchone()
        if row is None:
            raise ResearchError(404, "Record unavailable")
        return (
            json.loads(row["metadata"])
            | json.loads(row["payload"])
            | {"receipt_id": receipt, "expires_at": row["expires_at"]}
        )

    def withdraw(self, session_id: str, token: str) -> None:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            self.authorized(db, session_id, token)
            db.execute(
                "DELETE FROM research_sessions WHERE session_id = ?", (session_id,)
            )

    def purge_expired(self) -> int:
        with self.connect() as db:
            result = db.execute(
                "DELETE FROM research_sessions WHERE expires_at <= ?", (time.time(),)
            )
            return result.rowcount

    def withdraw_record(self, receipt: str) -> None:
        with self.connect() as db:
            result = db.execute(
                "DELETE FROM research_sessions WHERE receipt_id = ?", (receipt,)
            )
            if not result.rowcount:
                raise ResearchError(404, "Record unavailable")
