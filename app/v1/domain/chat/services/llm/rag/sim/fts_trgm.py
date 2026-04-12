from sqlmodel import Session, select, case, Float, cast, func, desc, or_
from app.v1.common.models.book_tables import BookAffiliation, Book


class Search:

    @staticmethod
    def fts_search(keywords: str):
        tsq = func.websearch_to_tsquery("simple", keywords)

        fts_rank_raw = func.ts_rank_cd(BookAffiliation.similarity_token, tsq)
        fts_score = case(
            (BookAffiliation.similarity_token.op("@@")(tsq), fts_rank_raw),
            else_=0.0
        ).label("fts_score")
        return fts_score


    @staticmethod
    def trgm_search(keywords: str):
        title_ns = func.replace(Book.title, " ", "")
        q_ns = func.replace(keywords, " ", "")

        trgm_raw = func.greatest(
            func.similarity(Book.title, keywords),
            func.similarity(title_ns, q_ns),
        )
        trgm_score = cast(trgm_raw, Float).label("trgm_score")
        return trgm_score


    def fts_trgm_search(self, session: Session, q: str, limit: int):
        q = (q or "").strip()
        if not q:
            return []

        tsq = func.websearch_to_tsquery("simple", q)
        fts_score = self.fts_search(q)
        trgm_score = self.trgm_search(q)
        score = fts_score + trgm_score

        stmt = (
            select(BookAffiliation, score)
            .select_from(BookAffiliation)
            .join(Book, Book.id == BookAffiliation.book_id)
            .where(
                or_(
                    BookAffiliation.similarity_token.op("@@")(tsq),
                    trgm_score >= 0,
                    Book.title.ilike(f"%{q}%")
                )
            )
            .order_by(desc(score))
            .limit(limit)
        )
        return session.exec(stmt).all()


search_class = Search()