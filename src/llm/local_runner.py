# RAM-Safe Local LLM Runner with Hardware Guard

import os
from typing import Optional
import psutil

from src.common.logging import logger
from src.config.settings import settings


class RAMSafeLocalRunner:
    """
    Hardware-aware local model executor.
    Monitors host physical memory before model loading to prevent OS thrashing or OOM freezes.
    """

    MIN_REQUIRED_RAM_MB = 350

    def __init__(self, model_name: str = "HuggingFaceTB/SmolLM-135M-Instruct"):
        self.model_name = model_name
        self._model = None
        self._tokenizer = None

    @classmethod
    def get_available_ram_mb(cls) -> int:
        return int(psutil.virtual_memory().available / (1024 * 1024))

    def can_safely_load(self) -> bool:
        free_mb = self.get_available_ram_mb()
        logger.info(f"Host memory check: {free_mb} MB available (Minimum required: {self.MIN_REQUIRED_RAM_MB} MB)")
        return free_mb >= self.MIN_REQUIRED_RAM_MB

    def load_model(self) -> bool:
        if not self.can_safely_load():
            logger.warning(
                f"Insufficient host RAM ({self.get_available_ram_mb()} MB < {self.MIN_REQUIRED_RAM_MB} MB). "
                "Local model load prevented to maintain system stability. Offloading to Gemini Cloud API."
            )
            return False

        if self._model is None:
            try:
                import torch
                from transformers import AutoModelForCausalLM, AutoTokenizer

                logger.info(f"Loading compact local model '{self.model_name}' into CPU memory with float32/int8...")
                self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self._model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float32,
                    low_cpu_mem_usage=True,
                )
                self._model.eval()
                logger.info("Compact local model successfully loaded.")
                return True
            except Exception as exc:
                logger.warning(f"Could not load local model '{self.model_name}': {exc}. Using cloud or API fallback.")
                return False
        return True

    def generate(self, prompt: str, max_new_tokens: int = 128) -> str:
        if self._model is None:
            if not self.load_model():
                return ""

        try:
            inputs = self._tokenizer(prompt, return_tensors="pt")
            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,
                    temperature=0.2,
                )
            decoded = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
            return decoded.replace(prompt, "").strip()
        except Exception as exc:
            logger.error(f"Local inference failure: {exc}")
            return ""
