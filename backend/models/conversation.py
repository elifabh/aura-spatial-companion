"""Conversation data model."""

from datetime import datetime
from pydantic import BaseModel


class ConversationEntry(BaseModel):
    id: int | None = None
    user_id: str
    user_message: str
    aura_reply: str
    timestamp: datetime = datetime.now()
    context_sources: list[str] = []
