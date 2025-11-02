from __future__ import annotations

import json
import sys
import tkinter as tk
from pathlib import Path
from typing import Optional, Tuple, List

from node_engine.simple_eval import solid_color, ImageSolid


class Tools:
    PAN = "pan"
    BRUSH = "brush"
    PEN = "pen"
    ARTBOARD = "artboard"


class CanvasView(tk.Canvas):
    def __init__(self, master: tk.Misc, **kwargs):
        super().__init__(master, background="#222", highlightthickness=0, **kwargs)
        self.scale_factor: float = 2.0  # pixels per document unit
        self.origin: Tuple[float, float] = (100.0, 100.0)  # pan offset
        self._drag_start: Optional[Tuple[int, int]] = None
        self._doc_image: Optional[ImageSolid] = None

        # Tool state
        self.current_tool: str = Tools.PAN
        self._space_pan: bool = False
        self.artboard: Tuple[float, float, float, float] = (0.0, 0.0, 256.0, 256.0)  # x,y,w,h in doc units
        self._artboard_start: Optional[Tuple[float, float]] = None
        self.brush_color: str = "#000000"
        self.brush_size: float = 4.0
        self.strokes: List[List[Tuple[float, float]]] = []  # list of polylines in doc coords
        self._cur_stroke: Optional[List[Tuple[float, float]]] = None
        self.paths: List[List[Tuple[float, float]]] = []
        self._cur_path: Optional[List[Tuple[float, float]]] = None

        # Bind events
        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        # Windows: <MouseWheel>, Linux: <Button-4/5>, macOS delta reversed
        self.bind("<MouseWheel>", self._on_wheel)
        self.bind("<Button-4>", lambda e: self._zoom(1.1, e.x, e.y))
        self.bind("<Button-5>", lambda e: self._zoom(0.9, e.x, e.y))
        # Keyboard for tool switching
        self.bind_all("<KeyPress>", self._on_key)

    # Coordinate transforms
    def screen_to_doc(self, x: float, y: float) -> Tuple[float, float]:
        ox, oy = self.origin
        s = self.scale_factor
        return (x - ox) / s, (y - oy) / s

    def doc_to_screen(self, x: float, y: float) -> Tuple[float, float]:
        ox, oy = self.origin
        s = self.scale_factor
        return ox + x * s, oy + y * s

    def set_tool(self, tool: str):
        self.current_tool = tool
        self._cur_path = None
        self._cur_stroke = None
        self.redraw()

    def load_image(self, img: ImageSolid) -> None:
        self._doc_image = img
        # Fit artboard to image by default
        self.artboard = (0.0, 0.0, float(img.width), float(img.height))
        self.redraw()

    def _on_key(self, event):
        k = event.keysym.lower()
        if k == "space":
            self._space_pan = True if event.type == "2" else False  # 2: KeyPress, 3: KeyRelease
            self.current_tool = Tools.PAN if self._space_pan else self.current_tool
        elif k == "b":
            self.set_tool(Tools.BRUSH)
        elif k == "p":
            self.set_tool(Tools.PEN)
        elif k == "a":
            self.set_tool(Tools.ARTBOARD)
        elif k == "v":
            self.set_tool(Tools.PAN)
        elif k in ("return", "escape") and self._cur_path:
            # finish current pen path
            self.paths.append(self._cur_path)
            self._cur_path = None
            self.redraw()

    def _on_press(self, event):
        self._drag_start = (event.x, event.y)
        if self.current_tool == Tools.PAN or self._space_pan:
            return
        dx, dy = self.screen_to_doc(event.x, event.y)
        if self.current_tool == Tools.ARTBOARD:
            self._artboard_start = (dx, dy)
        elif self.current_tool == Tools.BRUSH:
            self._cur_stroke = [(dx, dy)]
        elif self.current_tool == Tools.PEN:
            if self._cur_path is None:
                self._cur_path = []
            self._cur_path.append((dx, dy))
        self.redraw()

    def _on_drag(self, event):
        if self._drag_start is None:
            return
        if self.current_tool == Tools.PAN or self._space_pan:
            dx = event.x - self._drag_start[0]
            dy = event.y - self._drag_start[1]
            ox, oy = self.origin
            self.origin = (ox + dx, oy + dy)
            self._drag_start = (event.x, event.y)
        elif self.current_tool == Tools.ARTBOARD and self._artboard_start:
            x0, y0 = self._artboard_start
            x1, y1 = self.screen_to_doc(event.x, event.y)
            w = max(1.0, x1 - x0)
            h = max(1.0, y1 - y0)
            self.artboard = (x0, y0, w, h)
        elif self.current_tool == Tools.BRUSH and self._cur_stroke is not None:
            dx, dy = self.screen_to_doc(event.x, event.y)
            self._cur_stroke.append((dx, dy))
        self.redraw()

    def _on_release(self, event):
        if self.current_tool == Tools.BRUSH and self._cur_stroke is not None:
            self.strokes.append(self._cur_stroke)
            self._cur_stroke = None
        self._artboard_start = None
        self._drag_start = None
        self.redraw()

    def _on_wheel(self, event):
        # On Windows, event.delta is typically +/-120
        factor = 1.1 if event.delta > 0 else 0.9
        self._zoom(factor, event.x, event.y)

    def _zoom(self, factor: float, cx: int, cy: int):
        old = self.scale_factor
        new = max(0.2, min(20.0, old * factor))
        if abs(new - old) < 1e-6:
            return
        # Zoom towards cursor: adjust origin so document space under cursor stays fixed
        ox, oy = self.origin
        # Convert screen->doc coords before change
        dx = (cx - ox) / old
        dy = (cy - oy) / old
        self.scale_factor = new
        # Recompute origin to keep (dx,dy) under cursor
        self.origin = (cx - dx * new, cy - dy * new)
        self.redraw()

    def redraw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1 or h <= 1:
            return

        # Checkerboard background
        self._draw_checkerboard(w, h, tile=16)

        # Artboard
        ax, ay, aw, ah = self.artboard
        ax0, ay0 = self.doc_to_screen(ax, ay)
        ax1, ay1 = self.doc_to_screen(ax + aw, ay + ah)
        self.create_rectangle(ax0, ay0, ax1, ay1, outline="#888", width=1, dash=(4, 2))

        if self._doc_image:
            img = self._doc_image
            sx = self.scale_factor
            ox, oy = self.origin
            x0 = ox
            y0 = oy
            x1 = ox + img.width * sx
            y1 = oy + img.height * sx
            fill = "#%02x%02x%02x" % img.color_rgb
            self.create_rectangle(x0, y0, x1, y1, fill=fill, outline="#000000")
            self.create_rectangle(x0, y0, x1, y1, outline="#333333", width=1)

        # Brush strokes (polylines)
        self._draw_strokes()
        # Pen paths
        self._draw_paths()

    def _draw_checkerboard(self, w: int, h: int, tile: int = 16):
        size = max(4, int(tile * (self.scale_factor / 2.0)))
        # 80% and 90% gray tones
        c1 = "#CCCCCC"
        c2 = "#E5E5E5"
        for y in range(0, h, size):
            for x in range(0, w, size):
                color = c1 if ((x // size) + (y // size)) % 2 == 0 else c2
                self.create_rectangle(x, y, x + size, y + size, outline=color, fill=color)

    def _draw_strokes(self):
        if not self.strokes and not self._cur_stroke:
            return
        s = self.scale_factor
        w = max(1, int(self.brush_size * s))
        for stroke in self.strokes + ([self._cur_stroke] if self._cur_stroke else []):
            if not stroke or len(stroke) < 2:
                continue
            pts: List[float] = []
            for (dx, dy) in stroke:
                x, y = self.doc_to_screen(dx, dy)
                pts.extend([x, y])
            self.create_line(*pts, fill=self.brush_color, width=w, capstyle=tk.ROUND, joinstyle=tk.ROUND, smooth=True)

    def _draw_paths(self):
        if not self.paths and not self._cur_path:
            return
        paths = self.paths + ([self._cur_path] if self._cur_path else [])
        for idx, path in enumerate(paths):
            if not path or len(path) < 2:
                continue
            pts: List[float] = []
            for (dx, dy) in path:
                x, y = self.doc_to_screen(dx, dy)
                pts.extend([x, y])
            color = "#00d1ff" if path is self._cur_path else "#ffaa00"
            self.create_line(*pts, fill=color, width=2, capstyle=tk.ROUND, joinstyle=tk.ROUND)


def load_vxdoc_solid(path: Path) -> ImageSolid:
    # Minimal: find the first node of type solid_color in nodes/*.json
    nodes_dir = path / "nodes"
    for p in sorted(nodes_dir.glob("*.json")):
        try:
            node = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if node.get("type") == "solid_color":
            return solid_color(node.get("params", {}))
    # Fallback
    return solid_color({"width": 128, "height": 128, "color": "#66aaff"})


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    doc_path = Path(argv[0]) if argv else Path("examples/basic.vxdoc")
    root = tk.Tk()
    root.title(f"PicaDeli (scaffold) — {doc_path}")
    root.geometry("1000x700")

    # Toolbar
    toolbar = tk.Frame(root)
    toolbar.pack(side=tk.TOP, fill=tk.X)

    status = tk.StringVar(value=f"Tool: {Tools.PAN} • LMB: action • Space: pan • Wheel: zoom")

    def set_tool(tool: str):
        canvas.set_tool(tool)
        status.set(f"Tool: {tool} • LMB: action • Space: pan • Wheel: zoom")

    tk.Button(toolbar, text="Pan (V)", command=lambda: set_tool(Tools.PAN)).pack(side=tk.LEFT)
    tk.Button(toolbar, text="Brush (B)", command=lambda: set_tool(Tools.BRUSH)).pack(side=tk.LEFT)
    tk.Button(toolbar, text="Pen (P)", command=lambda: set_tool(Tools.PEN)).pack(side=tk.LEFT)
    tk.Button(toolbar, text="Artboard (A)", command=lambda: set_tool(Tools.ARTBOARD)).pack(side=tk.LEFT)

    canvas = CanvasView(root)
    canvas.pack(fill=tk.BOTH, expand=True)
    try:
        img = load_vxdoc_solid(doc_path)
    except Exception as exc:
        tk.messagebox.showerror("Load Error", str(exc))
        return 1
    canvas.load_image(img)

    # Simple status bar
    bar = tk.Label(root, textvariable=status, anchor="w")
    bar.pack(fill=tk.X)

    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
