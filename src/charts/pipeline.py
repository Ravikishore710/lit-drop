# Chart Visual Reasoning and ChartQA Evaluation Metrics

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChartData(BaseModel):
    title: Optional[str] = None
    x_axis_label: Optional[str] = None
    y_axis_label: Optional[str] = None
    series_names: List[str] = Field(default_factory=list)
    data_points: List[Dict[str, Any]] = Field(default_factory=list)


class ChartPipeline:
    @staticmethod
    def compute_relaxed_accuracy(pred_answer: str, gold_answer: str, tolerance: float = 0.05) -> bool:
        """
        Official ChartQA Relaxed Accuracy:
        - If numbers: considered correct if within 5% tolerance.
        - If text: exact match after normalization.
        """
        pred_clean = pred_answer.strip().lower()
        gold_clean = gold_answer.strip().lower()

        if pred_clean == gold_clean:
            return True

        # Extract numerical values
        num_pattern = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")
        pred_nums = num_pattern.findall(pred_clean)
        gold_nums = num_pattern.findall(gold_clean)

        if pred_nums and gold_nums:
            try:
                p_val = float(pred_nums[0])
                g_val = float(gold_nums[0])
                if g_val == 0.0:
                    return abs(p_val) <= 1e-4
                error = abs(p_val - g_val) / abs(g_val)
                return error <= tolerance
            except ValueError:
                pass

        return False
