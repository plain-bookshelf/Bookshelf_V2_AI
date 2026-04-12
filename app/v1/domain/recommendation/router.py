from fastapi import APIRouter
from sqlmodel import select
from app.v1.common.error.exception import MemberNotFoundException
from app.v1.common.dependencies import SessionDep
from app.v1.domain.recommendation.services.book_recommendation import recommend_by_similarity
from app.v1.common.models.user import Member

recommend_router = APIRouter()


@recommend_router.get("/recommend_books/{member_id}")
async def recommend_books(session: SessionDep, member_id: int, limit: int = 20):
    stmt = select(Member).where(Member.id == member_id)
    member = session.exec(stmt).first()
    if not member:
        raise MemberNotFoundException(member_id=member_id)

    result = recommend_by_similarity(session, member_id, limit)
    if not result:
        return {"books": []}
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