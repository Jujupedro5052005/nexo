"""Separate local AI SQLite. Connections per operation; atomic quota reservations."""

import hashlib
import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from nexo.domain.models.intelligence import ChatMessage, Methodology, QuotaExceeded


class SqliteIntelligenceStorage:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY, conversation TEXT NOT NULL,
                    role TEXT NOT NULL, text TEXT NOT NULL, created TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS methodologies (
                    identity TEXT NOT NULL, version INTEGER NOT NULL, body TEXT NOT NULL,
                    PRIMARY KEY(identity, version));
                CREATE TABLE IF NOT EXISTS documents (
                    identity TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS usage (
                    id INTEGER PRIMARY KEY, day TEXT NOT NULL, feature TEXT NOT NULL,
                    reserved INTEGER NOT NULL, actual INTEGER, state TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS analysis_cache (
                    identity TEXT PRIMARY KEY, created REAL NOT NULL, body TEXT NOT NULL);
            """)
        cutoff = datetime.now(timezone.utc) - timedelta(days=29)
        for document in self.documents():
            if (
                document.get("kind") == "youtube"
                and datetime.fromisoformat(document["fetched_at"]) < cutoff
            ):
                self.delete_document(document["id"])

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def history(self, conversation_id: str, limit: int = 12) -> tuple[ChatMessage, ...]:
        with self.connection() as db:
            rows = db.execute(
                "SELECT role,text,created FROM messages WHERE conversation=? ORDER BY id DESC LIMIT ?",
                (conversation_id, min(limit, 100)),
            ).fetchall()
        return tuple(
            ChatMessage(role=r[0], text=r[1], created_at=r[2]) for r in reversed(rows)
        )

    def conversations(self) -> tuple[str, ...]:
        with self.connection() as db:
            return tuple(
                r[0]
                for r in db.execute(
                    "SELECT conversation FROM messages GROUP BY conversation ORDER BY MAX(id) DESC LIMIT 100"
                )
            )

    def save_turn(self, conversation_id: str, question: str, answer: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self.connection() as db:
            db.executemany(
                "INSERT INTO messages(conversation,role,text,created) VALUES(?,?,?,?)",
                [
                    (conversation_id, role, text, now)
                    for role, text in (("user", question), ("assistant", answer))
                ],
            )

    def clear_conversations(self) -> None:
        with self.connection() as db:
            db.execute("DELETE FROM messages")
            db.execute("DELETE FROM analysis_cache")

    def methodologies(self) -> tuple[Methodology, ...]:
        with self.connection() as db:
            rows = db.execute(
                "SELECT body FROM methodologies ORDER BY identity,version DESC"
            ).fetchall()
        return tuple(Methodology.model_validate_json(row[0]) for row in rows)

    def save_methodology(self, method: Methodology) -> None:
        with self.connection() as db:
            db.execute(
                "INSERT INTO methodologies VALUES(?,?,?) ON CONFLICT(identity,version) DO UPDATE SET body=excluded.body",
                (method.methodology_id, method.version, method.model_dump_json()),
            )

    def documents(self) -> list[dict[str, Any]]:
        with self.connection() as db:
            return [
                json.loads(r[0])
                for r in db.execute("SELECT body FROM documents ORDER BY identity")
            ]

    def put_document(self, document: dict[str, Any]) -> None:
        with self.connection() as db:
            db.execute(
                "INSERT INTO documents VALUES(?,?) ON CONFLICT(identity) DO UPDATE SET body=excluded.body",
                (document["id"], json.dumps(document, ensure_ascii=False)),
            )

    def delete_document(self, identity: str) -> None:
        with self.connection() as db:
            db.execute("DELETE FROM documents WHERE identity=?", (identity,))

    def reserve(
        self, feature: str, tokens: int, request_limit: int, token_limit: int
    ) -> int:
        day = datetime.now(timezone.utc).date().isoformat()
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            requests, consumed = db.execute(
                "SELECT COUNT(*),COALESCE(SUM(COALESCE(actual,reserved)),0) FROM usage WHERE day=?",
                (day,),
            ).fetchone()
            if requests >= request_limit or consumed + tokens > token_limit:
                raise QuotaExceeded(
                    "Limite diário local da IA atingido. Aguarde o próximo dia UTC ou revise a configuração."
                )
            cursor = db.execute(
                "INSERT INTO usage(day,feature,reserved,state) VALUES(?,?,?,'reserved')",
                (day, feature, tokens),
            )
            assert cursor.lastrowid is not None
            return cursor.lastrowid

    def finish_usage(self, identity: int, tokens: int | None, state: str) -> None:
        with self.connection() as db:
            db.execute(
                "UPDATE usage SET actual=?,state=? WHERE id=?",
                (tokens, state, identity),
            )

    def usage(self) -> dict[str, Any]:
        day = datetime.now(timezone.utc).date().isoformat()
        with self.connection() as db:
            rows = db.execute(
                "SELECT feature,COUNT(*),SUM(COALESCE(actual,reserved)) FROM usage WHERE day=? GROUP BY feature",
                (day,),
            ).fetchall()
        return {
            "day_utc": day,
            "requests": sum(r[1] for r in rows),
            "tokens_accounted": sum(r[2] for r in rows),
            "features": rows,
        }

    def cached(self, context: str, max_age: int = 120) -> str | None:
        key = hashlib.sha256(context.encode()).hexdigest()
        with self.connection() as db:
            row = db.execute(
                "SELECT created,body FROM analysis_cache WHERE identity=?", (key,)
            ).fetchone()
        if row and datetime.now(timezone.utc).timestamp() - row[0] < max_age:
            return str(row[1])
        return None

    def cache(self, context: str, body: str) -> None:
        key = hashlib.sha256(context.encode()).hexdigest()
        now = datetime.now(timezone.utc).timestamp()
        with self.connection() as db:
            db.execute("DELETE FROM analysis_cache WHERE created < ?", (now - 120,))
            db.execute(
                "INSERT OR REPLACE INTO analysis_cache VALUES(?,?,?)", (key, now, body)
            )
