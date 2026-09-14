# LLM Orchestration and Provider Adapters

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import httpx

from src.common.logging import logger
from src.config.settings import settings


class BaseLLMAdapter(ABC):
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        top_p: float = 0.95,
        max_tokens: int = 2048,
    ) -> str:
        pass


class GeminiLLMAdapter(BaseLLMAdapter):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        self.model_name = model or settings.LLM_MODEL

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        top_p: float = 0.95,
        max_tokens: int = 2048,
    ) -> str:
        if not self.api_key:
            logger.warning("No Gemini API key provided. Using deterministic mock response.")
            return "Based on the retrieved evidence, the proposed methodology achieves superior empirical accuracy. [SRC_01]"

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_prompt if system_prompt else None,
            )
            config = genai.types.GenerationConfig(
                temperature=temperature,
                top_p=top_p,
                max_output_tokens=max_tokens,
            )
            response = model.generate_content(prompt, generation_config=config)
            return response.text.strip()
        except Exception as exc:
            logger.warning(f"Gemini generation unavailable ({exc}). Delegating to local runner / extractive synthesis.")
            return ""


class LocalQuantizedLLMAdapter(BaseLLMAdapter):
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.base_url = (base_url or settings.LOCAL_LLM_BASE_URL).rstrip("/")
        self.model = model or settings.LOCAL_LLM_MODEL

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        top_p: float = 0.95,
        max_tokens: int = 2048,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                res = client.post(f"{self.base_url}/chat/completions", json=payload)
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            logger.warning(f"Local LLM unreachable ({exc}).")
            return ""


from src.llm.local_runner import RAMSafeLocalRunner


class LLMOrchestrator:
    def __init__(self):
        self.gemini_adapter = GeminiLLMAdapter()
        self.local_adapter = LocalQuantizedLLMAdapter()
        self.safe_local_runner = RAMSafeLocalRunner()

    def _extractive_grounded_synthesis(self, query: str, evidence_bundle: str) -> str:
        """
        Synthesizes factual sentences directly from the retrieved evidence bundle,
        strictly tagging each extracted claim with its originating [SRC_XX] identifier.
        Guarantees ZERO dummy placeholders and full evidence grounding.
        """
        import re

        snippet_blocks = re.split(r"\[(SRC_\d{2})\]", evidence_bundle)
        if len(snippet_blocks) < 2:
            return "Based on the retrieved evidence, the provided document does not contain sufficient details to answer this query."

        query_tokens = set(re.findall(r"\b[A-Za-z0-9_]{3,}\b", query.lower()))
        stopwords = {
            "what", "which", "where", "when", "how", "does", "the", "and",
            "for", "with", "from", "that", "this", "are", "were", "been",
            "have", "has", "had", "show", "give", "tell", "explain", "about"
        }
        meaningful_q_tokens = {t for t in query_tokens if t not in stopwords}

        scored_sentences = []
        for i in range(1, len(snippet_blocks), 2):
            src_tag = snippet_blocks[i]
            src_content = snippet_blocks[i + 1] if i + 1 < len(snippet_blocks) else ""
            cleaned_content = re.sub(r"^\s*\([^)]+\):\s*", "", src_content).strip()

            raw_sentences = re.split(r"(?<=[.!?])\s+|\n+", cleaned_content)
            for s in raw_sentences:
                s_clean = s.strip()
                if len(s_clean) < 15:
                    continue
                s_tokens = set(re.findall(r"\b[A-Za-z0-9_]{3,}\b", s_clean.lower()))
                overlap = s_tokens.intersection(meaningful_q_tokens)
                score = len(overlap) * 2.0
                if any(term in query.lower() for term in ["value", "dimension", "rate", "hyperparameter", "size", "layer", "d_k", "d_v", "learning", "table"]):
                    if re.search(r"\d+(\.\d+)?", s_clean):
                        score += 2.0
                if score > 0:
                    scored_sentences.append((score, src_tag, s_clean))

        if not scored_sentences:
            return "Based on the retrieved evidence, the document does not contain explicit information directly answering this query."

        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        selected = []
        seen = set()
        for _, src_tag, sent in scored_sentences:
            if sent in seen:
                continue
            seen.add(sent)
            selected.append(f"{sent} [{src_tag}]")
            if len(selected) >= 3:
                break

        return " ".join(selected)

    def generate_grounded_answer(
        self,
        query: str,
        evidence_bundle: str,
        force_local: bool = False,
    ) -> str:
        system_prompt = (
            "You are a rigorous scientific document reasoning assistant. "
            "Answer the user query strictly and solely using the provided numbered evidence snippets. "
            "For every factual claim or measurement, append the exact source tag such as [SRC_01] or [SRC_02]. "
            "If the provided evidence does not contain sufficient information, state that clearly."
        )
        user_prompt = f"Query: {query}\n\nEvidence:\n{evidence_bundle}\n\nAnswer with inline citations:"

        if not force_local and self.gemini_adapter.api_key:
            ans = self.gemini_adapter.generate(user_prompt, system_prompt=system_prompt)
            if ans and len(ans) > 20 and "[SRC_" in ans:
                return ans

        # Fallback 1: Local server (Ollama/vLLM)
        if settings.LOCAL_LLM_ENABLED:
            try:
                ans = self.local_adapter.generate(user_prompt, system_prompt=system_prompt)
                if ans and "[SRC_" in ans:
                    return ans
            except Exception:
                pass

        # Fallback 2: Local compact CPU model (Qwen2.5-0.5B-Instruct)
        if self.safe_local_runner.can_safely_load():
            try:
                ans = self.safe_local_runner.generate(user_prompt, system_prompt=system_prompt)
                if ans and "[SRC_" in ans:
                    return ans
            except Exception as exc:
                logger.warning(f"Local Qwen generation exception: {exc}")

        # Fallback 3: Strict Extractive Grounded Synthesizer (Zero Hallucination, Zero Placeholders)
        return self._extractive_grounded_synthesis(query, evidence_bundle)

