from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Dict, Any


@dataclass
class ImageSolid:
    width: int
    height: int
    color_rgb: Tuple[int, int, int]


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    s = hex_color.lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) != 6:
        raise ValueError(f"invalid hex color: {hex_color}")
    r = int(s[0:2], 16)
    g = int(s[2:4], 16)
    b = int(s[4:6], 16)
    return r, g, b


def solid_color(params: Dict[str, Any]) -> ImageSolid:
    width = int(params.get("width", 64))
    height = int(params.get("height", 64))
    color = params.get("color", "#cccccc")
    rgb = hex_to_rgb(color)
    return ImageSolid(width=width, height=height, color_rgb=rgb)

