# Canonical Document Data Models

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from src.common.types import (
    ElementType,
    ExtractionStatus,
    ProcessingStatus,
    RelationType,
)


class DocumentMetadata(BaseModel):
    document_id: str
    source: str = "arxiv"
    source_url: Optional[str] = None
    title: str = "Untitled Document"
    authors: List[str] = Field(default_factory=list)
    abstract: str = ""
    publication_date: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    version: Optional[str] = None
    original_filename: str
    file_sha256: str
    file_size_bytes: int
    page_count: int
    ingestion_timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    parser_version: str = "0.1.0"
    processing_status: ProcessingStatus = ProcessingStatus.UPLOADED


class PageObject(BaseModel):
    document_id: str
    page_id: str
    page_number: int
    width: float
    height: float
    dpi: int = 150
    rendered_image_path: str
    extraction_status: ExtractionStatus = ExtractionStatus.SUCCESS


class ElementObject(BaseModel):
    element_id: str
    document_id: str
    page_id: str
    page_number: int
    element_type: ElementType
    bounding_box: Tuple[float, float, float, float]
    reading_order: int
    parent_section_id: Optional[str] = None
    previous_element_id: Optional[str] = None
    next_element_id: Optional[str] = None
    raw_content_reference: Optional[str] = None
    normalized_content: str
    structured_data: Optional[Dict[str, Any]] = None
    extraction_confidence: float = 1.0
    parser_version: str = "0.1.0"


class RelationObject(BaseModel):
    source_id: str
    target_id: str
    relation_type: RelationType
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CanonicalDocument(BaseModel):
    schema_version: str = "1.0.0"
    parser_version: str = "0.1.0"
    document_id: str
    metadata: DocumentMetadata
    pages: List[PageObject] = Field(default_factory=list)
    elements: List[ElementObject] = Field(default_factory=list)
    relations: List[RelationObject] = Field(default_factory=list)
