from fastapi import APIRouter, HTTPException
from db.session import SessionDep
from db.models import UserId
from services.recommendation.book_recommendation import book_sim


recommend_router = APIRouter()

# 샘플
@recommend_router.post("/recommend_books/{limit}")
async def recommend_books(session: SessionDep, book_ids: list[int], limit: int = 10):
    result = book_sim(session, book_ids, limit)
    return [(n,d,t) for t,n,d in result]


# with Session(engine) as session:
#     rows = book_sim(session, [8813, 8578], limit=15)
#     print(rows)
#     for t, n, d in rows:
#         print(n,d,t)