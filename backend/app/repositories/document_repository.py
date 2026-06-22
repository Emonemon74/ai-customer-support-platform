from sqlalchemy.orm import Session

from app.models.document import Document


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        filename: str,
        file_type: str,
        file_path: str,
        uploaded_by: int,
        conversation_id: int,
    ) -> Document:
        document = Document(
            filename=filename,
            file_type=file_type,
            file_path=file_path,
            uploaded_by=uploaded_by,
            conversation_id=conversation_id,
        )

        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        return document

    def get_by_conversation(self, user_id: int, conversation_id: int) -> list[Document]:
        return (
            self.db.query(Document)
            .filter(Document.uploaded_by == user_id)
            .filter(Document.conversation_id == conversation_id)
            .all()
        )

    def get_all_by_conversation(self, conversation_id: int) -> list[Document]:
        return (
            self.db.query(Document)
            .filter(Document.conversation_id == conversation_id)
            .all()
        )

    def get_by_id(self, document_id: int) -> Document | None:
        return (
            self.db.query(Document)
            .filter(Document.id == document_id)
            .first()
        )

    def update_status(self, document: Document, status: str) -> Document:
        document.status = status

        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        return document

    def delete(self, document: Document) -> None:
        self.db.delete(document)
        self.db.commit()
