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

from backend.core.vision import analyse_space_image, analyse_zones

from backend.db.sqlite import log_space_analysis, log_zone_analysis

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


class Zone(BaseModel):
    id: str
    label: str
    type: str
    color: str
    description: str
    recommendation: str
    priority: int
    x_percent: float
    y_percent: float
    width_percent: float
    height_percent: float

class ZoneAnalysisResponse(BaseModel):
    zones: list[Zone]
    overall_score: int
    summary: str
    groups_detected: list[str] = []


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


@router.post("/zone-analysis", response_model=ZoneAnalysisResponse)
async def zone_analysis(
    image: UploadFile = File(...),
    user_id: str = "default",
):
    """
    Analyse an uploaded image and return profile-personalised spatial zones.
    Each zone includes type, colour, coordinates (as % of image), and a recommendation.
    Results are saved to SQLite.
    """
    try:
        contents = await image.read()
        image_b64 = base64.b64encode(contents).decode("utf-8")

        result = await analyse_zones(image_b64, user_id)

        log_zone_analysis(
            user_id=user_id,
            zones=result.get("zones", []),
            overall_score=result.get("overall_score", 0),
            summary=result.get("summary", ""),
        )

        return ZoneAnalysisResponse(**result)
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


@router.get("/demo-zones/{user_id}", response_model=ZoneAnalysisResponse)
async def get_demo_zones(user_id: str):
    """
    Return pre-seeded zone analysis for a demo profile without requiring camera access.
    Fetches the most recent zone analysis stored for this user from SQLite.
    Valid user_ids: sarah, seamus, ms_murphy
    """
    from backend.db.sqlite import get_zone_analyses

    DEMO_USERS = {"sarah", "seamus", "ms_murphy"}
    if user_id not in DEMO_USERS:
        raise HTTPException(
            status_code=400,
            detail=f"'{user_id}' is not a demo profile. Valid options: {', '.join(DEMO_USERS)}"
        )

    rows = get_zone_analyses(user_id, limit=1)
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No demo zones found for '{user_id}'. Ensure the server has completed startup seeding."
        )

    row = rows[0]
    return ZoneAnalysisResponse(
        zones=[Zone(**z) for z in row["zones"]],
        overall_score=row["overall_score"],
        summary=row["summary"],
    )
