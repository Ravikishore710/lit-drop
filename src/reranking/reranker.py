# Cross-Encoder Reranker Abstraction

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseReranker(ABC):
    @abstractmethod
    def rerank(
        self, query: str, candidates: List[Dict[str, Any]], top_n: int = 8
    ) -> List[Dict[str, Any]]:
        pass


class LocalCrossEncoderReranker(BaseReranker):
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: str = "cpu",
    ):
        self.model_name = model_name
        self.device = device
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(self.model_name, device=self.device)
            except Exception:
                self._model = "FALLBACK"
        return self._model

    def rerank(
        self, query: str, candidates: List[Dict[str, Any]], top_n: int = 8
    ) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        model = self._get_model()
        if model == "FALLBACK":
            # Fallback to fusion score or lexical overlap
            return sorted(
                candidates,
                key=lambda x: x.get("fusion_score", x.get("score", 0.0)),
                reverse=True,
            )[:top_n]

        pairs = [[query, c.get("text", "")] for c in candidates]
        scores = model.predict(pairs)

        ranked = []
        for c, score in zip(candidates, scores):
            item = dict(c)
            item["rerank_score"] = float(score)
            ranked.append(item)

        ranked.sort(key=lambda x: x["rerank_score"], reverse=True)
        return ranked[:top_n]
