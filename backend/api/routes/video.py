"""
Video API — Room video upload, labelling, and memory retrieval.
Endpoints:
  POST /api/video/upload  — upload + analyse video
  POST /api/video/label   — label current scan result as a named room
  GET  /api/video/rooms/{user_id} — list user's saved rooms
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional

from backend.core.video import extract_frames, analyse_video_frames, save_room_to_memory, get_user_rooms

router = APIRouter()


class LabelRequest(BaseModel):
    user_id: str = "default"
    room_label: str
    description: str = ""
    analysis: Optional[dict] = None


@router.post("/upload")
async def upload_video(
    video: UploadFile = File(...),
    user_id: str = Form("default"),
    room_label: Optional[str] = Form(None),
):
    """
    Upload a video file for multi-frame spatial analysis.
    Optionally label the room immediately (e.g. 'Living Room').
    """
    try:
        video_bytes = await video.read()

        if len(video_bytes) < 1000:
            raise HTTPException(status_code=400, detail="Video file is too small or empty.")

        # Extract frames
        frames = extract_frames(video_bytes, max_frames=4)

        if not frames:
            raise HTTPException(
                status_code=422,
                detail="Could not extract frames. Please install opencv-python-headless or try a different video format."
            )

        # Analyse frames
        analysis = await analyse_video_frames(frames, room_label=room_label, user_id=user_id)

        # Save to room memory if label provided
        if room_label:
            save_room_to_memory(user_id, room_label, analysis)

        return {
            "status": "success",
            "user_id": user_id,
            "room_label": room_label,
            "analysis": analysis,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/label")
async def label_room(payload: LabelRequest):
    """
    Label a room manually and save a description (or full analysis) to memory.
    Used when the user says 'This is my living room' after a scan.
    """
    try:
        # If full analysis passed, use it; otherwise create minimal
        analysis = payload.analysis or {
            "description": payload.description or f"User's {payload.room_label}",
            "objects_detected": [],
            "risks_identified": [],
            "suggestions": [],
            "frames_analysed": 0,
        }

        saved = save_room_to_memory(payload.user_id, payload.room_label, analysis)

        return {
            "status": "saved" if saved else "error",
            "room_label": payload.room_label,
            "user_id": payload.user_id,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rooms/{user_id}")
async def get_rooms(user_id: str):
    """
    List all saved rooms for a user.
    """
    try:
        rooms = get_user_rooms(user_id)
        return {"user_id": user_id, "rooms": rooms, "count": len(rooms)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
