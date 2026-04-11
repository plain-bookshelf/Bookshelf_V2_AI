from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import Field, Relationship, SQLModel


# ──────────────────────────────────────
# ENUM
# ──────────────────────────────────────
class MemberRole(str, Enum):
    ROLE_USER = "ROLE_USER"
    ADMIN = "admin"


# ──────────────────────────────────────
# 유저 (member)
# ──────────────────────────────────────
class Member(SQLModel, table=True):
    __tablename__ = "member"

    id: Optional[int] = Field(default=None, primary_key=True)
    affiliation_id: int = Field(nullable=False, index=True)
    username: str = Field(max_length=45, nullable=False, unique=True)
    nickname: str = Field(max_length=45, nullable=False)
    password: str = Field(max_length=100, nullable=False)
    email: str = Field(max_length=45, nullable=False, unique=True)
    role: MemberRole = Field(nullable=False)
    profile_image: str = Field(max_length=1000, nullable=False)
    one_month_statistics: int = Field(default=0, nullable=False)
    overdue_term: datetime = Field(nullable=False)
    often_book_read_time: datetime = Field(nullable=False)
    rental_count: int
    reservation_count: int
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=False)

    sessions: list["ChatAiSession"] = Relationship(back_populates="member")