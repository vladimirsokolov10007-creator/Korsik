from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'employee',
    job_title TEXT NOT NULL DEFAULT 'Новый сотрудник',
    manager_name TEXT NOT NULL DEFAULT 'Руководитель не указан',
    location TEXT NOT NULL DEFAULT 'Не указана',
    start_date TEXT,
    experience_level TEXT NOT NULL DEFAULT 'new',
    preferred_hours TEXT NOT NULL DEFAULT '18:30–20:00',
    career_goal TEXT NOT NULL DEFAULT '',
    consent_to_pulse INTEGER NOT NULL DEFAULT 1,
    onboarding_stage TEXT NOT NULL DEFAULT 'registered',
    dialog_state TEXT NOT NULL DEFAULT 'ready',
    pending_hr_text TEXT NOT NULL DEFAULT '',
    last_chat_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    direction TEXT NOT NULL CHECK(direction IN ('in', 'out')),
    body TEXT NOT NULL,
    source_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    stage TEXT NOT NULL,
    text TEXT NOT NULL,
    sentiment TEXT NOT NULL,
    topics_json TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);
CREATE TABLE IF NOT EXISTS escalations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    source_message TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    reminder_type TEXT NOT NULL,
    due_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    sent_at TEXT,
    UNIQUE(user_id, reminder_type),
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);
CREATE TABLE IF NOT EXISTS delivery_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel TEXT NOT NULL,
    recipient_id TEXT NOT NULL,
    body TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connection() as connection:
            connection.executescript(SCHEMA)
            # Lightweight additive migration, so a deployed SQLite database keeps data.
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(users)").fetchall()}
            if "dialog_state" not in columns:
                connection.execute("ALTER TABLE users ADD COLUMN dialog_state TEXT NOT NULL DEFAULT 'ready'")
            if "pending_hr_text" not in columns:
                connection.execute("ALTER TABLE users ADD COLUMN pending_hr_text TEXT NOT NULL DEFAULT ''")
            if "last_chat_id" not in columns:
                connection.execute("ALTER TABLE users ADD COLUMN last_chat_id TEXT")

    def set_dialog_state(self, user_id: str, state: str) -> None:
        with self.connection() as connection:
            connection.execute("UPDATE users SET dialog_state = ?, updated_at = ? WHERE user_id = ?", (state, now(), user_id))

    def update_employee_fields(self, user_id: str, **fields: Any) -> None:
        allowed = {"display_name", "job_title", "location", "start_date", "experience_level", "manager_name", "preferred_hours", "career_goal", "consent_to_pulse", "onboarding_stage", "dialog_state", "pending_hr_text", "last_chat_id"}
        actual = {key: value for key, value in fields.items() if key in allowed}
        if not actual:
            return
        assignments = ", ".join(f"{key} = ?" for key in actual)
        values = [*actual.values(), now(), user_id]
        with self.connection() as connection:
            connection.execute(f"UPDATE users SET {assignments}, updated_at = ? WHERE user_id = ?", values)

    def delete_pending_reminders(self, user_id: str) -> None:
        with self.connection() as connection:
            connection.execute("DELETE FROM reminders WHERE user_id = ? AND status = 'pending'", (user_id,))

    def upsert_user(self, profile: dict[str, Any]) -> dict[str, Any]:
        timestamp = now()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO users (
                    user_id, display_name, role, job_title, manager_name, location, start_date,
                    experience_level, preferred_hours, career_goal, consent_to_pulse,
                    onboarding_stage, created_at, updated_at
                ) VALUES (?, ?, 'employee', ?, ?, ?, ?, ?, ?, ?, ?, 'registered', ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    display_name=excluded.display_name, job_title=excluded.job_title,
                    manager_name=excluded.manager_name, location=excluded.location,
                    start_date=excluded.start_date, experience_level=excluded.experience_level,
                    preferred_hours=excluded.preferred_hours, career_goal=excluded.career_goal,
                    consent_to_pulse=excluded.consent_to_pulse, updated_at=excluded.updated_at
                """,
                (
                    profile["user_id"], profile["display_name"], profile["job_title"],
                    profile["manager_name"], profile["location"],
                    profile.get("start_date"), profile["experience_level"],
                    profile["preferred_hours"], profile["career_goal"],
                    int(profile["consent_to_pulse"]), timestamp, timestamp,
                ),
            )
        return self.get_user(profile["user_id"]) or {}

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

    def ensure_employee(self, user_id: str, display_name: str = "Коллега") -> dict[str, Any]:
        current = self.get_user(user_id)
        if current:
            return current
        return self.upsert_user({
            "user_id": user_id, "display_name": display_name, "job_title": "Новый сотрудник",
            "manager_name": "Руководитель не указан", "location": "Не указана", "start_date": None,
            "experience_level": "new", "preferred_hours": "18:30–20:00", "career_goal": "",
            "consent_to_pulse": True,
        })

    def update_stage(self, user_id: str, stage: str) -> None:
        with self.connection() as connection:
            connection.execute("UPDATE users SET onboarding_stage = ?, updated_at = ? WHERE user_id = ?", (stage, now(), user_id))

    def save_message(self, user_id: str, direction: str, body: str, sources: list[dict[str, Any]] | None = None) -> None:
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO messages (user_id, direction, body, source_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, direction, body, json.dumps(sources or [], ensure_ascii=False), now()),
            )

    def save_feedback(self, user_id: str, stage: str, text: str, sentiment: str, topics: list[str], risk_level: str) -> None:
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO feedback (user_id, stage, text, sentiment, topics_json, risk_level, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, stage, text, sentiment, json.dumps(topics, ensure_ascii=False), risk_level, now()),
            )

    def create_escalation(self, user_id: str, reason: str, source_message: str = "") -> int:
        with self.connection() as connection:
            cursor = connection.execute(
                "INSERT INTO escalations (user_id, reason, source_message, created_at) VALUES (?, ?, ?, ?)",
                (user_id, reason, source_message, now()),
            )
            return int(cursor.lastrowid)

    def list_open_escalations(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """SELECT e.*, u.display_name, u.job_title, u.manager_name
                   FROM escalations e JOIN users u ON u.user_id=e.user_id
                   WHERE e.status='open' ORDER BY e.created_at DESC"""
            ).fetchall()
        return [dict(row) for row in rows]

    def resolve_escalation(self, escalation_id: int) -> bool:
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE escalations SET status='resolved', resolved_at=? WHERE id=? AND status='open'", (now(), escalation_id)
            )
            return cursor.rowcount == 1

    def add_reminder(self, user_id: str, reminder_type: str, due_at: str, payload: dict[str, Any]) -> None:
        with self.connection() as connection:
            connection.execute(
                """INSERT INTO reminders (user_id, reminder_type, due_at, payload_json, created_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(user_id, reminder_type) DO UPDATE SET due_at=excluded.due_at, payload_json=excluded.payload_json,
                   status='pending', sent_at=NULL""",
                (user_id, reminder_type, due_at, json.dumps(payload, ensure_ascii=False), now()),
            )

    def pending_reminders(self, current_time: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM reminders WHERE status='pending' AND due_at <= ? ORDER BY due_at", (current_time,)
            ).fetchall()
        return [dict(row) for row in rows]

    def mark_reminder_sent(self, reminder_id: int) -> None:
        with self.connection() as connection:
            connection.execute("UPDATE reminders SET status='sent', sent_at=? WHERE id=?", (now(), reminder_id))

    def log_delivery(self, channel: str, recipient_id: str, body: str, payload: dict[str, Any]) -> None:
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO delivery_log (channel, recipient_id, body, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (channel, recipient_id, body, json.dumps(payload, ensure_ascii=False), now()),
            )

    def dashboard_summary(self) -> dict[str, Any]:
        with self.connection() as connection:
            total = connection.execute("SELECT COUNT(*) FROM users WHERE role='employee'").fetchone()[0]
            open_escalations = connection.execute("SELECT COUNT(*) FROM escalations WHERE status='open'").fetchone()[0]
            feedback_total = connection.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
            risk_total = connection.execute("SELECT COUNT(*) FROM feedback WHERE risk_level IN ('medium','high')").fetchone()[0]
            stages = connection.execute("SELECT onboarding_stage, COUNT(*) as count FROM users WHERE role='employee' GROUP BY onboarding_stage").fetchall()
        return {
            "employees": total, "open_escalations": open_escalations,
            "feedback_total": feedback_total, "risk_feedback": risk_total,
            "stages": [dict(row) for row in stages],
        }

    def manager_team(self, manager_name: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT user_id, display_name, job_title, location, start_date, onboarding_stage, manager_name FROM users WHERE role='employee'"
        params: tuple[Any, ...] = ()
        if manager_name:
            query += " AND manager_name = ?"
            params = (manager_name,)
        query += " ORDER BY start_date IS NULL, start_date, display_name"
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def analytics(self, since: datetime | None = None) -> dict[str, Any]:
        query = "SELECT sentiment, topics_json, risk_level FROM feedback"
        params: tuple[str, ...] = ()
        if since:
            query += " WHERE created_at >= ?"
            params = (since.astimezone(timezone.utc).isoformat(),)
        query += " ORDER BY created_at DESC"
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        sentiment = {"positive": 0, "neutral": 0, "negative": 0}
        topics: dict[str, int] = {}
        high_risk = 0
        for row in rows:
            sentiment[row["sentiment"]] = sentiment.get(row["sentiment"], 0) + 1
            for topic in json.loads(row["topics_json"]):
                topics[topic] = topics.get(topic, 0) + 1
            if row["risk_level"] in {"medium", "high"}:
                high_risk += 1
        return {"sentiment": sentiment, "topics": topics, "risk_feedback": high_risk, "sample_size": len(rows)}
