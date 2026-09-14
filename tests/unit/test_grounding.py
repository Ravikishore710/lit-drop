# Unit Tests for Grounding and Citation Verification

from src.common.types import GroundingStatus
from src.grounding.verifier import CitationMetadata, CitationVerifier, EvidenceBundler


def test_citation_verifier_found():
    verifier = CitationVerifier()
    source_map = {
        "SRC_01": CitationMetadata(
            source_id="SRC_01",
            document_id="DOC001",
            page_number=3,
            element_ids=["DOC001_P003_E001"],
            text_snippet="Model A achieves 94.2% accuracy.",
        )
    }

    raw_answer = "Model A achieved an accuracy of 94.2% [SRC_01]."
    grounded = verifier.verify_answer(raw_answer, source_map)

    assert grounded.status == GroundingStatus.FOUND
    assert len(grounded.citations) == 1
    assert grounded.citations[0].source_id == "SRC_01"
    assert grounded.confidence >= 0.90


def test_citation_verifier_hallucinated_removal():
    verifier = CitationVerifier()
    source_map = {
        "SRC_01": CitationMetadata(
            source_id="SRC_01",
            document_id="DOC001",
            page_number=1,
            text_snippet="Snippet",
        )
    }

    raw_answer = "Claims supported by [SRC_01] and fake source [SRC_99]."
    grounded = verifier.verify_answer(raw_answer, source_map)

    assert len(grounded.citations) == 1
    assert any("SRC_99" in note for note in grounded.notes)
