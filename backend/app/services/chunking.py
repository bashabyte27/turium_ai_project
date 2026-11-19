"""How we split text into chunks.

1. Split on blank lines, so paragraphs stay together when they fit.
2. A paragraph that is too long is split into sentences.
3. Pieces are packed together until a chunk is about `size` characters.
4. Each chunk (except the first) starts with the end of the previous chunk
   (`overlap` characters), so an idea that crosses a boundary can still be found.

800 characters is roughly a short paragraph or two: small enough for precise
search, big enough to keep the surrounding context.
"""
import re


def split_long_paragraph(paragraph, size):
    pieces = []
    for sentence in re.split(r"(?<=[.!?])\s+", paragraph):
        # a "sentence" with no punctuation can still be too long, so cut it by words
        while len(sentence) > size:
            cut = sentence.rfind(" ", 0, size)
            if cut <= 0:
                cut = size
            pieces.append(sentence[:cut].strip())
            sentence = sentence[cut:].strip()
        if sentence:
            pieces.append(sentence)
    return pieces


def end_of(text, overlap):
    """The last `overlap` characters of text, starting at a word boundary."""
    if overlap <= 0:
        return ""
    if len(text) <= overlap:
        return text
    tail = text[-overlap:]
    first_space = tail.find(" ")
    return tail[first_space + 1:] if first_space != -1 else tail


def chunk_text(text, size=800, overlap=100):
    if overlap >= size:
        raise ValueError("overlap must be smaller than the chunk size")

    pieces = []
    for paragraph in re.split(r"\n\s*\n", text.strip()):
        paragraph = " ".join(paragraph.split())
        if not paragraph:
            continue
        if len(paragraph) <= size:
            pieces.append(paragraph)
        else:
            pieces.extend(split_long_paragraph(paragraph, size))

    # pack pieces together without going over the size
    groups = []
    current = ""
    for piece in pieces:
        if current and len(current) + 1 + len(piece) > size:
            groups.append(current)
            current = piece
        else:
            current = (current + " " + piece).strip()
    if current:
        groups.append(current)

    # add the overlap from the previous group
    chunks = []
    for index, group in enumerate(groups):
        if index == 0:
            chunks.append(group)
        else:
            chunks.append((end_of(groups[index - 1], overlap) + " " + group).strip())
    return chunks
