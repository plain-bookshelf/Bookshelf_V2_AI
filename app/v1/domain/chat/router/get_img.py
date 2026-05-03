from fastapi import APIRouter
from sqlmodel import select
from app.v1.common.dependencies import SessionDep
from app.v1.common.models.book_tables import Book
from app.v1.domain.chat.models import ChatAiImage, ChatAiMessage
from app.v1.domain.chat.schemas import ImgIds, BookImgs
from app.v1.common.error.exception import MessageNotFoundException


img_router = APIRouter()


@img_router.post("/get_and_add_imgs")
async def send_imgs(session: SessionDep, img_ids: ImgIds):
    stmt = select(ChatAiMessage).where(ChatAiMessage.id == img_ids.message_id)
    chat_session = session.exec(stmt).first()
    if not chat_session:
        raise MessageNotFoundException(message_id=img_ids.message_id)

    stmt = select(Book).where(Book.id.in_(img_ids.ids))
    result = session.exec(stmt).all()
    if not result:
        return BookImgs(book_imgs=[])

    for book in result:
        session.add(ChatAiImage(message_id=img_ids.message_id, image_url=book.book_image))
    session.commit()

    imgs_data = [book.book_image for book in result]

    return BookImgs(book_imgs=imgs_data)