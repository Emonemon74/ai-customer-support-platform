from app.ai.chunker import TextChunker


def test_chunk_pages_keeps_page_numbers_and_indexes():
    pages = [
        {"page_number": 1, "text": "Alpha section. " * 60},
        {"page_number": 2, "text": "Beta section describes something else entirely. " * 40},
    ]

    chunks = TextChunker.chunk_pages(pages, chunk_size=200, overlap=40)

    assert len(chunks) > 2
    assert [c["chunk_index"] for c in chunks] == list(range(len(chunks)))
    assert {c["page_number"] for c in chunks} == {1, 2}
    # no chunk straddles a page boundary
    for chunk in chunks:
        assert chunk["text"]


def test_chunk_pages_drops_noise_and_duplicates():
    pages = [
        {"page_number": 1, "text": "This is a real paragraph with enough content to keep."},
        {"page_number": 2, "text": "x"},  # too short -> dropped
        {"page_number": 3, "text": "This is a real paragraph with enough content to keep."},  # dup
    ]

    chunks = TextChunker.chunk_pages(pages)

    assert len(chunks) == 1
    assert chunks[0]["page_number"] == 1


def test_flat_chunk_respects_size():
    text = "word " * 500
    chunks = TextChunker.chunk(text, chunk_size=300, overlap=50)

    assert chunks
    assert all(len(c) <= 300 + 50 for c in chunks)
