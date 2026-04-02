"""
Chat API — Natural conversation with Aura.
Handles text-based interaction and conversation history.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.core.llm import generate_response
from backend.db.sqlite import log_conversation

router = APIRouter()


class ChatMessage(BaseModel):
    message: str
    user_id: str = "default"


class ChatResponse(BaseModel):
    reply: str
    context_used: list[str] = []


@router.post("/send", response_model=ChatResponse)
async def send_message(payload: ChatMessage):
    """Send a message to Aura and receive a contextual reply."""
    try:
        reply, context = await generate_response(
            user_message=payload.message,
            user_id=payload.user_id,
        )
        log_conversation(payload.user_id, payload.message, reply)
        return ChatResponse(reply=reply, context_used=context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{user_id}")
async def get_history(user_id: str, limit: int = 20):
    """Retrieve recent conversation history for a user."""
    from backend.db.sqlite import get_conversation_history
    return get_conversation_history(user_id, limit)
