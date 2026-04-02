"""
Camera API — Spatial vision analysis.
Receives images from the device camera and analyses them
using LLaVA for spatial understanding.
"""

import base64
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from backend.core.vision import analyse_space_image

router = APIRouter()


class VisionResponse(BaseModel):
    description: str
    objects_detected: list[str]
    suggestions: list[str]


@router.post("/analyse", response_model=VisionResponse)
async def analyse_image(image: UploadFile = File(...), user_id: str = "default"):
    """
    Analyse an uploaded image of the user's space.
    Returns detected objects, description, and personalised suggestions.
    """
    try:
        contents = await image.read()
        image_b64 = base64.b64encode(contents).decode("utf-8")

        result = await analyse_space_image(image_b64, user_id)
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
