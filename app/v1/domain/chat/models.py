from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import Field, Relationship, SQLModel
from app.v1.common.models.user import Member


class MessageRole(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"


# ──────────────────────────────────────
# 챗봇 세션 (chat_ai_session)
# ──────────────────────────────────────
class ChatAiSession(SQLModel):
    __tablename__ = "chat_ai_session"

    id: Optional[int] = Field(default=None, primary_key=True)
    member_id: int = Field(foreign_key="member.id", nullable=False, index=True)
    title: str = Field(max_length=20, nullable=False)
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=False)

    member: Optional[Member] = Relationship(back_populates="sessions")
    messages: list["ChatAiMessage"] = Relationship(back_populates="session")


# ──────────────────────────────────────
# 챗봇 메시지 (chat_ai_message)
# ──────────────────────────────────────
class ChatAiMessage(SQLModel):
    __tablename__ = "chat_ai_message"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chat_ai_session.id", nullable=False, index=True)
    content: str = Field(max_length=10000, nullable=False)
    token_usage: int = Field(nullable=False)
    role: MessageRole = Field(nullable=False)
    create_at: datetime = Field(default_factory=datetime.now, nullable=False)

    session: Optional[ChatAiSession] = Relationship(back_populates="messages")
    images: list["ChatAiImage"] = Relationship(back_populates="message")


# ──────────────────────────────────────
# 챗봇 이미지 (chat_ai_image)
# ──────────────────────────────────────
class ChatAiImage(SQLModel):
    __tablename__ = "chat_ai_image"

    id: Optional[int] = Field(default=None, primary_key=True)
    message_id: int = Field(foreign_key="chat_ai_message.id", nullable=False, index=True)
    image_url: str = Field(max_length=1000, nullable=False)
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)

    message: Optional[ChatAiMessage] = Relationship(back_populates="images")