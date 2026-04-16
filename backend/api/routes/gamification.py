"""
Gamification API — suggestion completion, points, and badges.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class CompletionRequest(BaseModel):
    user_id: str = "default"
    suggestion_text: str


@router.post("/complete")
def mark_suggestion_complete(req: CompletionRequest):
    """
    Mark a suggestion as completed for a user.
    Awards points, checks for badge unlocks, saves to SQLite.
    Returns: {points_awarded, total_points, badges_unlocked}
    """
    from backend.core.gamification import complete_suggestion
    return complete_suggestion(req.user_id, req.suggestion_text)
