from app.v1.common.models.book_tables import BookSimilarity, BookAffiliation, Book
from sqlmodel import select, Session, cast, Float, func


def embedding_sim(session: Session, ask_em: list[float], limit: int):
    distance_expr = cast(BookSimilarity.vector_similarity.op("<=>")(ask_em), Float)

    book_data = (
        select(
            Book.title.label("titles"),
            BookAffiliation.id.label("book_ids"),
            distance_expr.label("distances")
        )
        .select_from(BookAffiliation)
        .join(BookSimilarity, BookSimilarity.book_affiliationid == BookAffiliation.id)
        .join(Book, Book.id == BookAffiliation.book_id)
        .subquery()
    )

    ranked = (
        select(
            book_data.c.titles,
            book_data.c.book_ids,
            book_data.c.distances,
            func.row_number().over(
                partition_by=book_data.c.titles,
                order_by=(book_data.c.distances, book_data.c.book_ids)
            ).label("rank")
        )
        .subquery()
    )

    result = (
        select(
            ranked.c.titles,
            ranked.c.book_ids,
            ranked.c.distances
        )
        .where(ranked.c.rank == 1)
        .order_by(ranked.c.distances)
        .limit(limit)
    )

    return session.exec(result).all()