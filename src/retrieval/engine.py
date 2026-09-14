# Hybrid Multi-Channel Retrieval Engine with Reciprocal Rank Fusion (RRF)

import math
from typing import Any, Dict, List, Optional
from src.embeddings.provider import EmbeddingProvider
from src.vectorstore.qdrant import QdrantVectorStore


class BM25Retriever:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: List[Dict[str, Any]] = []
        self.doc_len: List[int] = []
        self.avg_doc_len = 0.0
        self.df: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}

    def index(self, documents: List[Dict[str, Any]]):
        self.corpus = documents
        total_len = 0
        self.df.clear()
        self.doc_len.clear()

        for doc in documents:
            tokens = doc.get("text", "").lower().split()
            self.doc_len.append(len(tokens))
            total_len += len(tokens)
            for token in set(tokens):
                self.df[token] = self.df.get(token, 0) + 1

        n_docs = max(1, len(documents))
        self.avg_doc_len = total_len / n_docs
        for token, freq in self.df.items():
            self.idf[token] = math.log((n_docs - freq + 0.5) / (freq + 0.5) + 1.0)

    def search(self, query: str, top_k: int = 30) -> List[Dict[str, Any]]:
        query_tokens = query.lower().split()
        scores = [0.0] * len(self.corpus)

        for token in query_tokens:
            if token not in self.idf:
                continue
            idf_val = self.idf[token]
            for idx, doc in enumerate(self.corpus):
                tokens = doc.get("text", "").lower().split()
                tf = tokens.count(token)
                if tf == 0:
                    continue
                num = tf * (self.k1 + 1.0)
                denom = tf + self.k1 * (1.0 - self.b + self.b * (self.doc_len[idx] / max(1.0, self.avg_doc_len)))
                scores[idx] += idf_val * (num / denom)

        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        results = []
        for idx in ranked_indices:
            if scores[idx] > 0.0:
                item = dict(self.corpus[idx])
                item["score"] = scores[idx]
                results.append(item)
        return results


def reciprocal_rank_fusion(
    ranked_lists: List[List[Dict[str, Any]]],
    key_field: str = "chunk_id",
    rrf_k: int = 60,
) -> List[Dict[str, Any]]:
    rrf_scores: Dict[str, float] = {}
    item_map: Dict[str, Dict[str, Any]] = {}

    for rank_list in ranked_lists:
        for rank, item in enumerate(rank_list, start=1):
            item_id = item.get(key_field, str(rank))
            item_map[item_id] = item
            rrf_scores[item_id] = rrf_scores.get(item_id, 0.0) + (1.0 / (rrf_k + rank))

    sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    fused_results = []
    for item_id in sorted_ids:
        merged = dict(item_map[item_id])
        merged["fusion_score"] = rrf_scores[item_id]
        fused_results.append(merged)
    return fused_results


class HybridRetrievalEngine:
    def __init__(
        self,
        vector_store: QdrantVectorStore,
        embedding_provider: EmbeddingProvider,
        dense_top_k: int = 30,
        lexical_top_k: int = 30,
    ):
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.bm25 = BM25Retriever()
        self.dense_top_k = dense_top_k
        self.lexical_top_k = lexical_top_k

    def index_documents(self, documents: List[Dict[str, Any]]):
        self.bm25.index(documents)

    def retrieve(
        self,
        query: str,
        filter_doc_id: Optional[str] = None,
        top_candidates: int = 50,
    ) -> List[Dict[str, Any]]:
        # 1. Dense Search
        query_vector = self.embedding_provider.embed_text(query)
        dense_results = self.vector_store.search(
            query_vector=query_vector,
            top_k=self.dense_top_k,
            filter_doc_id=filter_doc_id,
        )

        # 2. Lexical Search
        lexical_results = self.bm25.search(query=query, top_k=self.lexical_top_k)
        if filter_doc_id:
            lexical_results = [
                d for d in lexical_results if d.get("document_id") == filter_doc_id
            ]

        # 3. Reciprocal Rank Fusion
        fused = reciprocal_rank_fusion(
            [dense_results, lexical_results],
            key_field="chunk_id",
            rrf_k=60,
        )

        return fused[:top_candidates]
