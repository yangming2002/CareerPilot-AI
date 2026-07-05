"""Embedding function for vector search. Uses Bailian API to avoid local model downloads."""
from functools import lru_cache

from openai import OpenAI

from app.core.config import OPENAI_API_KEY, OPENAI_BASE_URL

DIM = 1536  # text-embedding-v2 dimension


@lru_cache(maxsize=1)
def _get_client() -> OpenAI:
    return OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Convert texts to embedding vectors via Bailian embedding API."""
    client = _get_client()
    resp = client.embeddings.create(
        model="text-embedding-v2",
        input=texts,
    )
    return [d.embedding for d in resp.data]


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]
