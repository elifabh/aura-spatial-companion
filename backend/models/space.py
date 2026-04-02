"""Space analysis data model."""

from pydantic import BaseModel


class SpaceAnalysis(BaseModel):
    description: str
    objects_detected: list[str] = []
    suggestions: list[str] = []
    safety_concerns: list[str] = []
    lighting_assessment: str = ""
