import re

from pypdf import PdfReader

_WHITESPACE = re.compile(r"[ \t]+")
_BLANK_LINES = re.compile(r"\n{3,}")


def _clean(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\xa0", " ")
    text = _WHITESPACE.sub(" ", text)
    text = _BLANK_LINES.sub("\n\n", text)
    return "\n".join(line.strip() for line in text.splitlines()).strip()


class PDFParser:

    @staticmethod
    def extract_pages(file_path: str) -> list[dict]:
        """Return one entry per page: ``{"page_number": int, "text": str}``.

        Page numbers are 1-based so they line up with what a human sees. Pages
        with almost no extractable text (covers, scanned images) are dropped so
        they never become empty chunks.
        """
        reader = PdfReader(file_path)
        pages: list[dict] = []

        for index, page in enumerate(reader.pages, start=1):
            cleaned = _clean(page.extract_text() or "")

            if len(cleaned) < 20:
                continue

            pages.append({"page_number": index, "text": cleaned})

        return pages

    @staticmethod
    def extract_text(file_path: str) -> str:
        """Backwards-compatible flat extraction."""
        return "\n\n".join(page["text"] for page in PDFParser.extract_pages(file_path))
