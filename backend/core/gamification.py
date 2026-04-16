"""
Gamification Engine — Points, badges, and suggestion completion tracking.
Encourages users to act on Aura's recommendations.
"""

import json
from datetime import datetime

# Points awarded per completed suggestion
POINTS_PER_SUGGESTION = 5

# Badge definitions: (points_threshold, badge_id, badge_name, description)
# Thresholds are multiples of POINTS_PER_SUGGESTION (5 pts each).
BADGES = [
    (5,   "getting_started",  "Getting Started",   "Completed your first suggestion!"),
    (25,  "space_improver",   "Space Improver",    "You've made 5 improvements."),
    (50,  "wellness_seeker",  "Wellness Seeker",   "Reaching 50 points — you're on a roll!"),
    (125, "aura_champion",    "Aura Champion",     "125 points — your space is thriving!"),
    (250, "master_of_space",  "Master of Space",   "250 points — the ultimate Aura achiever!"),
]


# ─────────────────────────────────────────────────────────
# SQLite helpers (lazy import to avoid circular deps)
# ─────────────────────────────────────────────────────────

def _get_conn():
    from backend.db.sqlite import get_db_connection
    return get_db_connection()


def _ensure_tables():
    """Create gamification tables if they don't exist yet (idempotent)."""
    conn = _get_conn()
    conn.executescript("""
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
    conn.close()


# ─────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────

def complete_suggestion(user_id: str, suggestion_text: str) -> dict:
    """
    Mark a suggestion as completed for a user.
    Awards POINTS_PER_SUGGESTION points and checks for newly unlocked badges.
    Returns: {points_awarded, total_points, badges_unlocked}
    """
    _ensure_tables()
    conn = _get_conn()

    # 1. Log the completion
    conn.execute(
        "INSERT INTO suggestion_completions (user_id, suggestion_text, points_awarded) VALUES (?, ?, ?)",
        (user_id, suggestion_text, POINTS_PER_SUGGESTION),
    )

    # 2. Upsert gamification row and capture old + new points
    row = conn.execute(
        "SELECT total_points, badges FROM user_gamification WHERE user_id = ?",
        (user_id,),
    ).fetchone()

    old_points = row[0] if row else 0
    old_badges = json.loads(row[1]) if row else []
    new_points = old_points + POINTS_PER_SUGGESTION

    if row:
        conn.execute(
            "UPDATE user_gamification SET total_points = ?, updated_at = ? WHERE user_id = ?",
            (new_points, datetime.now().isoformat(), user_id),
        )
    else:
        conn.execute(
            "INSERT INTO user_gamification (user_id, total_points, badges, updated_at) VALUES (?, ?, '[]', ?)",
            (user_id, new_points, datetime.now().isoformat()),
        )

    conn.commit()

    # 3. Determine newly unlocked badges
    newly_unlocked = _check_new_badges(old_points, new_points, old_badges)
    if newly_unlocked:
        updated_badges = old_badges + [b["id"] for b in newly_unlocked]
        conn.execute(
            "UPDATE user_gamification SET badges = ? WHERE user_id = ?",
            (json.dumps(updated_badges), user_id),
        )
        conn.commit()

    conn.close()

    return {
        "points_awarded": POINTS_PER_SUGGESTION,
        "total_points": new_points,
        "badges_unlocked": newly_unlocked,
    }


def get_user_points(user_id: str) -> int:
    """Return the total points for a user (0 if none recorded yet)."""
    _ensure_tables()
    conn = _get_conn()
    row = conn.execute(
        "SELECT total_points FROM user_gamification WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    return row[0] if row else 0


def get_user_badges(user_id: str) -> list[str]:
    """Return the list of badge IDs earned by the user."""
    _ensure_tables()
    conn = _get_conn()
    row = conn.execute(
        "SELECT badges FROM user_gamification WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    return json.loads(row[0]) if row else []


def get_all_badge_definitions() -> list[dict]:
    """Return all badge definitions as a list of dicts."""
    return [
        {
            "id": badge_id,
            "name": name,
            "description": description,
            "threshold": threshold,
        }
        for threshold, badge_id, name, description in BADGES
    ]


# ─────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────

def _check_new_badges(old_points: int, new_points: int, earned_ids: list[str]) -> list[dict]:
    """Return badge dicts for any badges crossed by going old→new points."""
    unlocked = []
    for threshold, badge_id, name, description in BADGES:
        if badge_id not in earned_ids and old_points < threshold <= new_points:
            unlocked.append({"id": badge_id, "name": name, "description": description})
    return unlocked
