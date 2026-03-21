from fastapi import APIRouter, HTTPException
from sqlmodel import select
from app.local_test_version.db.session import SessionDep
from app.local_test_version.db.models import BookIds
from app.local_test_version.db.schemas import Books

send_data_router = APIRouter()


@send_data_router.post("/send_img")
async def send_img(session: SessionDep, book_list: BookIds):
    stmt = select(Books).where(Books.id.in_(list(set(book_list.ids))))
    result = session.exec(stmt).all()
    if not result:
        raise HTTPException(status_code=404, detail="<no result>")

    return {
        "imgs": [book.img for book in result]
    }