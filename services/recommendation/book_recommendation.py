from db.schemas import BookVector, Books
from sqlmodel import select, Session, cast, Float, func, true


def book_sim(session: Session, book_ids: list[int], limit: int):

    targets = (
        select(BookVector.embedding.label("t_emb"))
        .where(BookVector.Books_id.in_(book_ids))
        .subquery()
    )

    dist = cast(BookVector.embedding.op("<=>")(targets.c.t_emb), Float)

    per_copy = (
        select(
            Books.id.label("book_id"),
            Books.titles.label("title"),
            func.min(dist).label("distance"),
        )
        .join(BookVector, BookVector.Books_id == Books.id)
        .join(targets, true())
        .where(~Books.id.in_(book_ids))
        .group_by(Books.id, Books.titles)
        .subquery()
    )

    ranked = (
        select(
            per_copy.c.title,
            per_copy.c.book_id,
            per_copy.c.distance,
            func.row_number().over(
                partition_by=per_copy.c.title,
                order_by=(per_copy.c.distance, per_copy.c.book_id),
            ).label("rn"),
        )
        .subquery()
    )

    result = (
        select(ranked.c.title, ranked.c.book_id, ranked.c.distance)
        .where(ranked.c.rn == 1)
        .where(ranked.c.distance > 0.09)
        .order_by(ranked.c.distance)
        .limit(limit)
    )

    return session.exec(result).all()


# from db.session import engine
# with Session(engine) as session:
#     rows = book_sim(session, [4503], limit=15)
#     print(rows)
#     for t, n, d in rows:
#         print(n,d,t)