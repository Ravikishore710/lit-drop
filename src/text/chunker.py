# Hierarchical Semantic Text Chunker

from typing import List
from pydantic import BaseModel, Field

from src.common.types import ElementType
from src.parsing.models import CanonicalDocument, ElementObject


class TextChunk(BaseModel):
    chunk_id: str
    document_id: str
    parent_section_id: str = "GLOBAL"
    page_numbers: List[int] = Field(default_factory=list)
    element_ids: List[str] = Field(default_factory=list)
    text: str
    token_count: int


class HierarchicalChunker:
    def __init__(self, max_tokens: int = 400, overlap_tokens: int = 50):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens

    def chunk_document(self, doc: CanonicalDocument) -> List[TextChunk]:
        chunks: List[TextChunk] = []
        chunk_idx = 0

        # Group elements by parent section
        section_buckets = {}
        for elem in doc.elements:
            if elem.element_type in (
                ElementType.PARAGRAPH,
                ElementType.TITLE,
                ElementType.SECTION_HEADING,
                ElementType.LIST,
                ElementType.CAPTION,
            ):
                sec_id = elem.parent_section_id or "ROOT_SECTION"
                section_buckets.setdefault(sec_id, []).append(elem)

        for sec_id, elements in section_buckets.items():
            current_tokens = 0
            current_texts: List[str] = []
            current_pages: List[int] = []
            current_element_ids: List[str] = []

            for elem in elements:
                content = elem.normalized_content.strip()
                if not content:
                    continue

                words = content.split()
                elem_tokens = len(words)

                if current_tokens + elem_tokens > self.max_tokens and current_texts:
                    chunk_idx += 1
                    chunk_id = f"{doc.document_id}_CHK{chunk_idx:04d}"
                    chunks.append(
                        TextChunk(
                            chunk_id=chunk_id,
                            document_id=doc.document_id,
                            parent_section_id=sec_id,
                            page_numbers=sorted(list(set(current_pages))),
                            element_ids=list(current_element_ids),
                            text=" ".join(current_texts),
                            token_count=current_tokens,
                        )
                    )

                    # Preserve overlap
                    overlap_words = " ".join(current_texts).split()[-self.overlap_tokens:]
                    current_texts = [" ".join(overlap_words), content] if overlap_words else [content]
                    current_tokens = len(overlap_words) + elem_tokens
                    current_pages = [elem.page_number]
                    current_element_ids = [elem.element_id]
                else:
                    current_texts.append(content)
                    current_tokens += elem_tokens
                    current_pages.append(elem.page_number)
                    current_element_ids.append(elem.element_id)

            if current_texts:
                chunk_idx += 1
                chunk_id = f"{doc.document_id}_CHK{chunk_idx:04d}"
                chunks.append(
                    TextChunk(
                        chunk_id=chunk_id,
                        document_id=doc.document_id,
                        parent_section_id=sec_id,
                        page_numbers=sorted(list(set(current_pages))),
                        element_ids=list(current_element_ids),
                        text=" ".join(current_texts),
                        token_count=current_tokens,
                    )
                )

        return chunks
