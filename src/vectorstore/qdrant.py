# Qdrant Vector Store Manager (HNSW + SQ8 Scalar Quantization)

from typing import Any, Dict, List, Optional
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from src.common.logging import logger
from src.config.settings import settings
from src.text.chunker import TextChunk


class QdrantVectorStore:
    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection_name: Optional[str] = None,
        vector_dim: int = 384,
        use_sq8: bool = True,
    ):
        self.collection_name = collection_name or settings.QDRANT_COLLECTION
        self.vector_dim = vector_dim
        self.use_sq8 = use_sq8

        target_url = url or settings.QDRANT_URL
        target_key = api_key or settings.QDRANT_API_KEY

        try:
            self.client = QdrantClient(url=target_url, api_key=target_key or None, timeout=5.0)
            self.client.get_collections()
        except Exception:
            logger.info("Remote Qdrant unavailable. Initializing lightweight local embedded Qdrant.")
            self.client = QdrantClient(location=":memory:")

        self._ensure_collection()

    def _ensure_collection(self):
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            quantization_config = (
                qmodels.ScalarQuantization(
                    scalar=qmodels.ScalarQuantizationConfig(
                        type=qmodels.ScalarType.INT8,
                        quantile=0.99,
                        always_ram=True,
                    )
                )
                if self.use_sq8
                else None
            )

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qmodels.VectorParams(
                    size=self.vector_dim,
                    distance=qmodels.Distance.COSINE,
                    hnsw_config=qmodels.HnswConfigDiff(
                        m=settings.HNSW_M,
                        ef_construct=settings.HNSW_EF_CONSTRUCT,
                    ),
                    quantization_config=quantization_config,
                ),
            )
            logger.info(f"Created Qdrant collection '{self.collection_name}' (dim={self.vector_dim}, SQ8={self.use_sq8})")

    def index_chunks(
        self, chunks: List[TextChunk], embeddings: List[List[float]]
    ) -> int:
        if not chunks:
            return 0

        points: List[qmodels.PointStruct] = []
        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            point_id = abs(hash(chunk.chunk_id)) % (2**63 - 1)
            payload = {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "parent_section_id": chunk.parent_section_id,
                "page_numbers": chunk.page_numbers,
                "element_ids": chunk.element_ids,
                "text": chunk.text,
                "token_count": chunk.token_count,
            }
            points.append(
                qmodels.PointStruct(id=point_id, vector=emb, payload=payload)
            )

        self.client.upsert(collection_name=self.collection_name, points=points)
        logger.info(f"Indexed {len(points)} chunks into Qdrant collection '{self.collection_name}'")
        return len(points)

    def search(
        self,
        query_vector: List[float],
        top_k: int = 30,
        filter_doc_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query_filter = None
        if filter_doc_id:
            query_filter = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="document_id",
                        match=qmodels.MatchValue(value=filter_doc_id),
                    )
                ]
            )

        if hasattr(self.client, "query_points"):
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=query_filter,
                limit=top_k,
            )
            points = response.points
        else:
            points = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=top_k,
            )

        hits = []
        for r in points:
            hit = dict(r.payload or {})
            hit["score"] = float(r.score)
            hits.append(hit)
        return hits
