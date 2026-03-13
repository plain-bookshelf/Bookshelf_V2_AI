from db.session import engine
from db.schemas import BookVector, Books
from sqlmodel import select, Session, asc, cast, Float, func


def book_sim(session: Session, book_id: int, limit: int):
    stmt = select(BookVector).where(BookVector.Books_id == book_id)
    vector = session.exec(stmt).first()
    distance_expr = cast(BookVector.embedding.op("<=>")(vector.embedding), Float)

    result = (
        select(
            Books.titles,
            func.min(BookVector.Books_id).label("Books_id"),
            func.min(distance_expr).label("distance")
        )
        .join(BookVector, BookVector.Books_id == Books.id)
        .group_by(Books.titles)
        .order_by(asc("distance"))
        .limit(limit+1)
    )

    return session.exec(result).all()[1:]


# with Session(engine) as session:
#     rows = book_sim(session, 8813, limit=15)
#     print(rows)
#     for t, n, d in rows:
#         print(n,d,t)