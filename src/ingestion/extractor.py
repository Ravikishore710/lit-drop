# Document Multimodal Layout and Element Extractor

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import fitz

from src.common.types import ElementType, RelationType
from src.parsing.models import ElementObject, RelationObject


class DocumentExtractor:
    HEADING_PATTERN = re.compile(
        r"^(?:\d+\.?\s+|[I|V|X]+\.?\s+|Abstract|Introduction|Related\s+Work|Methodology|Methods|Experiments|Results|Discussion|Conclusion|References)",
        re.IGNORECASE,
    )
    EQUATION_PATTERN = re.compile(r"\((?:\d+\.?\d*|[a-z])\)\s*$", re.IGNORECASE)
    TABLE_CAPTION_PATTERN = re.compile(r"^(?:Table|Tab\.)\s+\d+[:.]?", re.IGNORECASE)
    FIGURE_CAPTION_PATTERN = re.compile(r"^(?:Figure|Fig\.)\s+\d+[:.]?", re.IGNORECASE)
    CITATION_PATTERN = re.compile(r"\[(\d+(?:,\s*\d+)*)\]")

    def __init__(self, parser_version: str = "0.1.0"):
        self.parser_version = parser_version

    def extract_document_elements(
        self,
        pdf_path: Union[str, Path],
        document_id: str,
        artifacts_dir: Union[str, Path],
    ) -> Tuple[List[ElementObject], List[RelationObject]]:
        pdf_file = Path(pdf_path)
        art_base = Path(artifacts_dir) / document_id.replace("sha256:", "")
        crops_dir = art_base / "crops"
        crops_dir.mkdir(parents=True, exist_ok=True)

        elements: List[ElementObject] = []
        relations: List[RelationObject] = []

        doc = fitz.open(str(pdf_file))
        reading_order_counter = 0
        current_section_id: Optional[str] = None
        previous_elem_id: Optional[str] = None

        try:
            for page_idx in range(len(doc)):
                page_num = page_idx + 1
                page_id = f"{document_id}_P{page_num:03d}"
                page = doc[page_idx]

                relations.append(
                    RelationObject(
                        source_id=document_id,
                        target_id=page_id,
                        relation_type=RelationType.HAS_PAGE,
                    )
                )

                # Extract Text Blocks and Layout
                blocks = page.get_text("dict").get("blocks", [])
                for b_idx, block in enumerate(blocks):
                    reading_order_counter += 1
                    bbox = (
                        float(block["bbox"][0]),
                        float(block["bbox"][1]),
                        float(block["bbox"][2]),
                        float(block["bbox"][3]),
                    )

                    if block.get("type") == 0:
                        lines_text: List[str] = []
                        max_font_size = 0.0
                        for line in block.get("lines", []):
                            line_spans = [
                                span.get("text", "") for span in line.get("spans", [])
                            ]
                            for span in line.get("spans", []):
                                if span.get("size", 0.0) > max_font_size:
                                    max_font_size = span.get("size", 0.0)
                            lines_text.append(" ".join(line_spans).strip())

                        full_text = " ".join(lines_text).strip()
                        if not full_text:
                            continue

                        # Classify Element
                        elem_type = ElementType.PARAGRAPH
                        structured_data: Optional[Dict[str, Any]] = None

                        if page_num == 1 and reading_order_counter == 1 and max_font_size > 14:
                            elem_type = ElementType.TITLE
                        elif self.TABLE_CAPTION_PATTERN.match(full_text):
                            elem_type = ElementType.CAPTION
                        elif self.FIGURE_CAPTION_PATTERN.match(full_text):
                            elem_type = ElementType.CAPTION
                        elif self.HEADING_PATTERN.match(full_text) or (
                            max_font_size > 11.5 and len(full_text.split()) < 12
                        ):
                            elem_type = ElementType.SECTION_HEADING
                            current_section_id = (
                                f"{document_id}_SEC{reading_order_counter:03d}"
                            )
                            relations.append(
                                RelationObject(
                                    source_id=document_id,
                                    target_id=current_section_id,
                                    relation_type=RelationType.HAS_SECTION,
                                    metadata={"heading": full_text},
                                )
                            )
                        elif self.EQUATION_PATTERN.search(full_text) and len(full_text) < 150:
                            elem_type = ElementType.EQUATION

                        elem_id = f"{page_id}_E{b_idx:03d}"
                        element = ElementObject(
                            element_id=elem_id,
                            document_id=document_id,
                            page_id=page_id,
                            page_number=page_num,
                            element_type=elem_type,
                            bounding_box=bbox,
                            reading_order=reading_order_counter,
                            parent_section_id=current_section_id,
                            previous_element_id=previous_elem_id,
                            next_element_id=None,
                            normalized_content=full_text,
                            structured_data=structured_data,
                            extraction_confidence=0.95,
                            parser_version=self.parser_version,
                        )

                        if elements:
                            elements[-1].next_element_id = elem_id

                        elements.append(element)
                        previous_elem_id = elem_id

                        relations.append(
                            RelationObject(
                                source_id=document_id,
                                target_id=elem_id,
                                relation_type=RelationType.HAS_ELEMENT,
                            )
                        )

                        # Citations Check
                        citations = self.CITATION_PATTERN.findall(full_text)
                        for cite in citations:
                            relations.append(
                                RelationObject(
                                    source_id=elem_id,
                                    target_id=f"REF_{cite.strip()}",
                                    relation_type=RelationType.CITES,
                                    metadata={"text": cite},
                                )
                            )

                    elif block.get("type") == 1:
                        # Image / Figure Block
                        reading_order_counter += 1
                        elem_id = f"{page_id}_FIG{b_idx:03d}"
                        crop_path = crops_dir / f"{elem_id}.png"

                        try:
                            rect = fitz.Rect(*bbox)
                            pix = page.get_pixmap(clip=rect, alpha=False)
                            pix.save(str(crop_path))
                            raw_ref = str(crop_path.resolve())
                        except Exception:
                            raw_ref = None

                        element = ElementObject(
                            element_id=elem_id,
                            document_id=document_id,
                            page_id=page_id,
                            page_number=page_num,
                            element_type=ElementType.FIGURE,
                            bounding_box=bbox,
                            reading_order=reading_order_counter,
                            parent_section_id=current_section_id,
                            previous_element_id=previous_elem_id,
                            next_element_id=None,
                            raw_content_reference=raw_ref,
                            normalized_content=f"[Figure on Page {page_num}]",
                            extraction_confidence=0.90,
                            parser_version=self.parser_version,
                        )

                        if elements:
                            elements[-1].next_element_id = elem_id

                        elements.append(element)
                        previous_elem_id = elem_id

                        relations.append(
                            RelationObject(
                                source_id=document_id,
                                target_id=elem_id,
                                relation_type=RelationType.CONTAINS_FIGURE,
                            )
                        )

                # Extract Tables using PyMuPDF table finder
                tabs = page.find_tables()
                if tabs.tables:
                    for t_idx, tab in enumerate(tabs):
                        reading_order_counter += 1
                        t_bbox = (
                            float(tab.bbox[0]),
                            float(tab.bbox[1]),
                            float(tab.bbox[2]),
                            float(tab.bbox[3]),
                        )
                        t_elem_id = f"{page_id}_TAB{t_idx:03d}"
                        crop_path = crops_dir / f"{t_elem_id}.png"

                        try:
                            rect = fitz.Rect(*t_bbox)
                            pix = page.get_pixmap(clip=rect, alpha=False)
                            pix.save(str(crop_path))
                            raw_ref = str(crop_path.resolve())
                        except Exception:
                            raw_ref = None

                        extracted_df = tab.extract()
                        headers = [str(col or "") for col in extracted_df[0]] if extracted_df else []
                        rows = [
                            [str(cell or "") for cell in row]
                            for row in extracted_df[1:]
                        ] if len(extracted_df) > 1 else []

                        content_summary = f"Table with {len(headers)} columns and {len(rows)} rows: " + ", ".join(headers)

                        table_element = ElementObject(
                            element_id=t_elem_id,
                            document_id=document_id,
                            page_id=page_id,
                            page_number=page_num,
                            element_type=ElementType.TABLE,
                            bounding_box=t_bbox,
                            reading_order=reading_order_counter,
                            parent_section_id=current_section_id,
                            previous_element_id=previous_elem_id,
                            next_element_id=None,
                            raw_content_reference=raw_ref,
                            normalized_content=content_summary,
                            structured_data={"columns": headers, "rows": rows},
                            extraction_confidence=0.92,
                            parser_version=self.parser_version,
                        )

                        if elements:
                            elements[-1].next_element_id = t_elem_id

                        elements.append(table_element)
                        previous_elem_id = t_elem_id

                        relations.append(
                            RelationObject(
                                source_id=document_id,
                                target_id=t_elem_id,
                                relation_type=RelationType.CONTAINS_TABLE,
                            )
                        )
        finally:
            doc.close()

        return elements, relations
