import pytest

from app.services.chunking import chunk_text


def test_short_text_is_one_chunk():
    assert chunk_text("Hello world.") == ["Hello world."]


def test_empty_text_gives_no_chunks():
    assert chunk_text("   \n\n  ") == []


def test_chunks_stay_close_to_size_limit():
    text = " ".join(f"Sentence number {i} is here." for i in range(200))
    chunks = chunk_text(text, size=300, overlap=50)
    assert len(chunks) > 1
    # a chunk may be a bit over because of the overlap added at the start
    assert all(len(chunk) <= 300 + 50 + 1 for chunk in chunks)


def test_chunks_overlap():
    text = "\n\n".join(f"Paragraph {i} " + "word " * 40 for i in range(6))
    chunks = chunk_text(text, size=300, overlap=60)
    last_words_of_first = chunks[0].split()[-3:]
    assert " ".join(last_words_of_first) in chunks[1]


def test_text_with_no_punctuation_is_still_split():
    chunks = chunk_text("word " * 1000, size=200, overlap=20)
    assert len(chunks) > 1


def test_overlap_must_be_smaller_than_size():
    with pytest.raises(ValueError):
        chunk_text("some text", size=100, overlap=100)
