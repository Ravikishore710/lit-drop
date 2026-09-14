# Evidence Grounding and Citation Verification System

import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from src.common.types import GroundingStatus


class CitationMetadata(BaseModel):
    source_id: str
    document_id: str
    page_number: int
    parent_section_id: Optional[str] = None
    element_ids: List[str] = Field(default_factory=list)
    text_snippet: str = ""


class GroundedAnswer(BaseModel):
    answer: str
    status: GroundingStatus
    confidence: float
    citations: List[CitationMetadata] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class EvidenceBundler:
    @staticmethod
    def build_evidence_bundle(candidates: List[Dict[str, Any]]) -> Tuple[str, Dict[str, CitationMetadata]]:
        evidence_lines = []
        source_map: Dict[str, CitationMetadata] = {}

        for idx, item in enumerate(candidates, start=1):
            src_id = f"SRC_{idx:02d}"
            pages = item.get("page_numbers", [1])
            page_num = pages[0] if pages else 1
            meta = CitationMetadata(
                source_id=src_id,
                document_id=item.get("document_id", "UNKNOWN"),
                page_number=page_num,
                parent_section_id=item.get("parent_section_id"),
                element_ids=item.get("element_ids", []),
                text_snippet=item.get("text", "")[:200],
            )
            source_map[src_id] = meta
            evidence_lines.append(f"[{src_id}] (Doc: {meta.document_id}, Page: {meta.page_number}):\n{item.get('text', '')}\n")

        bundle_text = "\n".join(evidence_lines)
        return bundle_text, source_map


class CitationVerifier:
    CITATION_REGEX = re.compile(r"\[(SRC_\d{2})\]")

    def verify_answer(
        self,
        raw_answer: str,
        valid_sources: Dict[str, CitationMetadata],
        status_override: Optional[GroundingStatus] = None,
    ) -> GroundedAnswer:
        found_tags = set(self.CITATION_REGEX.findall(raw_answer))
        verified_citations: List[CitationMetadata] = []
        invalid_tags = []

        for tag in found_tags:
            if tag in valid_sources:
                verified_citations.append(valid_sources[tag])
            else:
                invalid_tags.append(tag)

        notes: List[str] = []
        if invalid_tags:
            notes.append(f"Removed ungrounded/hallucinated citation IDs: {invalid_tags}")

        # Determine Support Status
        if status_override:
            final_status = status_override
        elif not valid_sources:
            final_status = GroundingStatus.NOT_FOUND
        elif len(verified_citations) > 0:
            final_status = GroundingStatus.FOUND
        else:
            final_status = GroundingStatus.INFERRED
            notes.append("Answer contains substantive claims without direct citation anchors.")

        confidence = 0.95 if final_status == GroundingStatus.FOUND else 0.60

        return GroundedAnswer(
            answer=raw_answer,
            status=final_status,
            confidence=confidence,
            citations=verified_citations,
            notes=notes,
        )
