import logging
import re

import numpy as np

from app import embedder, llm
from app.errors import AppError
from app.logger import log
from app.schemas import QueryResponse, Source

SNIPPET_LENGTH = 400
SENTENCES_IN_QUICK_ANSWER = 3
MIN_SCORE_VS_BEST = 0.85  # a sentence must score at least 85% of the best sentence's score


def build_answer(question, chunks):
    """Turn the retrieved chunks into an answer with numbered sources."""
    if not chunks:
        return QueryResponse(
            answer="You have no saved content yet. Add a note or a URL first.",
            mode="none",
            sources=[],
        )

    sources = [
        Source(
            number=number,
            item_id=chunk["item_id"],
            title=chunk["title"],
            source_url=chunk["source_url"],
            snippet=chunk["text"][:SNIPPET_LENGTH],
            score=round(chunk["score"], 4),
        )
        for number, chunk in enumerate(chunks, start=1)
    ]

    if llm.llm_is_configured():
        try:
            answer = llm.ask_llm(question, [chunk["text"] for chunk in chunks])
            return QueryResponse(answer=answer, mode="llm", sources=sources)
        except AppError as error:
            # The LLM is down or slow. The user still gets quoted sentences instead of an error.
            log("llm_failed_using_fallback", logging.WARNING, reason=error.message)

    return QueryResponse(answer=quote_best_sentences(question, chunks), mode="extractive", sources=sources)


def quote_best_sentences(question, chunks):
    """No LLM available: pick the sentences that best match the question and quote them.

    Every sentence is copied word for word from the saved content, so nothing is made up.
    """
    sentences = []  # (source number, sentence)
    for number, chunk in enumerate(chunks, start=1):
        for sentence in re.split(r"(?<=[.!?])\s+", chunk["text"]):
            sentence = sentence.strip()
            # skip very short fragments, and questions (web pages are full of
            # "Can't find what you're looking for?" which is not an answer)
            if len(sentence) > 20 and not sentence.endswith("?"):
                sentences.append((number, sentence))
    if not sentences:
        return "The closest match is in source [1]."

    vectors = embedder.embed([question] + [sentence for _, sentence in sentences])
    scores = vectors[1:] @ vectors[0]
    best = np.argsort(scores)[::-1][:SENTENCES_IN_QUICK_ANSWER]

    # Skip sentences that match the question much worse than the best one,
    # otherwise unrelated text sneaks into the answer.
    best = [index for index in best if scores[index] >= scores[best[0]] * MIN_SCORE_VS_BEST]
    best = sorted(best)  # keep them in the order they appear in the sources

    parts = []
    already_used = set()
    for index in best:
        number, sentence = sentences[index]
        if sentence not in already_used:  # chunk overlap can repeat a sentence
            already_used.add(sentence)
            parts.append(f"{sentence} [{number}]")
    return " ".join(parts)
