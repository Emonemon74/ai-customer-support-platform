class TextChunker:

    @staticmethod
    def chunk(
        text: str,
        chunk_size: int = 800,
        overlap: int = 100,
    ) -> list[str]:

        chunks = []

        start = 0

        while start < len(text):

            end = start + chunk_size

            chunks.append(
                text[start:end]
            )

            start = end - overlap

        return chunks