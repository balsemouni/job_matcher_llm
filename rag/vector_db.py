import chromadb
import uuid
from rag.embeddings import embed_model, chunk_text
from config import CHROMA_PERSIST_DIR

try:
    chroma_client = chromadb.Client()
    cv_collection = chroma_client.get_collection("cv_chunks")
except:
    cv_collection = chroma_client.create_collection("cv_chunks")

def store_cv_in_vector_db(text):
    chunks = chunk_text(text)
    embeddings = embed_model.encode(chunks, convert_to_numpy=True).tolist()

    try:
        cv_collection.delete(where={})
    except:
        pass

    ids = [str(uuid.uuid4()) for _ in chunks]
    cv_collection.add(ids=ids, documents=chunks, embeddings=embeddings)
    return len(chunks)

def retrieve_relevant_context(query, k=5):
    q_emb = embed_model.encode([query], convert_to_numpy=True)[0]
    res = cv_collection.query(query_embeddings=[q_emb], n_results=k, include=["documents"])
    return "\n\n".join(res["documents"][0]) if res and res["documents"] else ""
