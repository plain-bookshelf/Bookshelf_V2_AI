from app.common.models.books import BookSimilarity
from sqlmodel import cast, Float, func, true
from sqlmodel import select, Session
from app.common.models.books import Book
from app.common.models.books import BookDetail


class BookRecommendationService:

    @staticmethod
    def _get_user_books_id(session: Session, member_id: int):
        statement = (
            select(BookDetail.book_id)
            .where(BookDetail.member_id == member_id)
            .where(BookDetail.rental_status == True)
        )
        result = session.exec(statement).all()

        if not result:
            return []
        return result


    def book_sim(self, session: Session, member_id: int, limit: int):
        book_ids = self._get_user_books_id(session, member_id)

        targets = (
            select(BookSimilarity.vector_similarity.label("t_emb"))
            .where(BookSimilarity.book_id.in_(book_ids))
            .subquery()
        )

        dist = cast(BookSimilarity.vector_similarity.op("<=>")(targets.c.t_emb), Float)

        per_copy = (
            select(
                Book.id.label("book_id"),
                Book.title.label("title"),
                func.min(dist).label("distance"),
            )
            .join(BookSimilarity, BookSimilarity.book_id == Book.id)
            .join(targets, true())
            .where(~Book.id.in_(book_ids))
            .group_by(Book.id, Book.titles)
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