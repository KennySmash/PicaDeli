from __future__ import annotations

from PySide6 import QtWidgets, QtGui, QtCore


class DummyCanvas(QtWidgets.QWidget):
    """Software fallback canvas.

    Provides a dark background and a request_draw() method so the rest of the
    UI can run without wgpu. The overlay draws the visuals on top.
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self._bg = QtGui.QColor(28, 32, 40)

    def paintEvent(self, ev: QtGui.QPaintEvent) -> None:
        p = QtGui.QPainter(self)
        p.fillRect(self.rect(), self._bg)
        p.end()

    # API compatibility shim
    def request_draw(self, func=None):
        if func is None:
            self.update()
        else:
            func()

