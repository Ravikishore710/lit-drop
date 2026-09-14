# Figure Subsystem and Visual Metadata

from typing import Optional, Tuple
from pydantic import BaseModel


class FigureMetadata(BaseModel):
    figure_id: str
    page_number: int
    bounding_box: Tuple[float, float, float, float]
    caption: Optional[str] = None
    surrounding_text: Optional[str] = None
    image_crop_path: Optional[str] = None
    visual_description: Optional[str] = None


class FigurePipeline:
    @staticmethod
    def associate_caption_heuristic(figure_bbox: Tuple[float, float, float, float], caption_candidates: list) -> Optional[str]:
        """
        Associates the closest text block below the figure as its caption.
        """
        _, _, _, fig_y1 = figure_bbox
        closest_caption = None
        min_dist = float("inf")

        for cand in caption_candidates:
            cand_y0 = cand.get("bounding_box", [0, 0, 0, 0])[1]
            if cand_y0 >= fig_y1 - 10:
                dist = cand_y0 - fig_y1
                if dist < min_dist:
                    min_dist = dist
                    closest_caption = cand.get("normalized_content")

        return closest_caption
