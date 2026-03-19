from sqlmodel import SQLModel

class UserMake(SQLModel):
    username: str

class Chat(SQLModel):
    member_id: int
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

class BookIds(SQLModel):
    ids: list[int]