# Integration Tests for Qdrant Vector Store with SQ8 Quantization

from src.text.chunker import TextChunk
from src.vectorstore.qdrant import QdrantVectorStore


def test_qdrant_indexing_and_search():
    store = QdrantVectorStore(collection_name="test_col_integration", vector_dim=4, use_sq8=True)

    chunks = [
        TextChunk(
            chunk_id="CHK_001",
            document_id="DOC_001",
            text="Attention is a mechanism connecting encoder and decoder.",
            token_count=10,
        ),
        TextChunk(
            chunk_id="CHK_002",
            document_id="DOC_002",
            text="Residual connections allow training of substantially deeper neural networks.",
            token_count=10,
        ),
    ]

    embeddings = [
        [0.5, 0.5, 0.5, 0.5],
        [-0.5, -0.5, -0.5, -0.5],
    ]

    count = store.index_chunks(chunks, embeddings)
    assert count == 2

    # Query with positive vector
    hits = store.search(query_vector=[0.5, 0.5, 0.5, 0.5], top_k=2)
    assert len(hits) == 2
    assert hits[0]["chunk_id"] == "CHK_001"
    assert hits[0]["score"] > hits[1]["score"]
