"""User data model."""

from pydantic import BaseModel


class UserProfile(BaseModel):
    user_id: str = "default"
    household_members: list[str] = []
    mobility_notes: str = ""
    interests: list[str] = []
    space_type: str = ""
    location: str = ""
    preferences: dict = {}


class UserSummary(BaseModel):
    user_id: str
    total_conversations: int = 0
    profile_completeness: float = 0.0
