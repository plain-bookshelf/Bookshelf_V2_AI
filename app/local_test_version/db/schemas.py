from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, DateTime, func, Column
from datetime import datetime, timezone
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import TSVECTOR

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class TimestampMixin(SQLModel):
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "nullable": False,
            "server_default": func.now(),
        },
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "nullable": False,
            "server_default": func.now(),
            "onupdate": func.now(),   # UPDATE 시 자동 갱신(ORM이 UPDATE 만들 때 반영)
        },
    )

class Role(str, Enum):
    user = "user"
    assistant = "assistant"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: Optional[str] = Field(default=None, index=True, unique=True)

    conversations: List["Conversation"] = Relationship(back_populates="user")


class Conversation(TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)

    user: Optional[User] = Relationship(back_populates="conversations")
    messages: List["Message"] = Relationship(back_populates="conversation")


class Message(TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id", index=True)

    role: Role
    content: str

    conversation: Optional[Conversation] = Relationship(back_populates="messages")


#----------------------------------
# Book

class Books(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    titles: Optional[str] = Field(default=None)
    authors: Optional[str] = Field(default=None)
    publisher: Optional[str] = Field(default=None)
    school: str
    id_number: str
    call_num: str
    intro: Optional[str] = Field(default=None)
    date: Optional[str] = Field(default=None)
    img: Optional[str] = Field(default=None)
    genres: Optional[str] = Field(default=None)

    search_tsv: Optional[str] = Field(default=None, sa_column=Column(TSVECTOR)) # FTS


class BookVector(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    Books_id: Optional[int] = Field(default=None, unique=True ,foreign_key="books.id", index=True)
    embedding: Optional[List[float]] = Field(
        default=None,
        sa_column=Column(Vector(1024)),
    )

class BookChunk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    Books_id: int = Field(foreign_key="books.id", index=True, unique=True)
    chunk_text: Optional[str] = Field(default=None)