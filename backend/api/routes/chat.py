"""
Chat API — Natural conversation with Aura.
Handles text-based interaction and conversation history.
Supports both standard and streaming (SSE) responses.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
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
    # Safety check
    from backend.core.safety import check_text_safety
    safety = check_text_safety(payload.message)
    if not safety["safe"]:
        log_conversation(payload.user_id, payload.message, safety["response"])
        return ChatResponse(reply=safety["response"], context_used=["safety_filter"])

    try:
        reply, context = await generate_response(
            user_message=payload.message,
            user_id=payload.user_id,
        )
        log_conversation(payload.user_id, payload.message, reply)
        return ChatResponse(reply=reply, context_used=context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def stream_message(payload: ChatMessage):
    """Stream a response word-by-word using Server-Sent Events (SSE).
    This provides a ChatGPT-like typing effect for better perceived latency."""
    import httpx
    from backend.core.safety import check_text_safety
    from backend.core.llm import get_dynamic_system_prompt
    from backend.core.rag import get_relevant_knowledge
    from backend.services.profile import get_user_profile
    from backend.config import (
        OLLAMA_BASE_URL, OLLAMA_MODEL,
        OLLAMA_OPTIONS, OLLAMA_KEEP_ALIVE, OLLAMA_NUM_CTX,
    )

    # Safety check
    safety = check_text_safety(payload.message)
    if not safety["safe"]:
        log_conversation(payload.user_id, payload.message, safety["response"])
        async def safety_stream():
            yield f"data: {safety['response']}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(safety_stream(), media_type="text/event-stream")

    # Build context (same as generate_response)
    profile = get_user_profile(payload.user_id)
    knowledge_chunks = get_relevant_knowledge(payload.message, profile)
    context_texts = [chunk["text"] for chunk in knowledge_chunks] if knowledge_chunks else []

    profile_text = (
        f"User Profile => Household: {profile.get('household_members', 'unknown')}, "
        f"Mobility: {profile.get('mobility_notes', 'none noted')}, "
        f"Space: {profile.get('space_type', 'unknown')}"
    ) if profile else "No profile data."

    context_block = "\n".join(context_texts[:3]) if context_texts else ""
    knowledge_note = ""
    if context_block:
        knowledge_note = (
            f"[Background knowledge — DO NOT quote this directly]\n"
            f"{context_block}\n\n"
        )

    full_prompt = (
        f"{knowledge_note}"
        f"[About this person]\n{profile_text}\n\n"
        f"[Their question]\n{payload.message}\n\n"
        f"Remember: respond like a warm friend, not a textbook. Keep it short and personal."
    )

    request_body = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "system": get_dynamic_system_prompt(profile),
        "stream": True,
        "options": {**OLLAMA_OPTIONS, "num_ctx": OLLAMA_NUM_CTX},
        "keep_alive": OLLAMA_KEEP_ALIVE,
    }

    async def event_stream():
        full_reply = ""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json=request_body,
                ) as response:
                    import json
                    async for line in response.aiter_lines():
                        if line.strip():
                            chunk = json.loads(line)
                            token = chunk.get("response", "")
                            if token:
                                full_reply += token
                                yield f"data: {token}\n\n"
                            if chunk.get("done", False):
                                break
        except Exception as e:
            yield f"data: [ERROR: {str(e)}]\n\n"

        # Log the complete conversation
        if full_reply.strip():
            log_conversation(payload.user_id, payload.message, full_reply.strip())

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/history/{user_id}")
async def get_history(user_id: str, limit: int = 20):
    """Retrieve recent conversation history for a user."""
    from backend.db.sqlite import get_conversation_history
    return get_conversation_history(user_id, limit)
