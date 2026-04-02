"""
SQLite Database — Local persistent storage.
Handles conversation logs, user profiles, and environmental data.
All data stays on the local machine.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from backend.config import SQLITE_DB_PATH


def get_db_connection() -> sqlite3.Connection:
    """Get a connection to the local SQLite database."""
    Path(SQLITE_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_db():
    """Initialise database tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id     TEXT PRIMARY KEY,
            profile_data TEXT NOT NULL DEFAULT '{}',
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       TEXT NOT NULL,
            user_message  TEXT NOT NULL,
            aura_reply    TEXT NOT NULL,
            timestamp     TEXT NOT NULL DEFAULT (datetime('now')),
            context_sources TEXT DEFAULT '[]'
        );

        CREATE TABLE IF NOT EXISTS environmental_logs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp  TEXT NOT NULL DEFAULT (datetime('now')),
            data_type  TEXT NOT NULL,
            value      TEXT NOT NULL,
            metadata   TEXT DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS space_analyses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT NOT NULL,
            timestamp   TEXT NOT NULL DEFAULT (datetime('now')),
            description TEXT,
            objects     TEXT DEFAULT '[]',
            suggestions TEXT DEFAULT '[]'
        );

        CREATE INDEX IF NOT EXISTS idx_conversations_user
            ON conversations(user_id, timestamp);
        CREATE INDEX IF NOT EXISTS idx_env_logs_timestamp
            ON environmental_logs(timestamp);
    """)

    conn.commit()
    conn.close()
    print("✦  Database initialised.")


def log_conversation(user_id: str, user_message: str, aura_reply: str):
    """Log a conversation exchange."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO conversations (user_id, user_message, aura_reply, timestamp)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, user_message, aura_reply, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_conversation_history(user_id: str, limit: int = 20) -> list[dict]:
    """Retrieve recent conversations for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, user_message, aura_reply, timestamp
        FROM conversations
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "user_message": r[1],
            "aura_reply": r[2],
            "timestamp": r[3],
        }
        for r in rows
    ]


def log_environmental_data(data_type: str, value: str, metadata: str = "{}"):
    """Log an environmental data point (weather, light, etc.)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO environmental_logs (data_type, value, metadata)
        VALUES (?, ?, ?)
        """,
        (data_type, value, metadata),
    )
    conn.commit()
    conn.close()
