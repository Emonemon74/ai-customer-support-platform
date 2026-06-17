class UnsupportedFileTypeError(Exception):
    def __init__(self, message: str = "Unsupported file type"):
        self.message = message
        super().__init__(self.message)


class FileTooLargeError(Exception):
    def __init__(self, message: str = "File size exceeds 10 MB"):
        self.message = message
        super().__init__(self.message)