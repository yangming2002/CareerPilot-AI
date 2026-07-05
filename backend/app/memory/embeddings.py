"""Embedding function for vector search. Uses sentence-transformers for zero-cost local embeddings."""
from functools import lru_cache

DIM = 512  # bge-small-zh-v1.5 dimension


@lru_cache(maxsize=1)
def _get_model():
    """Lazy-load the embedding model (downloaded once on first use)."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("BAAI/bge-small-zh-v1.5")


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Convert texts to embedding vectors."""
    model = _get_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return [e.tolist() for e in embeddings]


def embed_text(text: str) -> list[float]:
    """Convert a single text to embedding vector."""
    return embed_texts([text])[0]
