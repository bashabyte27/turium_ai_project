import numpy as np

from app import embedder
from app.repositories import chunks as chunks_repo


def find_relevant_chunks(question, top_k):
    """Return the `top_k` saved chunks closest in meaning to the question, best first.

    Vectors are unit length, so a dot product gives the cosine similarity.
    We compare against every chunk (exact, simple). That is fine for thousands of
    chunks; for much more you would switch to a real vector index.
    """
    chunks, vectors = chunks_repo.load_chunks(embedder.model_name())
    if not chunks:
        return []

    question_vector = embedder.embed([question])[0]
    scores = vectors @ question_vector
    best_first = np.argsort(scores)[::-1][:top_k]

    results = []
    for index in best_first:
        chunk = dict(chunks[index])
        chunk["score"] = float(scores[index])
        results.append(chunk)
    return results
