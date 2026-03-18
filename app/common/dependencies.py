from sqlmodel import Session
from typing import Annotated
from fastapi import Depends
from app.session import engine

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]