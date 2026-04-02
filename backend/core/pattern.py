"""
Pattern Recognition — Time series analysis on local SQLite logs.
Identifies behavioural patterns and environmental trends
to improve recommendation relevance over time.
"""

from datetime import datetime, timedelta
from backend.db.sqlite import get_db_connection


def get_activity_patterns(user_id: str, days: int = 30) -> dict:
    """
    Analyse recent conversation and interaction patterns.
    Returns a summary of when the user is most active,
    common topics, and recurring concerns.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    start_date = (datetime.now() - timedelta(days=days)).isoformat()

    cursor.execute(
        """
        SELECT timestamp, user_message, aura_reply
        FROM conversations
        WHERE user_id = ? AND timestamp >= ?
        ORDER BY timestamp DESC
        """,
        (user_id, start_date),
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {"total_interactions": 0, "patterns": []}

    # Analyse time-of-day patterns
    hour_counts = {}
    topics = []
    for row in rows:
        try:
            ts = datetime.fromisoformat(row[0])
            hour = ts.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        except (ValueError, TypeError):
            pass
        topics.append(row[1][:50])  # First 50 chars as topic hint

    peak_hour = max(hour_counts, key=hour_counts.get) if hour_counts else None

    return {
        "total_interactions": len(rows),
        "peak_activity_hour": peak_hour,
        "recent_topics": topics[:10],
        "days_analysed": days,
    }


def get_environmental_trends(days: int = 7) -> dict:
    """
    Analyse weather and environmental data trends.
    Returns patterns useful for proactive recommendations.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    start_date = (datetime.now() - timedelta(days=days)).isoformat()

    cursor.execute(
        """
        SELECT timestamp, data_type, value
        FROM environmental_logs
        WHERE timestamp >= ?
        ORDER BY timestamp DESC
        """,
        (start_date,),
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {"data_points": 0, "trends": []}

    return {
        "data_points": len(rows),
        "period_days": days,
        "raw_data": [
            {"timestamp": r[0], "type": r[1], "value": r[2]}
            for r in rows[:50]
        ],
    }
