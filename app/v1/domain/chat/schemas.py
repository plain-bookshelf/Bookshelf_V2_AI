from pydantic import BaseModel


class Chat(BaseModel):
    username: str
    session_id: int
    question: str


class ChatAnswer(BaseModel):
    agent: dict
    message_id: int


class ImgIds(BaseModel):
    message_id: int
    ids: list[int]


class BookImgs(BaseModel):
    book_imgs: list[str]