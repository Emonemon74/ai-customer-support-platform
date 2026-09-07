"""Recursive, page-aware text chunking.

The old chunker sliced the whole document every ``chunk_size`` characters with
no regard for structure, so a chunk could begin mid-sentence and span a page
break. This version splits each page independently, preferring natural
boundaries (paragraph -> line -> sentence -> word) and only falling back to a
hard character cut when a single fragment is still too long. Every chunk keeps
its source page number and an index.
"""

import hashlib

_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def _split_recursive(text: str, chunk_size: int, separators: list[str]) -> list[str]:
    separator = separators[0]
    remaining = separators[1:]

    if separator == "":
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    pieces = text.split(separator)
    out: list[str] = []

    for piece in pieces:
        if len(piece) <= chunk_size:
            out.append(piece)
        else:
            out.extend(_split_recursive(piece, chunk_size, remaining))

    return [p for p in out if p]


def _merge(pieces: list[str], chunk_size: int, overlap: int) -> list[str]:
    chunks: list[str] = []
    current = ""

    for piece in pieces:
        candidate = f"{current} {piece}".strip() if current else piece

        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)
            tail = current[-overlap:] if overlap else ""
            current = f"{tail} {piece}".strip()
        else:
            chunks.append(piece)
            current = ""

    if current:
        chunks.append(current)

    return chunks


class TextChunker:

    @staticmethod
    def chunk(text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
        """Flat chunking of a single string (kept for callers that don't have
        page structure)."""
        pieces = _split_recursive(text, chunk_size, _SEPARATORS)
        return _merge(pieces, chunk_size, overlap)

    @staticmethod
    def chunk_pages(
        pages: list[dict],
        chunk_size: int = 800,
        overlap: int = 120,
    ) -> list[dict]:
        """Chunk ``[{"page_number", "text"}]`` into structured chunks.

        Returns ``[{"text", "page_number", "chunk_index"}]`` with noisy and
        duplicate fragments removed. ``chunk_index`` is document-global.
        """
        results: list[dict] = []
        seen: set[str] = set()

        for page in pages:
            for raw in TextChunker.chunk(page["text"], chunk_size, overlap):
                text = raw.strip()

                if len(text) < 40:
                    continue

                fingerprint = hashlib.md5(
                    " ".join(text.lower().split()).encode()
                ).hexdigest()
                if fingerprint in seen:
                    continue
                seen.add(fingerprint)

                results.append(
                    {
                        "text": text,
                        "page_number": page["page_number"],
                        "chunk_index": len(results),
                    }
                )

        return results
