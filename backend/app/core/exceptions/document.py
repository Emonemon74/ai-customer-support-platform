class UnsupportedFileTypeError(Exception):
    def __init__(self, message: str = "Unsupported file type"):
        self.message = message
        super().__init__(self.message)


class FileTooLargeError(Exception):
    def __init__(self, message: str = "File size exceeds 10 MB"):
        self.message = message
        super().__init__(self.message)


class DuplicateDocumentError(Exception):
    def __init__(self, message: str = "This document has already been uploaded to this conversation"):
        self.message = message
        super().__init__(self.message)


class NoReadableTextError(Exception):
    """The PDF parsed but yielded no text to index (scanned or image-only)."""

    def __init__(
        self,
        message: str = (
            "No readable text found. This PDF looks like a scanned image or "
            "screenshot. Upload a text-based PDF (one where you can select the text)."
        ),
    ):
        self.message = message
        super().__init__(self.message)
