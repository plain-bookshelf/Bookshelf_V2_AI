from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.session import create_tables
from api.chat import chat_router
from api.recommend import recommend_router

from db.models import UserMake
from db.schemas import User
from db.session import SessionDep


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    create_tables()

@app.post("/user")
async def create_user(session: SessionDep, user_in: UserMake):
    dict_user = user_in.model_dump()
    db_user = User.model_validate(dict_user)

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


app.include_router(chat_router)
app.include_router(recommend_router)