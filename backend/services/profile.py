"""
Profile Service — User profile management.
Stores and retrieves user profiles from local SQLite.
All data stays on-device.
"""

import json
from backend.db.sqlite import get_db_connection


def get_user_profile(user_id: str) -> dict | None:
    """Retrieve a user profile by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT profile_data FROM user_profiles WHERE user_id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return json.loads(row[0])
    return None


def update_user_profile(user_id: str, updates: dict) -> dict:
    """Create or update a user profile."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get existing profile or start fresh
    existing = get_user_profile(user_id) or {}
    existing.update(updates)
    profile_json = json.dumps(existing)

    cursor.execute(
        """
        INSERT INTO user_profiles (user_id, profile_data)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET profile_data = ?
        """,
        (user_id, profile_json, profile_json),
    )
    conn.commit()
    conn.close()

    return existing
