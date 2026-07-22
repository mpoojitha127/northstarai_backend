"""
Goal Memory: semantic retrieval over past decisions and messages.

Each user gets their own Chroma collection (namespaced by user_id) so
retrieval never leaks across accounts. We store short text chunks
("On {date}, decided X because Y") rather than raw message dumps, since
that's what the alignment engine actually needs at query time: prior
decisions and milestones relevant to the current request, not full chat logs.
"""
import chromadb
from chromadb.utils import embedding_functions

from app.core.config import settings

_client: chromadb.ClientAPI | None = None
_default_ef = embedding_functions.DefaultEmbeddingFunction()


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    return _client


def _collection_name(user_id: str) -> str:
    return f"user_{user_id}_memory"


def get_collection(user_id: str):
    client = _get_client()
    return client.get_or_create_collection(
        name=_collection_name(user_id), embedding_function=_default_ef
    )


def add_memory(user_id: str, memory_id: str, text: str, metadata: dict) -> None:
    collection = get_collection(user_id)
    collection.upsert(ids=[memory_id], documents=[text], metadatas=[metadata])


def query_memory(user_id: str, query_text: str, n_results: int = 5) -> list[dict]:
    collection = get_collection(user_id)
    if collection.count() == 0:
        return []
    n_results = min(n_results, collection.count())
    results = collection.query(query_texts=[query_text], n_results=n_results)

    memories = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    for doc, meta in zip(docs, metas):
        memories.append({"text": doc, "metadata": meta})
    return memories
