# Page Rendering Pipeline

from pathlib import Path
from typing import List, Tuple, Union
import fitz

from src.common.exceptions import PDFParsingError
from src.common.types import ExtractionStatus
from src.parsing.models import PageObject


class PageRenderer:
    def __init__(self, dpi: int = 150):
        self.dpi = dpi
        self.zoom = dpi / 72.0
        self.matrix = fitz.Matrix(self.zoom, self.zoom)

    def render_document(
        self,
        pdf_path: Union[str, Path],
        document_id: str,
        output_dir: Union[str, Path],
    ) -> List[PageObject]:
        pdf_file = Path(pdf_path)
        out_base = Path(output_dir) / document_id.replace("sha256:", "") / "pages"
        out_base.mkdir(parents=True, exist_ok=True)

        pages: List[PageObject] = []

        try:
            doc = fitz.open(str(pdf_file))
        except Exception as exc:
            raise PDFParsingError(f"Failed opening PDF for rendering: {exc}")

        try:
            for page_index in range(len(doc)):
                page_num = page_index + 1
                page_id = f"{document_id}_P{page_num:03d}"
                page = doc[page_index]
                rect = page.rect

                img_filename = f"page_{page_num:03d}.png"
                img_path = out_base / img_filename

                pix = page.get_pixmap(matrix=self.matrix, alpha=False)
                pix.save(str(img_path))

                pages.append(
                    PageObject(
                        document_id=document_id,
                        page_id=page_id,
                        page_number=page_num,
                        width=float(rect.width),
                        height=float(rect.height),
                        dpi=self.dpi,
                        rendered_image_path=str(img_path.resolve()),
                        extraction_status=ExtractionStatus.SUCCESS,
                    )
                )
        finally:
            doc.close()

        return pages
