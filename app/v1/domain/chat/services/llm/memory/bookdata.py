from sqlmodel import select, Session
from app.v1.common.error.exception import SessionNotFoundException
from app.v1.domain.chat.models import ChatAiSession


def get_book_datas(session: Session, con_id: int):

    statement = select(ChatAiSession).where(ChatAiSession.id == con_id)
    chat_session = session.exec(statement).first()

    if not chat_session:
        return SessionNotFoundException(session_id=con_id)

    if not chat_session.active_book_meta:
        return "현재 대화에 활성화된 도서 정보가 없습니다."

    formatted_books = []
    for book in chat_session.active_book_meta:
        title = book.get("title", "제목없음")
        author = book.get("author", "저자미상")
        call_number = book.get("call_number", "정보없음")
        reg_numbers = book.get("reg_numbers", "정보없음")
        book_id = book.get("id", "알수없음")

        formatted_books.append(
            f"- 『{title}』 ({author}) | 청구기호: {call_number} | 등록번호: {reg_numbers} | 책 ID: {book_id}"
        )
    return "\n".join(formatted_books)


def update_session_book_meta(session: Session, con_id: int, new_chunks: list):

    stmt = select(ChatAiSession).where(ChatAiSession.id == con_id)
    chat_session = session.exec(stmt).first()

    if not chat_session:
        return SessionNotFoundException(session_id=con_id)

    new_metadata = []
    for chunk in new_chunks:
        category = ", ".join(gl.genre.genre_name for gl in chunk.book.genre_links) or "없음"
        reg_numbers = ", ".join(d.registration_number for d in chunk.details) or "없음"
        call_numbers = ", ".join(d.call_number for d in chunk.details) or "없음"

        meta = {
            "id": chunk.book.id,
            "title": chunk.book.title,
            "author": chunk.book.author,
            "category": category,
            "reg_numbers": reg_numbers,
            "call_number": call_numbers
        }
        new_metadata.append(meta)

    current_meta = chat_session.active_book_meta or []
    combined_meta = current_meta + new_metadata

    chat_session.active_book_meta = combined_meta[-10:]
    print("\n업데이트된 메타데이터:", chat_session.active_book_meta)

    session.add(chat_session)
    session.commit()