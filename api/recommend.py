from fastapi import APIRouter, HTTPException
from db.session import SessionDep
from db.models import UserId


recommend_router = APIRouter()

@recommend_router.post("/recommend_books")
async def recommend_books(session: SessionDep, user_id: UserId):
    pass