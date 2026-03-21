from FlagEmbedding import BGEM3FlagModel

m3 = BGEM3FlagModel("BAAI/bge-m3")

def query_embedding(user_q):
    out = m3.encode(user_q, batch_size=12, max_length=4096)
    dense = out['dense_vecs']
    return dense