# Unit Tests for Hashing and Identifiers

from src.common.hashing import compute_bytes_sha256, format_document_id


def test_compute_bytes_sha256():
    sample = b"Scientific Multimodal Document Intelligence System"
    digest = compute_bytes_sha256(sample)
    assert len(digest) == 64
    assert isinstance(digest, str)


def test_format_document_id():
    digest = "a" * 64
    doc_id = format_document_id(digest)
    assert doc_id == f"sha256:{'a' * 64}"

    # Verify idempotency if already prefixed
    doc_id_prefixed = format_document_id(f"sha256:{digest}")
    assert doc_id_prefixed == f"sha256:{'a' * 64}"
