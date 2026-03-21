from chunking import get_chunks
from app.local_test_version.db.schemas import BookChunk, Books, BookVector
from FlagEmbedding import BGEM3FlagModel
from sqlmodel import Session, select
from app.local_test_version.db.session import engine

m3 = BGEM3FlagModel("BAAI/bge-m3")
chunks, ids = get_chunks(Session(engine))
out = m3.encode(chunks, batch_size=12, max_length=4096)
dense = out['dense_vecs']

with Session(engine) as session:
    book_ids = session.exec(select(Books.id).order_by(Books.id)).all()
    book_ids = list(book_ids)

    for bid, text, emb in zip(ids, chunks, dense):
        bc = session.exec(select(BookChunk).where(BookChunk.Books_id == bid)).first()
        if bc is None:
            session.add(BookChunk(Books_id=bid, chunk_text=text))
        else:
            bc.chunk_text = text

        bv = session.exec(select(BookVector).where(BookVector.Books_id == bid)).first()
        emb_list = emb.tolist()
        if bv is None:
            session.add(BookVector(Books_id=bid, embedding=emb_list))
        else:
            bv.embedding = emb_list

    session.commit()