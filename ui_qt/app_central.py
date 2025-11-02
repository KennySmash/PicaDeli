from __future__ import annotations

import os
import sys
import json
import logging
from pathlib import Path


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    doc_path = Path(argv[0]) if argv else Path("examples/basic.vxdoc")

    try:
        from PySide6 import QtWidgets, QtCore, QtGui
    except Exception as exc:
        print("Qt (PySide6) not installed. Install with: pip install PySide6", file=sys.stderr)
        print(f"Details: {exc}", file=sys.stderr)
        return 1

    # Probe wgpu (defer instantiation of canvas until we have a parent)
    wgpu_available = True
    wgpu_err = None
    CanvasCtor = None
    SceneFactory = None
    try:
        import wgpu.backends.auto  # noqa: F401
        try:
            from rendercanvas.qt import WgpuCanvas as CanvasCtor  # modern path
        except Exception:
            from wgpu.gui.qt import WgpuCanvas as CanvasCtor  # deprecated fallback
        from .wgpu_canvas import create_wgpu_scene as SceneFactory
        if os.environ.get("WGPU_BACKEND"):
            print(f"WGPU_BACKEND={os.environ['WGPU_BACKEND']}")
    except Exception as exc:
        wgpu_available = False
        wgpu_err = exc

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(["PicaDeli Qt"])  # type: ignore[arg-type]

    win = QtWidgets.QMainWindow()
    win.setWindowTitle("PicaDeli — Qt + wgpu")
    win.resize(1280, 900)

    # Central canvas container: stacked (canvas below, overlay above)
    central_container = QtWidgets.QWidget()
    central_stack = QtWidgets.QStackedLayout(central_container)
    central_stack.setStackingMode(QtWidgets.QStackedLayout.StackingMode.StackAll)
    central_stack.setContentsMargins(0, 0, 0, 0)
    win.setCentralWidget(central_container)

    # Left Tools dock (emoji buttons)
    from .tools import Tools
    tools_panel = QtWidgets.QWidget()
    vbox_tools = QtWidgets.QVBoxLayout(tools_panel)
    vbox_tools.setContentsMargins(6, 6, 6, 6)
    vbox_tools.setSpacing(8)
    group = QtWidgets.QButtonGroup(tools_panel)
    group.setExclusive(True)

    def add_tool_btn(emoji: str, tip: str, tool_id: str):
        b = QtWidgets.QPushButton(emoji)
        b.setToolTip(tip)
        b.setCheckable(True)
        b.setFixedSize(48, 40)
        b.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        vbox_tools.addWidget(b)
        group.addButton(b)
        b.tool_id = tool_id  # type: ignore[attr-defined]
        return b

    btn_pan = add_tool_btn("✋", "Pan (V)", Tools.PAN)
    btn_brush = add_tool_btn("🖌️", "Brush (B)", Tools.BRUSH)
    btn_pen = add_tool_btn("✒️", "Pen (P)", Tools.PEN)
    btn_art = add_tool_btn("🗒️", "Artboard (A)", Tools.ARTBOARD)
    vbox_tools.addStretch(1)
    btn_pan.setChecked(True)

    dock_tools = QtWidgets.QDockWidget("Tools")
    dock_tools.setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable)
    dock_tools.setWidget(tools_panel)
    dock_tools.setMinimumWidth(72)
    dock_tools.setMaximumWidth(120)
    win.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock_tools)

    # Create canvas (GPU or software) and overlay
    from .overlay import CanvasOverlay
    from .tools import ToolState
    from .persist import load_settings, save_settings

    # Load persisted panel options
    s = load_settings(doc_path)
    init_state = ToolState()
    init_state.brush_color = s.get("brush_color", init_state.brush_color)
    init_state.brush_size = float(s.get("brush_size", init_state.brush_size))
    ab = s.get("artboard")
    if isinstance(ab, (list, tuple)) and len(ab) == 4:
        try:
            init_state.artboard = (float(ab[0]), float(ab[1]), float(ab[2]), float(ab[3]))
        except Exception:
            pass

    canvas = None
    scene = None
    if wgpu_available and CanvasCtor is not None:
        try:
            canvas = CanvasCtor(central_container)  # type: ignore[call-arg]
        except TypeError:
            canvas = CanvasCtor()  # type: ignore[call-arg]
            canvas.setParent(central_container)
        canvas.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        central_stack.addWidget(canvas)

        try:
            scene = SceneFactory(canvas)  # type: ignore[arg-type]
        except Exception as exc:
            wgpu_available = False
            wgpu_err = exc

    if canvas is None:
        from .dummy_canvas import DummyCanvas
        canvas = DummyCanvas(central_container)
        central_stack.addWidget(canvas)

    overlay = CanvasOverlay(central_container, init_state)
    overlay.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
    central_stack.addWidget(overlay)
    try:
        overlay.raise_()
    except Exception:
        pass
    QtCore.QTimer.singleShot(0, overlay.fit_to_view)
    QtCore.QTimer.singleShot(100, overlay.fit_to_view)
    QtCore.QTimer.singleShot(0, overlay.setFocus)

    # Drive frames for non-callback canvases
    if scene is not None and not hasattr(canvas, "request_draw"):
        timer = QtCore.QTimer(central_container)
        timer.setInterval(16)
        timer.timeout.connect(scene.draw_frame)  # type: ignore[arg-type]
        timer.start()
        central_container._frame_timer = timer  # type: ignore[attr-defined]

    # Bind left tools to overlay
    btn_pan.toggled.connect(lambda checked, o=overlay: checked and o.set_tool(Tools.PAN))  # type: ignore[arg-type]
    btn_brush.toggled.connect(lambda checked, o=overlay: checked and o.set_tool(Tools.BRUSH))  # type: ignore[arg-type]
    btn_pen.toggled.connect(lambda checked, o=overlay: checked and o.set_tool(Tools.PEN))  # type: ignore[arg-type]
    btn_art.toggled.connect(lambda checked, o=overlay: checked and o.set_tool(Tools.ARTBOARD))  # type: ignore[arg-type]

    # Right Properties dock (tool options)
    from .options import ToolOptions
    def persist_now():
        data = {
            "brush_color": overlay.state.brush_color,
            "brush_size": overlay.state.brush_size,
            "artboard": list(overlay.state.artboard),
            "tool": overlay.state.tool,
        }
        save_settings(doc_path, data)

    props = ToolOptions(overlay, on_change=persist_now)
    dock_props = QtWidgets.QDockWidget("Properties")
    dock_props.setWidget(props)
    dock_props.setMinimumWidth(220)
    win.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock_props)

    # Console dock + logging
    from .console import ConsoleWidget, QtLogHandler, StreamToLogger
    console = ConsoleWidget()
    dock = QtWidgets.QDockWidget("Console")
    dock.setObjectName("ConsoleDock")
    dock.setWidget(console)
    win.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    qt_handler = QtLogHandler(console)
    root_logger.addHandler(qt_handler)
    root_logger.addHandler(logging.StreamHandler(sys.stderr))
    sys.stdout = StreamToLogger("STDOUT", level=logging.INFO)  # type: ignore[assignment]
    sys.stderr = StreamToLogger("STDERR", level=logging.ERROR)  # type: ignore[assignment]

    log = logging.getLogger("ui_qt")
    log.info("PicaDeli Qt starting (central canvas)")
    log.info("wgpu available: %s", wgpu_available)
    if not wgpu_available and wgpu_err:
        log.warning("wgpu import failed: %r", wgpu_err)

    # Persist on overlay settings changes (e.g., artboard resize via drag)
    try:
        overlay.settings_changed.connect(persist_now)  # type: ignore[attr-defined]
    except Exception:
        pass

    # Bottom status bar with Console toggle
    statusbar = QtWidgets.QStatusBar()
    win.setStatusBar(statusbar)
    btn_console = QtWidgets.QPushButton("Console")
    btn_console.setCheckable(True)
    btn_console.setChecked(True)
    btn_console.clicked.connect(lambda checked: dock.setVisible(checked))  # type: ignore[arg-type]
    dock.visibilityChanged.connect(lambda vis: btn_console.setChecked(bool(vis)))  # type: ignore[arg-type]
    statusbar.addPermanentWidget(btn_console)
    # Doc path indicator
    doc_label = QtWidgets.QLabel(str(doc_path))
    doc_label.setStyleSheet("color:#888")
    statusbar.addWidget(doc_label, 1)

    # Menu: File + View
    menu = win.menuBar()
    file_menu = menu.addMenu("File")

    def set_document(new_path: Path):
        nonlocal doc_path
        doc_path = new_path
        doc_label.setText(str(doc_path))
        # Load settings and apply to overlay
        s2 = load_settings(doc_path)
        overlay.state.brush_color = s2.get("brush_color", overlay.state.brush_color)
        overlay.state.brush_size = float(s2.get("brush_size", overlay.state.brush_size))
        ab2 = s2.get("artboard")
        if isinstance(ab2, (list, tuple)) and len(ab2) == 4:
            try:
                overlay.state.artboard = (float(ab2[0]), float(ab2[1]), float(ab2[2]), float(ab2[3]))
            except Exception:
                pass
        # Fit view after change
        QtWidgets.QApplication.processEvents()
        QtCore.QTimer.singleShot(0, overlay.fit_to_view)
        persist_now()

    def action_new_document():
        parent_dir = QtWidgets.QFileDialog.getExistingDirectory(win, "Choose Parent Folder for New Document")
        if not parent_dir:
            return
        name, ok = QtWidgets.QInputDialog.getText(win, "New Document", "Document folder name:")
        if not ok or not name:
            return
        new_dir = Path(parent_dir) / name
        if new_dir.exists():
            QtWidgets.QMessageBox.warning(win, "Exists", f"Folder already exists: {new_dir}")
            return
        try:
            # Create skeleton
            (new_dir / "nodes").mkdir(parents=True, exist_ok=True)
            (new_dir / "layers").mkdir(parents=True, exist_ok=True)
            (new_dir / "assets").mkdir(parents=True, exist_ok=True)
            (new_dir / "collab").mkdir(parents=True, exist_ok=True)
            (new_dir / "ui").mkdir(parents=True, exist_ok=True)
            (new_dir / "assets" / ".gitkeep").write_text("", encoding="utf-8")
            # Minimal manifest
            manifest = {"name": name, "schema_version": "0.1.0", "type": "vxdoc"}
            (new_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            # Sample node and layer
            node = {"id": "node-1", "type": "solid_color", "params": {"color": "#66aaff", "width": 512, "height": 512}}
            layer = {"id": "layer-1", "name": "Base", "source_node": "node-1", "opacity": 1.0, "blend": "normal"}
            (new_dir / "nodes" / "sample.json").write_text(json.dumps(node, indent=2), encoding="utf-8")
            (new_dir / "layers" / "sample.json").write_text(json.dumps(layer, indent=2), encoding="utf-8")
            (new_dir / "collab" / "presence.json").write_text(json.dumps({"active": []}, indent=2), encoding="utf-8")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(win, "Error", f"Failed to create document:\n{exc}")
            return
        set_document(new_dir)

    def action_open_document():
        folder = QtWidgets.QFileDialog.getExistingDirectory(win, "Open Document Folder", str(doc_path))
        if not folder:
            return
        set_document(Path(folder))

    def action_save_settings():
        persist_now()
        statusbar.showMessage("UI settings saved", 2000)

    file_menu.addAction("New Document…", action_new_document)
    file_menu.addAction("Open Document Folder…", action_open_document)
    file_menu.addSeparator()
    file_menu.addAction("Save UI Settings", action_save_settings)
    file_menu.addSeparator()
    file_menu.addAction("Exit", win.close)

    view_menu = menu.addMenu("View")
    act_console = view_menu.addAction("Toggle Console")
    act_console.setCheckable(True)
    act_console.setChecked(True)
    act_console.triggered.connect(lambda checked: dock.setVisible(checked))  # type: ignore[arg-type]

    win.show()
    log.info("Qt window shown; entering event loop")
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
