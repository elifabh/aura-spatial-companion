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
    household_members: list[dict] | None = None
    mobility_notes: str | None = None
    interests: list[str] | None = None
    space_type: str | None = None
    location: str | None = None
    accessibility_needs: list[str] | None = None


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


class MoodLog(BaseModel):
    mood: str
    weather_data: str = "{}"
    sun_data: str = "{}"
    
@router.post("/{user_id}/mood")
async def register_mood(user_id: str, data: MoodLog):
    from backend.db.sqlite import log_mood, get_recent_moods
    import httpx
    from backend.config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_OPTIONS, OLLAMA_KEEP_ALIVE, OLLAMA_NUM_CTX
    
    log_mood(user_id, data.mood, data.weather_data, data.sun_data)
    
    recent = get_recent_moods(user_id, limit=7)
    insight = None
    
    if len(recent) >= 7:
        # Detect patterns
        history_text = "\n".join([
            f"- Mood: {m['mood']} | Weather: {m['weather_data']} | Sun: {m['sun_data']} | Time: {m['timestamp']}"
            for m in recent
        ])
        prompt = f"Here are the user's last 7 mood logs:\n{history_text}\nDetect any environmental pattern (e.g. they feel tired on cloudy days). Keep it down to a 1 sentence friendly insight linking their mood to space/environment."
        
        request_body = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "system": "You are Aura. Be warm, concise, and insightful.",
            "stream": False,
            "options": {**OLLAMA_OPTIONS, "num_ctx": OLLAMA_NUM_CTX},
            "keep_alive": OLLAMA_KEEP_ALIVE,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json=request_body,
                )
                response.raise_for_status()
                insight = response.json().get("response", "").strip()
        except Exception as e:
            print(f"[Pattern Detection] Failed to generate insight: {type(e).__name__} - {str(e)}")
            insight = None
    # Get mood-specific activity suggestions, adapted to user profile
    from backend.core.mood_activities import get_mood_activities
    from backend.services.profile import get_user_profile
    user_prof = get_user_profile(user_id)
    activities = get_mood_activities(data.mood, count=3, profile=user_prof)
            
    return {"status": "logged", "insight": insight, "activities": activities}


@router.get("/{user_id}/pattern")
async def get_pattern(user_id: str):
    """Get the predicted wellness pattern for a user using ROCKET classifier."""
    from backend.core.timeseries import get_classifier
    
    classifier = get_classifier()
    pattern = classifier.predict(user_id)
    
    if pattern is None:
        return {
            "pattern": None,
            "message": "Not enough data yet. Keep logging moods to discover your pattern!"
        }
    
    label_info = classifier.get_pattern_label(pattern)
    return {
        "pattern": pattern,
        "label": label_info["label"],
        "emoji": label_info["emoji"],
        "description": label_info["description"],
    }
