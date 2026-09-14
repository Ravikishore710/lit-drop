# Equation Subsystem and LaTeX Alignment

import re
from typing import Optional, Tuple
from pydantic import BaseModel


class EquationMetadata(BaseModel):
    equation_id: str
    page_number: int
    bounding_box: Tuple[float, float, float, float]
    equation_number: Optional[str] = None
    surrounding_text: Optional[str] = None
    latex_content: Optional[str] = None
    crop_image_path: Optional[str] = None


class EquationPipeline:
    NUMBER_PATTERN = re.compile(r"\((?:\d+(?:\.\d+)*|[a-zA-Z])\)\s*$")

    @classmethod
    def extract_equation_number(cls, raw_text: str) -> Optional[str]:
        match = cls.NUMBER_PATTERN.search(raw_text.strip())
        if match:
            return match.group(0).strip("() ")
        return None

    @staticmethod
    def format_latex_fallback(raw_text: str) -> str:
        clean = raw_text.strip()
        # Basic normalization of mathematical symbols
        clean = clean.replace("×", r"\times ").replace("±", r"\pm ")
        return f"$$ {clean} $$"
