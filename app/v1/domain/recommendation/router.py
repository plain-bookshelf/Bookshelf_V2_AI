from fastapi import APIRouter
from app.v1.common.dependencies import SessionDep
from app.v1.domain.recommendation.services.book_recommendation import recommend_by_similarity


recommend_router = APIRouter()


@recommend_router.post("/recommend_books")
async def recommend_books(session: SessionDep, member_id: int, limit: int = 10):
    result = recommend_by_similarity(session, member_id, limit)
    if not result:
        return {"message": "no recommendation"}
    return {
        "books": [
            {
                "id": book_id,
                "title": title,
                "img": img,
                "dis": dis
            } for title, book_id, img, dis in result
        ]
    }