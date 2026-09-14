# Embedding Provider Abstraction

from abc import ABC, abstractmethod
from typing import List, Optional, Union
import numpy as np


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        pass

    @abstractmethod
    def embed_image(self, image_path: str) -> Optional[List[float]]:
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        pass


class LocalSentenceTransformerProvider(EmbeddingProvider):
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._model = None
        self._dim = 384

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name, device=self.device)
                self._dim = self._model.get_sentence_embedding_dimension()
            except Exception:
                self._model = "MOCK"
        return self._model

    def embed_text(self, text: str) -> List[float]:
        model = self._get_model()
        if model == "MOCK":
            np.random.seed(abs(hash(text)) % (2**32))
            vec = np.random.normal(0, 1, self._dim)
            return (vec / np.linalg.norm(vec)).tolist()
        emb = model.encode(text, normalize_embeddings=True)
        return emb.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        model = self._get_model()
        if model == "MOCK":
            return [self.embed_text(t) for t in texts]
        embs = model.encode(texts, normalize_embeddings=True)
        return embs.tolist()

    def embed_image(self, image_path: str) -> Optional[List[float]]:
        return None

    @property
    def dimension(self) -> int:
        return self._dim
