from sqlmodel import SQLModel

class UserMake(SQLModel):
    username: str

class Chat(SQLModel):
    username: str
    session_id: int
    question: str

class Con(SQLModel):
    user_id: int

class Messages(SQLModel):
    con_id: int
    role: str
    content: str

class UserId(SQLModel):
    id: int

class ImgIds(SQLModel):
    message_id: int
    ids: list[int]