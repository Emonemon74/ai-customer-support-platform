import chromadb


client = chromadb.PersistentClient(path="chroma_db")

collection = client.get_or_create_collection(
    name="documents"
)


class VectorStore:
    def __init__(self):
        self.collection = collection

    def add_document(
        self,
        document_id: int,
        chunks: list[str],
        user_id: int,
        conversation_id: int,
        filename: str,
    ) -> None:
        ids = [
            f"user-{user_id}-doc-{document_id}-chunk-{index}"
            for index in range(len(chunks))
        ]

        metadatas = [
            {
                "document_id": document_id,
                "chunk_index": index,
                "user_id": user_id,
                "conversation_id": conversation_id,
                "filename": filename,
            }
            for index in range(len(chunks))
        ]

        self.collection.add(
            ids=ids,
            documents=chunks,
            metadatas=metadatas,
        )

    def store_chunks(
        self,
        document_id: int,
        chunks: list[str],
        user_id: int,
        conversation_id: int,
        filename: str,
    ) -> None:
        self.add_document(
            document_id=document_id,
            chunks=chunks,
            user_id=user_id,
            conversation_id=conversation_id,
            filename=filename,
        )

    def delete_document(self, document_id: int) -> None:
        ids = self.collection.get(
            where={"document_id": document_id}
        )["ids"]

        if ids:
            self.collection.delete(ids=ids)
