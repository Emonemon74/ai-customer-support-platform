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
