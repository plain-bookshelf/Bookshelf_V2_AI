from pydantic import BaseModel
from datetime import datetime


class Chat(BaseModel):
    username: str
    session_id: int
    question: str


class ChatAnswer(BaseModel):
    agent: dict
    message_id: int


class ChatSession(BaseModel):
    id: int
    member_id: int
    title: str
    created_at: datetime
    updated_at: datetime


class ImgIds(BaseModel):
    message_id: int
    ids: list[int]


class BookImgs(BaseModel):
    book_imgs: list[str]