import hashlib
import re

import numpy as np

from app.config import settings

DIMENSIONS = 384
_local_model = None


def model_name():
    return f"{settings.embedding_provider}:{settings.embedding_model}"


def embed(texts):
    """Turn a list of texts into a 2D array of unit-length vectors (one row per text)."""
    if settings.embedding_provider == "hash":
        vectors = _hash_embed(texts)
    else:
        vectors = _local_embed(texts)
    lengths = np.linalg.norm(vectors, axis=1, keepdims=True)
    return (vectors / np.maximum(lengths, 1e-12)).astype(np.float32)


def _local_embed(texts):
    global _local_model
    if _local_model is None:
        # imported here because it is slow to load and not needed for tests
        from fastembed import TextEmbedding

        _local_model = TextEmbedding(model_name=settings.embedding_model)
    return np.array(list(_local_model.embed(texts)), dtype=np.float32)


def _hash_embed(texts):
    """Offline fallback: counts words into fixed buckets. Matches on words, not meaning."""
    vectors = np.zeros((len(texts), DIMENSIONS), dtype=np.float32)
    for row, text in enumerate(texts):
        for word in re.findall(r"[a-z0-9]+", text.lower()):
            bucket = int(hashlib.md5(word.encode()).hexdigest(), 16) % DIMENSIONS
            vectors[row, bucket] += 1
    return vectors
