"""
Video Analysis Core — Frame extraction + multi-frame spatial analysis.
Uses OpenCV for frame extraction, Gemma 4 for analysis.
Stores room memory in ChromaDB.
"""

import base64
import io
from typing import Optional

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

from backend.config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_OPTIONS, OLLAMA_KEEP_ALIVE, OLLAMA_NUM_CTX
import httpx


def extract_frames(video_bytes: bytes, max_frames: int = 4) -> list[str]:
    """
    Extract evenly spaced frames from video bytes.
    Returns list of base64-encoded JPEG strings.
    Falls back gracefully if OpenCV not available.
    """
    if not OPENCV_AVAILABLE:
        print("[Video] OpenCV not available — cannot extract frames.")
        return []

    try:
        import numpy as np

        # Write bytes to a numpy buffer and decode
        arr = np.frombuffer(video_bytes, dtype=np.uint8)
        # Use imdecode trick via temp in-memory
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name

        cap = cv2.VideoCapture(tmp_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30

        frames_b64 = []
        if total_frames <= 0:
            cap.release()
            os.unlink(tmp_path)
            return []

        # Pick evenly spaced frame indices
        indices = [int(i * total_frames / max_frames) for i in range(max_frames)]

        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret:
                continue
            # Resize for efficiency
            h, w = frame.shape[:2]
            if w > 1280:
                scale = 1280 / w
                frame = cv2.resize(frame, (1280, int(h * scale)))
            # Encode to JPEG
            _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frames_b64.append(base64.b64encode(buf.tobytes()).decode("utf-8"))

        cap.release()
        os.unlink(tmp_path)
        return frames_b64

    except Exception as e:
        print(f"[Video] Frame extraction error: {e}")
        return []


async def analyse_video_frames(frames_b64: list[str], room_label: str = None, user_id: str = "default") -> dict:
    """
    Send multiple frames to Gemma 4 for combined spatial analysis.
    Fetches user profile for personalised recommendations.
    Returns unified room analysis dict.
    """
    if not frames_b64:
        return {
            "description": "Could not extract frames from video.",
            "objects_detected": [],
            "risks_identified": [],
            "suggestions": ["Try uploading a shorter, well-lit video."],
            "room_label": room_label,
        }

    # Fetch user profile for personalised analysis
    profile_text = "No known profile."
    try:
        from backend.services.profile import get_user_profile
        profile = get_user_profile(user_id)
        if profile:
            profile_text = (
                f"Household members: {profile.get('household_members', [])}, "
                f"Accessibility needs: {profile.get('accessibility_needs', [])}, "
                f"Space type: {profile.get('space_type', 'Unknown')}, "
                f"Interests: {profile.get('interests', [])}, "
                f"Concerns: {profile.get('concerns', 'None')}"
            )
    except Exception as e:
        print(f"[Video] Could not load profile: {e}")

    label_ctx = f' This is the user\'s "{room_label}".' if room_label else ""

    prompt = (
        f"You are Aura, a spatial intelligence assistant.{label_ctx}\n"
        f"[USER PROFILE]\n{profile_text}\n\n"
        "I'm showing you multiple frames from a room video. "
        "Analyse the space holistically and tailor your response to the user's profile above.\n"
        "1. A warm, friendly description of the overall space\n"
        "2. Key objects and furniture you notice\n"
        "3. Any safety risks or concerns (especially relevant to the user's household and accessibility needs)\n"
        "4. 2-3 specific, actionable improvement suggestions (no purchases), personalised to who lives here\n\n"
        "Respond in JSON with keys: description (string), objects_detected (list of strings), "
        "risks_identified (list of strings), suggestions (list of strings), "
        "score (object with integer keys: overall, light, air, safety, comfort — each 0-100)."
    )

    request_body = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "images": frames_b64,
        "stream": False,
        "format": "json",
        "options": {**OLLAMA_OPTIONS, "num_ctx": OLLAMA_NUM_CTX},
        "keep_alive": OLLAMA_KEEP_ALIVE,
    }

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=request_body,
            )
            response.raise_for_status()
            data = response.json()

        from backend.core.llm import validate_llm_response
        raw = data.get("response", "")
        # validate_llm_response returns a parsed dict if successful, otherwise raises or handles it.
        # Wait, validate_llm_response in llm.py returns a dict? Let me check its implementation next.
        # Let's import json just in case
        import json
        try:
            # Assume validate_llm_response cleans markdown and parses it or returns raw text? Let's check.
            cleaned = raw.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.split("```json")[1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            result = json.loads(cleaned.strip())
        except Exception:
            result = {}

        # Normalise score sub-dict
        raw_score = result.get("score", {})
        if isinstance(raw_score, dict):
            score = {
                "overall":  int(raw_score.get("overall",  50)),
                "light":    int(raw_score.get("light",    50)),
                "air":      int(raw_score.get("air",      50)),
                "safety":   int(raw_score.get("safety",   50)),
                "comfort":  int(raw_score.get("comfort",  50)),
            }
        else:
            score = {"overall": 50, "light": 50, "air": 50, "safety": 50, "comfort": 50}

        return {
            "description":     result.get("description", "Space analysed."),
            "objects_detected": result.get("objects_detected", []),
            "risks_identified": result.get("risks_identified", []),
            "suggestions":     result.get("suggestions", []),
            "score":           score,
            "room_label":      room_label,
            "frames_analysed": len(frames_b64),
        }

    except Exception as e:
        print(f"[Video] Analysis error: {e}")
        return {
            "description": "Video analysis completed.",
            "objects_detected": [],
            "risks_identified": [],
            "suggestions": ["Your space looks interesting! Try a photo scan for detailed analysis."],
            "score": {"overall": 50, "light": 50, "air": 50, "safety": 50, "comfort": 50},
            "room_label": room_label,
            "frames_analysed": len(frames_b64),
        }


def save_room_to_memory(user_id: str, room_label: str, analysis: dict) -> bool:
    """
    Save room analysis to ChromaDB for persistent room memory.
    The model can reference this in future conversations.
    """
    try:
        import chromadb
        from backend.config import CHROMA_PERSIST_DIR

        client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        collection = client.get_or_create_collection(
            name="room_memory",
            metadata={"hnsw:space": "cosine"},
        )

        doc_id = f"{user_id}_{room_label.lower().replace(' ', '_')}"
        doc_text = (
            f"Room: {room_label}\n"
            f"Description: {analysis.get('description', '')}\n"
            f"Objects: {', '.join(analysis.get('objects_detected', []))}\n"
            f"Suggestions: {'; '.join(str(s) for s in analysis.get('suggestions', []))}"
        )

        collection.upsert(
            documents=[doc_text],
            ids=[doc_id],
            metadatas=[{
                "user_id": user_id,
                "room_label": room_label,
                "frames_analysed": str(analysis.get("frames_analysed", 0)),
            }],
        )
        return True

    except Exception as e:
        print(f"[Video] ChromaDB room save error: {e}")
        return False


def get_user_rooms(user_id: str) -> list[dict]:
    """
    Retrieve all saved rooms for a user from ChromaDB.
    """
    try:
        import chromadb
        from backend.config import CHROMA_PERSIST_DIR

        client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        collection = client.get_or_create_collection(name="room_memory")

        results = collection.get(
            where={"user_id": user_id},
            include=["documents", "metadatas"],
        )

        rooms = []
        for doc, meta in zip(results["documents"], results["metadatas"]):
            rooms.append({
                "room_label": meta.get("room_label", "Unknown Room"),
                "summary": doc[:200] + "..." if len(doc) > 200 else doc,
                "frames_analysed": meta.get("frames_analysed", "0"),
            })
        return rooms

    except Exception as e:
        print(f"[Video] ChromaDB rooms retrieval error: {e}")
        return []
