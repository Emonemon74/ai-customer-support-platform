import chromadb

from app.ai.embeddings import generate_embeddings


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
    ) -> None:
        embeddings = generate_embeddings(chunks)

        ids = [
            f"{document_id}_{index}"
            for index in range(len(chunks))
        ]

        metadatas = [
            {
                "document_id": document_id,
                "chunk_index": index,
            }
            for index in range(len(chunks))
        ]

        self.collection.add(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )


def store_chunks(
    document_id: int,
    chunks: list[str],
) -> None:
    VectorStore().add_document(
        document_id=document_id,
        chunks=chunks,
    )