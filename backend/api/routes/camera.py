"""
Camera API — Spatial vision analysis.
Receives images from the device camera and analyses them
using Gemma 4 E4B for spatial understanding.
Supports optional compass heading for directional context.
"""

import base64
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from pydantic import BaseModel
from typing import Optional

from backend.core.vision import analyse_space_image

from backend.db.sqlite import log_space_analysis

router = APIRouter()


class Suggestion(BaseModel):
    action: str
    confidence: int
    why_this_matters: str

class VisionResponse(BaseModel):
    description: str
    objects_detected: list[str]
    risks_identified: list[str] = []
    suggestions: list[Suggestion | str] # Fallback for old str
    score: dict
    comparison: str
    sun_recommendations: list[str] = []


@router.post("/analyse", response_model=VisionResponse)
async def analyse_image(
    image: UploadFile = File(...),
    user_id: str = "default",
    compass_heading: Optional[float] = Query(None, description="Compass heading 0-360"),
    lat: Optional[float] = Query(None, description="Latitude for sun position"),
    lon: Optional[float] = Query(None, description="Longitude for sun position"),
):
    """
    Analyse an uploaded image of the user's space.
    Optional compass_heading + lat/lon enriches analysis with directional context.
    """
    try:
        contents = await image.read()
        image_b64 = base64.b64encode(contents).decode("utf-8")

        result = await analyse_space_image(image_b64, user_id)
        
        # Add sun/compass recommendations if location data provided
        sun_recommendations = []
        if lat is not None and lon is not None:
            try:
                from backend.services.sun import get_sun_recommendations
                from backend.services.profile import get_user_profile
                profile = get_user_profile(user_id)
                sun_recommendations = get_sun_recommendations(
                    lat, lon, compass_heading, profile
                )
            except Exception as e:
                print(f"[Camera] Sun recommendations error: {e}")
        
        result["sun_recommendations"] = sun_recommendations
        
        # Save to SQLite
        log_space_analysis(
            user_id=user_id,
            description=result.get("description", ""),
            objects=result.get("objects_detected", []),
            suggestions=result.get("suggestions", []),
            score=result.get("score", {})
        )
        
        return VisionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/snapshot")
async def camera_snapshot(image: UploadFile = File(...)):
    """Quick snapshot analysis — returns a plain-text summary."""
    try:
        contents = await image.read()
        image_b64 = base64.b64encode(contents).decode("utf-8")
        result = await analyse_space_image(image_b64)
        return {"summary": result.get("description", "")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
