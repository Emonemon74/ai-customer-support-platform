from app.ai.parser import PDFParser
from app.ai.chunker import TextChunker
from app.ai.vector_store import VectorStore

text = PDFParser.extract_text(
    "uploads/c368f064-8242-405f-b43c-b4a8a432d4df.pdf"
)

print(text[:500])

chunks = TextChunker.chunk(text)

print(f"Total chunks: {len(chunks)}")

VectorStore().add_document(
    1,
    chunks,
)

print("Stored successfully.")