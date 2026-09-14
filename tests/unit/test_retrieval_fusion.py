# Unit Tests for Reciprocal Rank Fusion (RRF) and Retrieval

from src.retrieval.engine import reciprocal_rank_fusion


def test_reciprocal_rank_fusion():
    list_dense = [
        {"chunk_id": "CHK_01", "score": 0.9},
        {"chunk_id": "CHK_02", "score": 0.8},
        {"chunk_id": "CHK_03", "score": 0.7},
    ]
    list_lexical = [
        {"chunk_id": "CHK_02", "score": 12.5},
        {"chunk_id": "CHK_01", "score": 10.0},
        {"chunk_id": "CHK_04", "score": 8.0},
    ]

    fused = reciprocal_rank_fusion([list_dense, list_lexical], key_field="chunk_id", rrf_k=60)
    assert len(fused) == 4

    top_id = fused[0]["chunk_id"]
    # Both CHK_01 and CHK_02 appear at rank 1 and 2, so one of them must be top
    assert top_id in ("CHK_01", "CHK_02")
    assert "fusion_score" in fused[0]
    assert fused[0]["fusion_score"] > fused[-1]["fusion_score"]
