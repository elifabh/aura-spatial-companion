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
    knowledge = get_relevant_knowledge(payload.context, profile)
    recommendations = await generate_recommendation(
        profile=profile,
        knowledge=knowledge,
        context=payload.context,
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
    ]
