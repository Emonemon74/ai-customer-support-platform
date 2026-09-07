import chromadb

client = chromadb.PersistentClient(path="chroma_db")

collection = client.get_or_create_collection(name="documents")


def _normalise(chunks: list) -> list[dict]:
    """Accept either ``list[str]`` (legacy) or ``list[{text, page_number,
    chunk_index}]`` and return the structured form."""
    normalised: list[dict] = []

    for index, chunk in enumerate(chunks):
        if isinstance(chunk, str):
            normalised.append(
                {"text": chunk, "page_number": None, "chunk_index": index}
            )
        else:
            normalised.append(
                {
                    "text": chunk["text"],
                    "page_number": chunk.get("page_number"),
                    "chunk_index": chunk.get("chunk_index", index),
                }
            )

    return normalised


class VectorStore:
    def __init__(self):
        self.collection = collection

    def add_document(
        self,
        document_id: int,
        chunks: list,
        user_id: int,
        conversation_id: int,
        filename: str,
    ) -> None:
        structured = _normalise(chunks)
        if not structured:
            return

        document_id = int(document_id)
        user_id = int(user_id)
        conversation_id = int(conversation_id)

        ids = [f"u{user_id}-d{document_id}-c{c['chunk_index']}" for c in structured]

        metadatas = [
            {
                "document_id": document_id,
                "chunk_index": c["chunk_index"],
                "page_number": c["page_number"] if c["page_number"] is not None else -1,
                "user_id": user_id,
                "conversation_id": conversation_id,
                "filename": filename,
            }
            for c in structured
        ]

        self.collection.add(
            ids=ids,
            documents=[c["text"] for c in structured],
            metadatas=metadatas,
        )

    # Retained for older call sites.
    def store_chunks(self, document_id, chunks, user_id, conversation_id, filename):
        self.add_document(document_id, chunks, user_id, conversation_id, filename)

    def delete_document(self, document_id: int, user_id: int | None = None) -> None:
        where: dict = {"document_id": int(document_id)}

        if user_id is not None:
            where = {
                "$and": [
                    {"document_id": int(document_id)},
                    {"user_id": int(user_id)},
                ]
            }

        ids = self.collection.get(where=where)["ids"]

        if ids:
            self.collection.delete(ids=ids)
