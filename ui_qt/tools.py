from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional


class Tools:
    PAN = "pan"
    BRUSH = "brush"
    PEN = "pen"
    ARTBOARD = "artboard"


@dataclass
class ToolState:
    scale: float = 2.0
    origin: Tuple[float, float] = (100.0, 100.0)
    tool: str = Tools.PAN
    artboard: Tuple[float, float, float, float] = (0.0, 0.0, 256.0, 256.0)
    brush_color: str = "#000000"
    brush_size: float = 4.0
    strokes: List[List[Tuple[float, float]]] = field(default_factory=list)
    cur_stroke: Optional[List[Tuple[float, float]]] = None
    paths: List[List[Tuple[float, float]]] = field(default_factory=list)
    cur_path: Optional[List[Tuple[float, float]]] = None

    def screen_to_doc(self, x: float, y: float) -> Tuple[float, float]:
        ox, oy = self.origin
        s = self.scale
        return (x - ox) / s, (y - oy) / s

    def doc_to_screen(self, x: float, y: float) -> Tuple[float, float]:
        ox, oy = self.origin
        s = self.scale
        return ox + x * s, oy + y * s

