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
    ) -> Document:
        document = Document(
            filename=filename,
            file_type=file_type,
            file_path=file_path,
            uploaded_by=uploaded_by,
        )

        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        return document