# Scientific Table Extraction Pipeline and GriTS Evaluation Metrics

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class TableStructure(BaseModel):
    columns: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)
    caption: Optional[str] = None
    bbox: Optional[Tuple[float, float, float, float]] = None


class TablePipeline:
    @staticmethod
    def to_markdown(table: TableStructure) -> str:
        if not table.columns and not table.rows:
            return ""

        cols = table.columns if table.columns else [f"Col {i+1}" for i in range(len(table.rows[0]))]
        header_line = "| " + " | ".join(cols) + " |"
        sep_line = "| " + " | ".join(["---"] * len(cols)) + " |"
        row_lines = [
            "| " + " | ".join(str(cell) for cell in row) + " |"
            for row in table.rows
        ]
        return "\n".join([header_line, sep_line] + row_lines)

    @staticmethod
    def compute_grits(pred_rows: List[List[str]], gold_rows: List[List[str]]) -> Dict[str, float]:
        """
        GriTS (Grid Table Similarity) metric for PubTables-1M evaluation.
        Computes cell-level precision, recall, and F1 over cell matrices.
        """
        pred_cells = set()
        for r_idx, row in enumerate(pred_rows):
            for c_idx, val in enumerate(row):
                pred_cells.add((r_idx, c_idx, str(val).strip().lower()))

        gold_cells = set()
        for r_idx, row in enumerate(gold_rows):
            for c_idx, val in enumerate(row):
                gold_cells.add((r_idx, c_idx, str(val).strip().lower()))

        if not gold_cells and not pred_cells:
            return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
        if not gold_cells or not pred_cells:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

        matches = len(pred_cells.intersection(gold_cells))
        precision = matches / len(pred_cells) if pred_cells else 0.0
        recall = matches / len(gold_cells) if gold_cells else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }
