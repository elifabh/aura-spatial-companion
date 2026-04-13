"""
Recommendations API — Personalised spatial suggestions.
Philosophy: "Live better with what you have."
No purchase suggestions. No major changes.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.core.rag import get_relevant_knowledge
from backend.core.llm import generate_recommendation
from backend.services.profile import get_user_profile

router = APIRouter()


class RecommendationRequest(BaseModel):
    user_id: str = "default"
    context: str = ""


class Recommendation(BaseModel):
    title: str
    description: str
    category: str
    relevance_score: float


@router.post("/generate", response_model=list[Recommendation])
async def generate_recommendations(payload: RecommendationRequest):
    """
    Generate personalised recommendations based on:
    - User profile (household, mobility, interests)
    - RAG knowledge base (Irish health & demographic data)
    - Current context (weather, time, recent observations)
    """
    profile = get_user_profile(payload.user_id)
    
    # Adım 7: Enrich context with weather and sun if it's broad
    enriched_context = payload.context
    if not enriched_context:
        try:
            from backend.services.weather import get_current_weather
            from backend.services.sun import get_sunrise_sunset
            # Fixed location for demo purposes, in production comes from frontend
            w = await get_current_weather(53.3498, -6.2603)
            s = get_sunrise_sunset(53.3498, -6.2603)
            enriched_context = (
                f"Weather: {w.get('weather_description', 'unknown')}, {w.get('temperature', '-')}°C. "
                f"Sunrise: {s.get('sunrise', '-')}, Sunset: {s.get('sunset', '-')}. "
                "Suggest daily routine or lifestyle adjustments based on this."
            )
        except Exception as e:
            print(f"[Recommendations] Context enrichment failed: {e}")

    knowledge = get_relevant_knowledge(enriched_context, profile)
    recommendations = await generate_recommendation(
        profile=profile,
        knowledge=knowledge,
        context=enriched_context,
    )
    return recommendations


@router.get("/categories")
async def list_categories():
    """List available recommendation categories."""
    return [
        "safety",
        "comfort",
        "organisation",
        "lighting",
        "air_quality",
        "activity",
        "accessibility",
        "lifestyle",
        "routine",
    ]

