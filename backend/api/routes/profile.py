"""
Profile API — User profile management.
Builds and updates the personal profile used for
personalised recommendations.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.profile import get_user_profile, update_user_profile

router = APIRouter()


class ProfileUpdate(BaseModel):
    household_members: list[str] | None = None
    mobility_notes: str | None = None
    interests: list[str] | None = None
    space_type: str | None = None
    location: str | None = None


@router.get("/{user_id}")
async def get_profile(user_id: str):
    """Get the full user profile."""
    profile = get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/{user_id}")
async def update_profile(user_id: str, data: ProfileUpdate):
    """Update user profile fields."""
    updated = update_user_profile(user_id, data.model_dump(exclude_none=True))
    return updated


@router.post("/create")
async def create_profile(user_id: str = "default"):
    """Create a new blank profile for a user."""
    profile = update_user_profile(user_id, {})
    return profile
