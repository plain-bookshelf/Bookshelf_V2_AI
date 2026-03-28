from fastapi import APIRouter
from sqlmodel import select
from app.v1.common.dependencies import SessionDep
from app.v1.common.models.book_tables import Book
from app.v1.domain.chat.models import ChatAiImage
from app.v1.domain.chat.schemas import ImgIds


img_router = APIRouter()


@img_router.get("/get_imgs")
async def send_imgs(session: SessionDep, img_ids: ImgIds):
    stmt = select(Book).where(Book.id.in_(img_ids.ids))
    result = session.exec(stmt).all()
    if not result:
        return {"book_imgs": []}

    for book in result:
        session.add(ChatAiImage(message_id=img_ids.message_id, image_url=book.book_image))
    session.commit()

    return {
        "book_imgs": [
            book.book_image for book in result
        ]
    }