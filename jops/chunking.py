from sqlmodel import Session, select
from db.schemas import Books

def get_chunks(session: Session):
    chunk = []
    ids = []
    books = session.exec(select(Books)).all()
    for book in books:
        sen = "\n".join([
            f"[제목] {book.titles}",
            f"[제목] {book.titles}",
            f"[저자] {book.authors}",
            f"[저자] {book.authors}",
            f"[장르] {book.genres if book.genres != 'NaN' else ''}",
            f"[장르] {book.genres if book.genres != 'NaN' else ''}",
            f"[출판사] {book.publisher if book.publisher != 'NaN' else ''}",
            f"[책소개] {book.intro if book.intro != 'NaN' else ''}",
        ]).strip()
        chunk.append(sen)
        ids.append(book.id)

    return chunk, ids