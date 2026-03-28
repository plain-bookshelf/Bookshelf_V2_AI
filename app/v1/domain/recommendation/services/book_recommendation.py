# from sqlmodel import cast, Float, func, true
# from sqlmodel import select, Session
# from app.v1.common.models.book_tables import BookDetail
# from app.v1.common.models.book_tables import BookSimilarity
# from app.v1.common.models.book_tables import BookAffiliation
#
#
# class BookRecommendationService:
#
#     @staticmethod
#     def _get_user_books_id(session: Session, member_id: int):
#         statement = (
#             select(BookDetail.book_affiliation_id)
#             .where(BookDetail.member_id == member_id)
#             .where(BookDetail.rental_status == True)
#         )
#         result = session.exec(statement).all()
#
#         if not result:
#             return []
#         return result
#
#
#     def book_sim(self, session: Session, member_id: int, limit: int):
#         book_ids = self._get_user_books_id(session, member_id)
#         if not book_ids:
#             return []
#
#         targets = (
#             select(BookSimilarity.vector_similarity.label("t_emb"))
#             .where(BookSimilarity.book_affiliationid.in_(book_ids))
#             .subquery()
#         )
#
#         dist = cast(BookSimilarity.vector_similarity.op("<=>")(targets.c.t_emb), Float)
#
#         per_copy = (
#             select(
#                 BookAffiliation.id.label("book_id"),
#                 BookAffiliation.book.title.label("title"),
#                 BookAffiliation.book.book_image.label("img"),
#                 func.min(dist).label("distance"),
#             )
#             .join(BookSimilarity, BookSimilarity.book_affiliationid == BookAffiliation.id)
#             .join(targets, true())
#             .where(~BookAffiliation.id.in_(book_ids))
#             .group_by(BookAffiliation.id, BookAffiliation.book.title, BookAffiliation.book.book_image)
#             .subquery()
#         )
#
#         ranked = (
#             select(
#                 per_copy.c.title,
#                 per_copy.c.book_id,
#                 per_copy.c.img,
#                 per_copy.c.distance,
#                 func.row_number().over(
#                     partition_by=per_copy.c.title,
#                     order_by=(per_copy.c.distance, per_copy.c.book_id),
#                 ).label("rn"),
#             )
#             .subquery()
#         )
#
#         result = (
#             select(ranked.c.title, ranked.c.book_id, ranked.c.img, ranked.c.distance)
#             .where(ranked.c.rn == 1)
#             .where(ranked.c.distance > 0.09)
#             .order_by(ranked.c.distance)
#             .limit(limit)
#         )
#
#         return session.exec(result).all()
#
#
# book_recommendation_service = BookRecommendationService()


from sqlmodel import cast, Float, func, true, select, Session
from app.v1.common.models.book_tables import (
    Book,
    BookAffiliation,
    BookDetail,
    BookSimilarity,
)


def get_user_book_ids(session: Session, member_id: int) -> list[int]:
    statement = (
        select(BookDetail.book_affiliation_id)
        .where(BookDetail.member_id == member_id)
        .where(BookDetail.rental_status == True)
    )
    result = session.exec(statement).all()
    return list(result) if result else []


def recommend_by_similarity(
    session: Session, member_id: int, limit: int
):
    book_ids = get_user_book_ids(session, member_id)
    if not book_ids:
        return []

    targets = (
        select(BookSimilarity.vector_similarity.label("t_emb"))
        .where(BookSimilarity.book_affiliationid.in_(book_ids))
        .subquery()
    )

    dist = cast(
        BookSimilarity.vector_similarity.op("<=>")(targets.c.t_emb), Float
    )

    per_copy = (
        select(
            BookAffiliation.id.label("book_affiliation_id"),
            Book.title.label("title"),
            Book.book_image.label("img"),
            func.min(dist).label("distance"),
        )
        .select_from(BookAffiliation)
        .join(BookSimilarity, BookSimilarity.book_affiliationid == BookAffiliation.id)
        .join(Book, Book.id == BookAffiliation.book_id)
        .join(targets, true())
        .where(~BookAffiliation.id.in_(book_ids))
        .group_by(BookAffiliation.id, Book.title, Book.book_image)
        .subquery()
    )

    ranked = (
        select(
            per_copy.c.title,
            per_copy.c.book_affiliation_id,
            per_copy.c.img,
            per_copy.c.distance,
            func.row_number()
            .over(
                partition_by=per_copy.c.title,
                order_by=(per_copy.c.distance, per_copy.c.book_affiliation_id),
            )
            .label("rn"),
        )
        .subquery()
    )

    result = (
        select(
            ranked.c.title,
            ranked.c.book_affiliation_id,
            ranked.c.img,
            ranked.c.distance,
        )
        .where(ranked.c.rn == 1)
        .where(ranked.c.distance > 0.09)
        .order_by(ranked.c.distance)
        .limit(limit)
    )

    return session.exec(result).all()