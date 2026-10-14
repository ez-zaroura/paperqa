import pytest
from src.ingest import chunk_text


def test_chunks_are_not_longer_than_size():
    chunks = chunk_text("a" * 2000, size=800, overlap=150)
    assert all(len(c) <= 800 for c in chunks)


def test_consecutive_chunks_overlap():
    text = "".join(str(i % 10) for i in range(2000))
    chunks = chunk_text(text, size=800, overlap=150)
    assert chunks[0][-150:] == chunks[1][:150]


def test_empty_text_gives_no_chunks():
    assert chunk_text("") == []


def test_overlap_too_large_raises_error():
    with pytest.raises(ValueError):
        chunk_text("abc", size=100, overlap=100)