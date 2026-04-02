"""Recommendation data model."""

from pydantic import BaseModel


class Recommendation(BaseModel):
    title: str
    description: str
    category: str
    relevance_score: float = 0.0


class RecommendationSet(BaseModel):
    user_id: str
    recommendations: list[Recommendation]
    context: str = ""
