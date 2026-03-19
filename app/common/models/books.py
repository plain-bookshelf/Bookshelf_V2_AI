from datetime import date, datetime
from typing import Optional, List
from sqlmodel import Field, Relationship, SQLModel, Column
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import TSVECTOR

# ──────────────────────────────────────
# 장르 (genre)
# ──────────────────────────────────────
class Genre(SQLModel):
    __tablename__ = "genre"

    id: Optional[int] = Field(default=None, primary_key=True)
    genre_name: str = Field(max_length=45, nullable=False, unique=True)

    book_links: list["BookGenre"] = Relationship(back_populates="genre")


# ──────────────────────────────────────
# 책 장르 (book_genre) — 다대다 중간 테이블
# ──────────────────────────────────────
class BookGenre(SQLModel):
    __tablename__ = "book_genre"

    book_id: int = Field(foreign_key="book.id", primary_key=True)
    genre_id: int = Field(foreign_key="genre.id", primary_key=True)

    book: Optional["Book"] = Relationship(back_populates="genre_links")
    genre: Optional[Genre] = Relationship(back_populates="book_links")


# ──────────────────────────────────────
# 책 (book)
# ──────────────────────────────────────
class Book(SQLModel):
    __tablename__ = "book"

    id: Optional[int] = Field(default=None, primary_key=True)
    affiliation_id: int = Field(nullable=False, index=True)
    title: str = Field(max_length=100, nullable=False)
    author: str = Field(max_length=100, nullable=False)
    publication_date: Optional[str] = Field(default=None, max_length=20)
    introduction: str = Field(max_length=1000, nullable=False)
    book_image: str = Field(max_length=100, nullable=False)
    publisher: Optional[str] = Field(default=None, max_length=20)
    rental_count: int = Field(default=0, nullable=False)
    reservation_count: int = Field(default=0, nullable=False)
    like_count: int = Field(default=0, nullable=False)
    similarity_token: Optional[str] = Field(default=None, max_length=1000)

    genre_links: list[BookGenre] = Relationship(back_populates="book")
    chunks: list["BookChunk"] = Relationship(back_populates="book")
    similarities: list["BookSimilarity"] = Relationship(back_populates="book")
    details: list["BookDetail"] = Relationship(back_populates="book")


# ──────────────────────────────────────
# 책 유사도 (book_similarity)
# ──────────────────────────────────────
class BookSimilarity(SQLModel):
    __tablename__ = "book_similarity"

    book_id: int = Field(primary_key=True, foreign_key="book.id")
    vector_similarity: List[float] = Field(
        sa_column=Column(Vector(1024)),
    )
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=False)

    book: Optional[Book] = Relationship(back_populates="similarities")


# ──────────────────────────────────────
# 책 청크 (book_chunk)
# ──────────────────────────────────────
class BookChunk(SQLModel):
    __tablename__ = "book_chunk"

    book_id: int = Field(primary_key=True, foreign_key="book.id")
    chunk: str = Field(max_length=1000, nullable=False)
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=False)

    book: Optional[Book] = Relationship(back_populates="chunks")


# ──────────────────────────────────────
# 책 상세정보 (book_detail)
# ──────────────────────────────────────
class BookDetail(SQLModel):
    __tablename__ = "book_detail"

    id: Optional[int] = Field(default=None, primary_key=True)
    member_id: int = Field(foreign_key="member.id", nullable=False, index=True)
    book_id: int = Field(foreign_key="book.id", nullable=False, index=True)
    affiliation_id: int = Field(nullable=False, index=True)
    rental_request_status: bool = Field(nullable=False)
    rental_status: bool = Field(nullable=False)
    return_date: date = Field(nullable=False)
    registration_number: str = Field(max_length=100, nullable=False)
    call_number: str = Field(max_length=45, nullable=False)

    book: Optional[Book] = Relationship(back_populates="details")