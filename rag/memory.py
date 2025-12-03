import uuid
from rag.embeddings import embed_model
import chromadb

try:
    # Tries to load an existing collection called "memory".This is where all chat memory will be stored as embeddings.
    memory_client = chromadb.Client()
    memory_collection = memory_client.get_collection("memory")
except:
    memory_collection = memory_client.create_collection("memory")

def store_memory(user, ai):
    text = f"USER: {user}\nAI: {ai}"
    emb = embed_model.encode([text], convert_to_numpy=True)[0]
    memory_collection.add(ids=[str(uuid.uuid4())], documents=[text], embeddings=[emb])

def retrieve_memory(prompt, k=3):
    q_emb = embed_model.encode([prompt], convert_to_numpy=True)[0]
    res = memory_collection.query(query_embeddings=[q_emb], n_results=k, include=["documents"])
    return "\n".join(res["documents"][0]) if res["documents"] else ""
