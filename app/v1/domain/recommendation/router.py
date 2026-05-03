from fastapi import APIRouter
from app.v1.domain.chat.services.chat_service.get_infos import get_member
from app.v1.common.dependencies import SessionDep
from app.v1.domain.recommendation.services.book_recommendation import recommend_by_similarity
from app.v1.domain.recommendation.schemas import BookResponse, BookInfo

recommend_router = APIRouter()


@recommend_router.get("/recommend_books/{username}")
async def recommend_books(session: SessionDep, username: str, limit: int = 20):
    member = get_member(session, username)

    result = recommend_by_similarity(session, member.id, limit)
    if not result:
        return BookResponse(books=[])

    books_data = [BookInfo(id=book_id, title=title, img=img, dis=dis)
                  for title, book_id, img, dis in result]

    return BookResponse(books=books_data)