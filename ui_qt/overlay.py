from __future__ import annotations

from PySide6 import QtWidgets, QtGui, QtCore
from typing import Optional, Tuple, List

from .tools import ToolState, Tools


class CanvasOverlay(QtWidgets.QWidget):
    """Transparent overlay that captures input and draws tool visuals.

    Sits on top of a rendering widget (e.g., WgpuCanvas).
    """

    tool_changed = QtCore.Signal(str)
    settings_changed = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget, state: ToolState):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.state = state
        self._drag_start: Optional[Tuple[int, int]] = None
        self._artboard_start: Optional[Tuple[float, float]] = None
        self._space_pan: bool = False
        self.auto_fit: bool = True

    def resizeEvent(self, ev: QtGui.QResizeEvent) -> None:
        super().resizeEvent(ev)
        if self.auto_fit:
            self.fit_to_view()
        self.update()

    def fit_to_view(self, padding: int = 24) -> None:
        # Fit the artboard to the overlay rect, centered, with padding
        rect = self.rect()
        if rect.width() <= 0 or rect.height() <= 0:
            return
        ax, ay, aw, ah = self.state.artboard
        if aw <= 0 or ah <= 0:
            return
        sx = (rect.width() - 2 * padding) / aw
        sy = (rect.height() - 2 * padding) / ah
        s = max(0.1, min(sx, sy))
        cx = rect.width() * 0.5
        cy = rect.height() * 0.5
        # Center artboard
        self.state.scale = s
        self.state.origin = (
            cx - (ax + aw * 0.5) * s,
            cy - (ay + ah * 0.5) * s,
        )

    # Input handling
    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        self._drag_start = (ev.position().x(), ev.position().y())
        # User interaction disables auto-fit
        self.auto_fit = False
        if self.state.tool == Tools.PAN or self._space_pan:
            self._set_cursor(QtCore.Qt.CursorShape.ClosedHandCursor)
            return
        dx, dy = self.state.screen_to_doc(ev.position().x(), ev.position().y())
        if self.state.tool == Tools.ARTBOARD:
            self._artboard_start = (dx, dy)
        elif self.state.tool == Tools.BRUSH:
            self.state.cur_stroke = [(dx, dy)]
        elif self.state.tool == Tools.PEN:
            if self.state.cur_path is None:
                self.state.cur_path = []
            self.state.cur_path.append((dx, dy))
        self.update()

    def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
        if self._drag_start is None:
            return
        if self.state.tool == Tools.PAN or self._space_pan:
            dx = ev.position().x() - self._drag_start[0]
            dy = ev.position().y() - self._drag_start[1]
            ox, oy = self.state.origin
            self.state.origin = (ox + dx, oy + dy)
            self._drag_start = (ev.position().x(), ev.position().y())
        elif self.state.tool == Tools.ARTBOARD and self._artboard_start:
            x0, y0 = self._artboard_start
            x1, y1 = self.state.screen_to_doc(ev.position().x(), ev.position().y())
            w = max(1.0, x1 - x0)
            h = max(1.0, y1 - y0)
            self.state.artboard = (x0, y0, w, h)
        elif self.state.tool == Tools.BRUSH and self.state.cur_stroke is not None:
            dx, dy = self.state.screen_to_doc(ev.position().x(), ev.position().y())
            self.state.cur_stroke.append((dx, dy))
        self.update()

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
        if self.state.tool == Tools.BRUSH and self.state.cur_stroke is not None:
            self.state.strokes.append(self.state.cur_stroke)
            self.state.cur_stroke = None
        self._artboard_start = None
        self._drag_start = None
        # Restore cursor after panning
        if self.state.tool == Tools.PAN and not self._space_pan:
            self._apply_cursor()
        # Notify settings might have changed (e.g., artboard resize)
        try:
            self.settings_changed.emit()
        except Exception:
            pass
        self.update()

    def wheelEvent(self, ev: QtGui.QWheelEvent) -> None:
        delta = ev.angleDelta().y()
        self.auto_fit = False
        factor = 1.1 if delta > 0 else 0.9
        self._zoom(factor, ev.position().x(), ev.position().y())

    def keyPressEvent(self, ev: QtGui.QKeyEvent) -> None:
        k = ev.key()
        if k == QtCore.Qt.Key.Key_Space:
            self._space_pan = True
            self._set_cursor(QtCore.Qt.CursorShape.OpenHandCursor)
        elif k == QtCore.Qt.Key.Key_B:
            self.set_tool(Tools.BRUSH)
        elif k == QtCore.Qt.Key.Key_P:
            self.set_tool(Tools.PEN)
        elif k == QtCore.Qt.Key.Key_A:
            self.set_tool(Tools.ARTBOARD)
        elif k == QtCore.Qt.Key.Key_V:
            self.set_tool(Tools.PAN)
        elif k in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter, QtCore.Qt.Key.Key_Escape):
            if self.state.cur_path:
                self.state.paths.append(self.state.cur_path)
                self.state.cur_path = None
        self.update()

    def keyReleaseEvent(self, ev: QtGui.QKeyEvent) -> None:
        if ev.key() == QtCore.Qt.Key.Key_Space:
            self._space_pan = False
            self._apply_cursor()

    def set_tool(self, tool: str):
        self.state.tool = tool
        self.state.cur_path = None
        self.state.cur_stroke = None
        self._apply_cursor()
        try:
            self.tool_changed.emit(tool)
        except Exception:
            pass
        self.update()

    def _apply_cursor(self):
        # Map tool to cursor icon
        if self.state.tool == Tools.PAN:
            self._set_cursor(QtCore.Qt.CursorShape.OpenHandCursor)
        elif self.state.tool == Tools.BRUSH:
            self._set_cursor(QtCore.Qt.CursorShape.CrossCursor)
        elif self.state.tool == Tools.PEN:
            self._set_cursor(QtCore.Qt.CursorShape.CrossCursor)
        elif self.state.tool == Tools.ARTBOARD:
            self._set_cursor(QtCore.Qt.CursorShape.CrossCursor)

    def _set_cursor(self, cursor: QtCore.Qt.CursorShape):
        try:
            self.setCursor(QtGui.QCursor(cursor))
        except Exception:
            pass

    def _zoom(self, factor: float, cx: float, cy: float):
        old = self.state.scale
        new = max(0.2, min(20.0, old * factor))
        if abs(new - old) < 1e-6:
            return
        ox, oy = self.state.origin
        dx = (cx - ox) / old
        dy = (cy - oy) / old
        self.state.scale = new
        self.state.origin = (cx - dx * new, cy - dy * new)

        self.update()

    # Painting helpers
    def paintEvent(self, ev: QtGui.QPaintEvent) -> None:
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

        self._draw_checker(p)
        self._draw_artboard(p)
        self._draw_strokes(p)
        self._draw_paths(p)
        p.end()

    def _draw_checker(self, p: QtGui.QPainter, tile: int = 16):
        s = max(4, int(tile * (self.state.scale / 2.0)))
        # 80% gray (highlights) and 90% gray (dark zones) per request
        c_light = QtGui.QColor("#CCCCCC")  # 80%
        c_dark = QtGui.QColor("#E5E5E5")   # ~90%
        rect = self.rect()
        for y in range(0, rect.height(), s):
            for x in range(0, rect.width(), s):
                p.fillRect(x, y, s, s, c_light if ((x // s) + (y // s)) % 2 == 0 else c_dark)

    def _draw_artboard(self, p: QtGui.QPainter):
        ax, ay, aw, ah = self.state.artboard
        x0, y0 = self.state.doc_to_screen(ax, ay)
        x1, y1 = self.state.doc_to_screen(ax + aw, ay + ah)
        pen = QtGui.QPen(QtGui.QColor("#888"))
        pen.setStyle(QtCore.Qt.PenStyle.DashLine)
        p.setPen(pen)
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        p.drawRect(QtCore.QRectF(x0, y0, x1 - x0, y1 - y0))

    def _draw_strokes(self, p: QtGui.QPainter):
        all_strokes: List[List[Tuple[float, float]]] = self.state.strokes + (
            [self.state.cur_stroke] if self.state.cur_stroke else []
        )
        pen = QtGui.QPen(QtGui.QColor(self.state.brush_color))
        pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
        pen.setWidth(max(1, int(self.state.brush_size * self.state.scale)))
        p.setPen(pen)
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        for stroke in all_strokes:
            if not stroke or len(stroke) < 2:
                continue
            path = QtGui.QPainterPath()
            x0, y0 = self.state.doc_to_screen(*stroke[0])
            path.moveTo(x0, y0)
            for pt in stroke[1:]:
                x, y = self.state.doc_to_screen(*pt)
                path.lineTo(x, y)
            p.drawPath(path)

    def _draw_paths(self, p: QtGui.QPainter):
        paths = self.state.paths + ([self.state.cur_path] if self.state.cur_path else [])
        for path_pts in paths:
            if not path_pts or len(path_pts) < 2:
                continue
            pen = QtGui.QPen(QtGui.QColor("#ffaa00"))
            pen.setWidth(2)
            p.setPen(pen)
            path = QtGui.QPainterPath()
            x0, y0 = self.state.doc_to_screen(*path_pts[0])
            path.moveTo(x0, y0)
            for pt in path_pts[1:]:
                x, y = self.state.doc_to_screen(*pt)
                path.lineTo(x, y)
            p.drawPath(path)
