from sqlmodel import SQLModel

class UserMake(SQLModel):
    username: str

class Chat(SQLModel):
    user_id: int
    con_id: int
    question: str

class Con(SQLModel):
    user_id: int

class Messages(SQLModel):
    con_id: int
    role: str
    content: str

class UserId(SQLModel):
    id: int