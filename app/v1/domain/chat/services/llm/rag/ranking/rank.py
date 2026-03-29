from sqlmodel import Session, cast, Float, select, asc, desc, func, or_
from app.v1.domain.chat.services.llm.rag.sim.vector import embedding_sim
from app.v1.domain.chat.services.llm.rag.sim.fts_trgm import search_class
from app.v1.common.models.book_tables import BookChunk, BookSimilarity, BookAffiliation


class Ranking:

    def __init__(self):
        self.search = search_class


    def _set_ids(self, session: Session, ask_em: list[float], keywords: str, limit: int):
        top_ids = set()
        vector = embedding_sim(session, ask_em, limit=limit)
        fts_trgm = self.search.fts_trgm_search(session, keywords, limit=limit)
        for (t, n, d), (book, score) in zip(vector, fts_trgm):
            top_ids.add(n)
            top_ids.add(book.id)
        return list(top_ids)


    def get_ranked_chunk(
            self,
            session: Session,
            ask_em: list[float],
            keywords: str,
            limit: int,
            k: int = 60,
            w_vec: float = 1.0,
            w_fts: float = 1.0,
    ):

        vec_results = embedding_sim(session, ask_em, limit=limit)
        vec_rank = {row.book_ids: i + 1 for i, row in enumerate(vec_results)}


        fts_results = self.search.fts_trgm_search(session, keywords, limit=limit)
        fts_rank = {row.id: i + 1 for i, row in enumerate(fts_results)}


        all_ids = set(vec_rank) | set(fts_rank)
        scores = {}
        for bid in all_ids:
            s = 0.0
            if bid in vec_rank:
                s += w_vec * (1.0 / (k + vec_rank[bid]))
            if bid in fts_rank:
                s += w_fts * (1.0 / (k + fts_rank[bid]))
            scores[bid] = s

        fused = sorted(all_ids, key=lambda x: scores[x], reverse=True)


        stmt = select(BookChunk.id, BookChunk.chunk).where(BookChunk.id.in_(fused))
        result = session.exec(stmt).all()
        m = {bid: text for bid, text in result}
        return [f"[id] {bid}\n" + m[bid] for bid in fused if bid in m]


ranking_class = Ranking()