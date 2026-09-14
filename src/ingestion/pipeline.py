# End-to-End Document Ingestion Pipeline

from pathlib import Path
from typing import Optional, Union

from src.common.logging import log_stage, logger
from src.common.types import ProcessingStatus
from src.config.settings import settings
from src.ingestion.extractor import DocumentExtractor
from src.ingestion.renderer import PageRenderer
from src.ingestion.validator import PDFValidator
from src.parsing.models import CanonicalDocument, DocumentMetadata
from src.parsing.serializer import CanonicalSerializer


class IngestionPipeline:
    def __init__(
        self,
        validator: Optional[PDFValidator] = None,
        renderer: Optional[PageRenderer] = None,
        extractor: Optional[DocumentExtractor] = None,
    ):
        self.validator = validator or PDFValidator()
        self.renderer = renderer or PageRenderer(dpi=settings.RENDER_DPI)
        self.extractor = extractor or DocumentExtractor(parser_version=settings.PARSER_VERSION)

    def process_pdf(
        self,
        pdf_path: Union[str, Path],
        source: str = "arxiv",
        source_url: Optional[str] = None,
        arxiv_id: Optional[str] = None,
        output_dir: Optional[Union[str, Path]] = None,
    ) -> CanonicalDocument:
        pdf_file = Path(pdf_path)
        out_dir = Path(output_dir or settings.CANONICAL_DIR)
        intermediate_dir = settings.INTERMEDIATE_DIR

        with log_stage("file_validation", filename=pdf_file.name):
            _, document_id, meta = self.validator.validate(pdf_file)

        with log_stage("page_rendering", document_id=document_id):
            pages = self.renderer.render_document(
                pdf_path=pdf_file,
                document_id=document_id,
                output_dir=intermediate_dir,
            )

        with log_stage("element_extraction", document_id=document_id):
            elements, relations = self.extractor.extract_document_elements(
                pdf_path=pdf_file,
                document_id=document_id,
                artifacts_dir=intermediate_dir,
            )

        # Build Document Metadata
        metadata = DocumentMetadata(
            document_id=document_id,
            source=source,
            source_url=source_url,
            title=str(meta.get("title", pdf_file.stem)),
            authors=[str(meta.get("author", ""))] if meta.get("author") else [],
            abstract="",
            publication_date=None,
            categories=[],
            doi=None,
            arxiv_id=arxiv_id,
            version=None,
            original_filename=pdf_file.name,
            file_sha256=str(meta["file_sha256"]),
            file_size_bytes=int(meta["file_size_bytes"]),
            page_count=int(meta["page_count"]),
            parser_version=settings.PARSER_VERSION,
            processing_status=ProcessingStatus.READY,
        )

        canonical_doc = CanonicalDocument(
            schema_version=settings.SCHEMA_VERSION,
            parser_version=settings.PARSER_VERSION,
            document_id=document_id,
            metadata=metadata,
            pages=pages,
            elements=elements,
            relations=relations,
        )

        with log_stage("canonical_serialization", document_id=document_id):
            CanonicalSerializer.serialize_document(canonical_doc, out_dir)

        return canonical_doc
