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
            suggestions TEXT DEFAULT '[]',
            scores      TEXT DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS mood_logs (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      TEXT NOT NULL,
            mood         TEXT NOT NULL,
            weather_data TEXT DEFAULT '{}',
            sun_data     TEXT DEFAULT '{}',
            timestamp    TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS zone_analyses (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       TEXT NOT NULL,
            timestamp     TEXT NOT NULL DEFAULT (datetime('now')),
            zones         TEXT DEFAULT '[]',
            overall_score INTEGER DEFAULT 0,
            summary       TEXT DEFAULT ''
        );

        CREATE INDEX IF NOT EXISTS idx_conversations_user
            ON conversations(user_id, timestamp);
        CREATE INDEX IF NOT EXISTS idx_env_logs_timestamp
            ON environmental_logs(timestamp);
        CREATE INDEX IF NOT EXISTS idx_zone_analyses_user
            ON zone_analyses(user_id, timestamp);
            
        CREATE TABLE IF NOT EXISTS session_evaluations (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       TEXT NOT NULL,
            relevance_score REAL,
            safety_score REAL,
            feasibility_score REAL,
            irish_context_score REAL,
            accessibility_score REAL,
            overall_score REAL,
            timestamp     TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS suggestion_completions (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id          TEXT NOT NULL,
            suggestion_text  TEXT NOT NULL,
            points_awarded   INTEGER DEFAULT 10,
            timestamp        TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS user_gamification (
            user_id      TEXT PRIMARY KEY,
            total_points INTEGER DEFAULT 0,
            badges       TEXT DEFAULT '[]',
            updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_completions_user
            ON suggestion_completions(user_id, timestamp);
    """)

    conn.commit()
    
    # Simple migration for existing DBs
    try:
        cursor.execute("ALTER TABLE space_analyses ADD COLUMN scores TEXT DEFAULT '{}'")
        conn.commit()
    except sqlite3.OperationalError:
        # Column likely already exists
        pass
        
    conn.close()
    print("[Aura] Database initialised (v2).")


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

def log_mood(user_id: str, mood: str, weather_data: str = "{}", sun_data: str = "{}"):
    """Log a user's mood alongside environmental context."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO mood_logs (user_id, mood, weather_data, sun_data)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, mood, weather_data, sun_data)
    )
    conn.commit()
    conn.close()

def get_recent_moods(user_id: str, limit: int = 7) -> list[dict]:
    """Retrieve recent mood entries for pattern detection."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT mood, weather_data, sun_data, timestamp
        FROM mood_logs
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (user_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "mood": r[0],
            "weather_data": r[1],
            "sun_data": r[2],
            "timestamp": r[3]
        }
        for r in rows
    ]

import json


def log_zone_analysis(user_id: str, zones: list, overall_score: int, summary: str) -> int:
    """Persist a zone analysis result and return the new row id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO zone_analyses (user_id, zones, overall_score, summary)
           VALUES (?, ?, ?, ?)""",
        (user_id, json.dumps(zones), overall_score, summary),
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def get_zone_analyses(user_id: str, limit: int = 10) -> list[dict]:
    """Retrieve recent zone analyses for a user, newest first."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, zones, overall_score, summary, timestamp
           FROM zone_analyses WHERE user_id = ?
           ORDER BY timestamp DESC LIMIT ?""",
        (user_id, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "zones": json.loads(r[1]),
            "overall_score": r[2],
            "summary": r[3],
            "timestamp": r[4],
        }
        for r in rows
    ]


def log_space_analysis(user_id: str, description: str, objects: list, suggestions: list, score: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO space_analyses (user_id, description, objects, suggestions, scores)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, description, json.dumps(objects), json.dumps(suggestions), json.dumps(score))
    )
    conn.commit()
    conn.close()
