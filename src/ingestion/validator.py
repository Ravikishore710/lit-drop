# PDF File Validation and Integrity Verification

from pathlib import Path
from typing import Dict, Optional, Tuple, Union
import fitz

from src.common.exceptions import FileValidationError
from src.common.hashing import compute_file_sha256, format_document_id


class PDFValidator:
    def __init__(
        self,
        min_pages: int = 1,
        max_pages: int = 200,
        max_file_size_bytes: int = 100 * 1024 * 1024,
    ):
        self.min_pages = min_pages
        self.max_pages = max_pages
        self.max_file_size_bytes = max_file_size_bytes

    def validate(
        self, file_path: Union[str, Path]
    ) -> Tuple[bool, str, Dict[str, Union[str, int, bool]]]:
        path = Path(file_path)
        if not path.exists():
            raise FileValidationError(f"File does not exist: {path}")

        file_size = path.stat().st_size
        if file_size == 0:
            raise FileValidationError(f"File is empty: {path}")
        if file_size > self.max_file_size_bytes:
            raise FileValidationError(
                f"File exceeds maximum allowed size ({file_size} > {self.max_file_size_bytes} bytes)"
            )

        with open(path, "rb") as f:
            header = f.read(5)
            if not header.startswith(b"%PDF-"):
                raise FileValidationError(f"Invalid PDF magic header: {header!r}")

        sha256_hex = compute_file_sha256(path)
        document_id = format_document_id(sha256_hex)

        try:
            doc = fitz.open(str(path))
        except Exception as exc:
            raise FileValidationError(f"Corrupted PDF cannot be opened: {exc}")

        try:
            if doc.is_encrypted:
                raise FileValidationError("PDF is password-encrypted and cannot be processed")

            page_count = len(doc)
            if page_count < self.min_pages:
                raise FileValidationError(
                    f"PDF has fewer than {self.min_pages} pages (found {page_count})"
                )
            if page_count > self.max_pages:
                raise FileValidationError(
                    f"PDF exceeds {self.max_pages} pages (found {page_count})"
                )

            metadata = {
                "file_sha256": sha256_hex,
                "document_id": document_id,
                "file_size_bytes": file_size,
                "page_count": page_count,
                "is_encrypted": False,
                "format": doc.metadata.get("format", "PDF"),
                "title": doc.metadata.get("title", "").strip() or path.stem,
                "author": doc.metadata.get("author", "").strip(),
            }
        finally:
            doc.close()

        return True, document_id, metadata
