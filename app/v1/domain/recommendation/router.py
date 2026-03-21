from fastapi import APIRouter
from app.v1.common.dependencies import SessionDep
from app.v1.domain.recommendation.services.book_recommendation import book_recommendation_service


recommend_router = APIRouter()


@recommend_router.post("/recommend_books/{limit}")
async def recommend_books(session: SessionDep, member_id: int, limit: int = 10):
    result = book_recommendation_service.book_sim(session, member_id, limit)
    if not result:
        return {"message": "no recommendation"}
    return [(n,d,t) for t,n,d in result]