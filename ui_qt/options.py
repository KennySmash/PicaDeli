from __future__ import annotations

from typing import Optional

from PySide6 import QtWidgets, QtGui, QtCore

from .tools import Tools


class ToolOptions(QtWidgets.QStackedWidget):
    def __init__(self, overlay, parent: Optional[QtWidgets.QWidget] = None, on_change: Optional[callable] = None):
        super().__init__(parent)
        self.overlay = overlay
        self._on_change = on_change

        # Pages for each tool
        self.page_pan = self._make_pan_page()
        self.page_brush = self._make_brush_page()
        self.page_pen = self._make_pen_page()
        self.page_art = self._make_artboard_page()

        self.addWidget(self.page_pan)
        self.addWidget(self.page_brush)
        self.addWidget(self.page_pen)
        self.addWidget(self.page_art)

        # Initial selection
        self.setCurrentIndex(self._index_for_tool(self.overlay.state.tool))
        try:
            self.overlay.tool_changed.connect(self._on_tool_changed)  # type: ignore[attr-defined]
        except Exception:
            pass

    def _index_for_tool(self, tool: str) -> int:
        order = [Tools.PAN, Tools.BRUSH, Tools.PEN, Tools.ARTBOARD]
        return max(0, order.index(tool))

    def _on_tool_changed(self, tool: str) -> None:
        self.setCurrentIndex(self._index_for_tool(tool))

    def _make_pan_page(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        l = QtWidgets.QFormLayout(w)
        l.addRow("Pan:", QtWidgets.QLabel("Drag canvas • Space to pan"))
        return w

    def _make_brush_page(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        l = QtWidgets.QFormLayout(w)

        # Brush size
        size_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        size_slider.setRange(1, 64)
        size_slider.setValue(int(self.overlay.state.brush_size))
        size_lbl = QtWidgets.QLabel(f"{int(self.overlay.state.brush_size)} px")

        def on_size(val: int):
            self.overlay.state.brush_size = float(val)
            size_lbl.setText(f"{val} px")
            self.overlay.update()
            if self._on_change:
                self._on_change()

        size_slider.valueChanged.connect(on_size)
        size_row = QtWidgets.QHBoxLayout()
        size_row.addWidget(size_slider)
        size_row.addWidget(size_lbl)
        size_row_widget = QtWidgets.QWidget()
        size_row_widget.setLayout(size_row)
        l.addRow("Size", size_row_widget)

        # Brush color
        color_btn = QtWidgets.QPushButton()
        color_btn.setText("")
        color_btn.setFixedHeight(28)
        color_btn.setStyleSheet(f"background: {self.overlay.state.brush_color}; border: 1px solid #444;")

        def pick_color():
            col = QtWidgets.QColorDialog.getColor(QtGui.QColor(self.overlay.state.brush_color), w, "Choose Brush Color")
            if col.isValid():
                self.overlay.state.brush_color = col.name()
                color_btn.setStyleSheet(f"background: {col.name()}; border: 1px solid #444;")
                self.overlay.update()
                if self._on_change:
                    self._on_change()

        color_btn.clicked.connect(pick_color)
        l.addRow("Color", color_btn)
        return w

    def _make_pen_page(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        l = QtWidgets.QFormLayout(w)
        l.addRow("Pen:", QtWidgets.QLabel("Click to add points • Enter/Esc to finish"))
        return w

    def _make_artboard_page(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        l = QtWidgets.QFormLayout(w)

        width_spin = QtWidgets.QSpinBox()
        height_spin = QtWidgets.QSpinBox()
        width_spin.setRange(1, 16384)
        height_spin.setRange(1, 16384)
        _, _, aw, ah = self.overlay.state.artboard
        width_spin.setValue(int(aw))
        height_spin.setValue(int(ah))

        def on_w(val: int):
            ax, ay, _, h = self.overlay.state.artboard
            self.overlay.state.artboard = (ax, ay, float(val), float(h))
            self.overlay.update()
            if self._on_change:
                self._on_change()

        def on_h(val: int):
            ax, ay, w_, _ = self.overlay.state.artboard
            self.overlay.state.artboard = (ax, ay, float(w_), float(val))
            self.overlay.update()
            if self._on_change:
                self._on_change()

        width_spin.valueChanged.connect(on_w)
        height_spin.valueChanged.connect(on_h)

        l.addRow("Width", width_spin)
        l.addRow("Height", height_spin)
        return w
