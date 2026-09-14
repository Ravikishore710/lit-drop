# Unit Tests for Hierarchical Semantic Chunker

from src.common.types import ElementType
from src.parsing.models import CanonicalDocument, DocumentMetadata, ElementObject
from src.text.chunker import HierarchicalChunker


def test_hierarchical_chunker():
    doc_id = "sha256:" + "b" * 64
    elements = [
        ElementObject(
            element_id=f"{doc_id}_E001",
            document_id=doc_id,
            page_id=f"{doc_id}_P001",
            page_number=1,
            element_type=ElementType.SECTION_HEADING,
            bounding_box=(50.0, 50.0, 200.0, 70.0),
            reading_order=1,
            parent_section_id="SEC_01",
            normalized_content="1. Introduction",
        ),
        ElementObject(
            element_id=f"{doc_id}_E002",
            document_id=doc_id,
            page_id=f"{doc_id}_P001",
            page_number=1,
            element_type=ElementType.PARAGRAPH,
            bounding_box=(50.0, 80.0, 500.0, 200.0),
            reading_order=2,
            parent_section_id="SEC_01",
            normalized_content="Scientific document intelligence requires processing complex multimodal signals including text, charts, tables, and equations.",
        ),
    ]

    canonical_doc = CanonicalDocument(
        document_id=doc_id,
        metadata=DocumentMetadata(
            document_id=doc_id,
            original_filename="sample.pdf",
            file_sha256="b" * 64,
            file_size_bytes=1024,
            page_count=1,
        ),
        elements=elements,
    )

    chunker = HierarchicalChunker(max_tokens=100)
    chunks = chunker.chunk_document(canonical_doc)

    assert len(chunks) == 1
    assert chunks[0].document_id == doc_id
    assert "Scientific document intelligence" in chunks[0].text
    assert chunks[0].parent_section_id == "SEC_01"
    assert chunks[0].page_numbers == [1]
