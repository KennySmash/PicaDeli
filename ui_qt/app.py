from __future__ import annotations

import sys
import os
import logging


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]

    try:
        from PySide6 import QtWidgets, QtCore, QtGui
    except Exception as exc:
        print("Qt (PySide6) not installed. Install with: pip install PySide6", file=sys.stderr)
        print(f"Details: {exc}", file=sys.stderr)
        return 1

    # Try to import wgpu canvas (instantiate later with a parent)
    wgpu_available = True
    wgpu_err = None
    CanvasCtor = None
    SceneFactory = None
    canvas = None
    scene = None
    try:
        import wgpu.backends.auto  # noqa: F401
        try:
            from rendercanvas.qt import WgpuCanvas as CanvasCtor
        except Exception:
            from wgpu.gui.qt import WgpuCanvas as CanvasCtor
        from .wgpu_canvas import create_wgpu_scene as SceneFactory

        if os.environ.get("WGPU_BACKEND"):
            print(f"WGPU_BACKEND={os.environ['WGPU_BACKEND']}")
    except Exception as exc:
        wgpu_available = False
        wgpu_err = exc

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(["PicaDeli Qt"])  # type: ignore[arg-type]

    win = QtWidgets.QMainWindow()
    win.setWindowTitle("PicaDeli — Qt + ImGui + wgpu")
    win.resize(1200, 800)

    central = QtWidgets.QWidget()
    root_layout = QtWidgets.QVBoxLayout(central)
    root_layout.setContentsMargins(0, 0, 0, 0)
    root_layout.setSpacing(0)

    # Toolbar (Qt side-by-side panels approach for now)
    toolbar = QtWidgets.QToolBar()
    toolbar.setMovable(True)
    win.addToolBar(QtCore.Qt.TopToolBarArea, toolbar)

    # (removed wgpu status label from toolbar)

    # Central splitter: left = (future) panels; right = canvas + overlay tools
    splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
    root_layout.addWidget(splitter, stretch=1)

    # Left tools panel (emoji buttons)
    from .tools import Tools

    tools_panel = QtWidgets.QWidget()
    tools_panel.setMinimumWidth(64)
    tools_panel.setMaximumWidth(80)
    tools_panel.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Expanding)
    vbox_tools = QtWidgets.QVBoxLayout(tools_panel)
    vbox_tools.setContentsMargins(6, 6, 6, 6)
    vbox_tools.setSpacing(8)

    group = QtWidgets.QButtonGroup(tools_panel)
    group.setExclusive(True)

    btns = {}
    def add_tool_btn(emoji: str, tip: str, tool_id: str):
        b = QtWidgets.QPushButton(emoji)
        b.setToolTip(tip)
        b.setCheckable(True)
        b.setFixedHeight(40)
        b.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        vbox_tools.addWidget(b)
        group.addButton(b)
        btns[tool_id] = b

    add_tool_btn("✋", "Pan (V)", Tools.PAN)
    add_tool_btn("🖌️", "Brush (B)", Tools.BRUSH)
    add_tool_btn("✒️", "Pen (P)", Tools.PEN)
    add_tool_btn("🗒️", "Artboard (A)", Tools.ARTBOARD)
    vbox_tools.addStretch(1)
    btns[Tools.PAN].setChecked(True)

    splitter.addWidget(tools_panel)

    # Right: canvas area (wgpu or placeholder) with overlay
    right = QtWidgets.QStackedWidget()
    right.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
    splitter.addWidget(right)
    # Prefer canvas taking the space
    splitter.setCollapsible(0, False)
    splitter.setCollapsible(1, False)
    splitter.setStretchFactor(0, 0)
    splitter.setStretchFactor(1, 1)
    splitter.setSizes([260, 1400])

    if wgpu_available and CanvasCtor is not None:
        # Container that stacks canvas + transparent overlay
        container = QtWidgets.QWidget()
        container.setLayout(QtWidgets.QVBoxLayout())
        container.layout().setContentsMargins(0, 0, 0, 0)
        container.layout().setSpacing(0)

        # Use absolute layout to stack widgets
        absolute = QtWidgets.QStackedLayout()
        absolute.setStackingMode(QtWidgets.QStackedLayout.StackingMode.StackAll)
        container.setLayout(absolute)
        from PySide6 import QtWidgets as _QtWidgets
        from PySide6 import QtCore as _QtCore
        from PySide6 import QtGui as _QtGui

        # Ensure widgets expand to fill
        absolute.setContentsMargins(0, 0, 0, 0)
        try:
            canvas = CanvasCtor(container)  # type: ignore[call-arg]
        except TypeError:
            canvas = CanvasCtor()  # type: ignore[call-arg]
            canvas.setParent(container)
        canvas.setSizePolicy(_QtWidgets.QSizePolicy.Policy.Expanding, _QtWidgets.QSizePolicy.Policy.Expanding)
        absolute.addWidget(canvas)

        from .tools import ToolState, Tools
        from .overlay import CanvasOverlay

        state = ToolState()
        overlay = CanvasOverlay(container, state)
        overlay.setSizePolicy(_QtWidgets.QSizePolicy.Policy.Expanding, _QtWidgets.QSizePolicy.Policy.Expanding)
        absolute.addWidget(overlay)
        # Initial fit once geometry is available after layout pass
        QtCore.QTimer.singleShot(0, overlay.fit_to_view)
        QtCore.QTimer.singleShot(100, overlay.fit_to_view)

        # Initialize scene now that canvas exists
        try:
            scene = SceneFactory(canvas)  # type: ignore[arg-type]
        except Exception as exc:
            wgpu_available = False
            wgpu_err = exc

        # If the canvas lacks a request_draw mechanism, drive frames with a timer
        if scene is not None and not hasattr(canvas, "request_draw"):
            timer = QtCore.QTimer(container)
            timer.setInterval(16)
            timer.timeout.connect(scene.draw_frame)  # type: ignore[arg-type]
            timer.start()
            # Keep reference to prevent GC
            container._frame_timer = timer  # type: ignore[attr-defined]

        container.setSizePolicy(_QtWidgets.QSizePolicy.Policy.Expanding, _QtWidgets.QSizePolicy.Policy.Expanding)
        right.addWidget(container)
        right.setCurrentWidget(container)

        # Bind left tools buttons to overlay
        for child in tools_panel.findChildren(QtWidgets.QPushButton):
            tip = child.toolTip()
            if "Pan" in tip:
                child.toggled.connect(lambda checked, o=overlay: checked and o.set_tool(Tools.PAN))  # type: ignore[arg-type]
            elif "Brush" in tip:
                child.toggled.connect(lambda checked, o=overlay: checked and o.set_tool(Tools.BRUSH))  # type: ignore[arg-type]
            elif "Pen" in tip:
                child.toggled.connect(lambda checked, o=overlay: checked and o.set_tool(Tools.PEN))  # type: ignore[arg-type]
            elif "Artboard" in tip:
                child.toggled.connect(lambda checked, o=overlay: checked and o.set_tool(Tools.ARTBOARD))  # type: ignore[arg-type]
        # (removed Fit to View button; auto-fit occurs by default)
    else:
        # Software fallback: dummy canvas + overlay so tools work
        from .dummy_canvas import DummyCanvas

        container = QtWidgets.QWidget()
        container.setLayout(QtWidgets.QVBoxLayout())
        container.layout().setContentsMargins(0, 0, 0, 0)
        container.layout().setSpacing(0)

        absolute = QtWidgets.QStackedLayout()
        absolute.setStackingMode(QtWidgets.QStackedLayout.StackingMode.StackAll)
        container.setLayout(absolute)

        sw_canvas = DummyCanvas(container)
        absolute.addWidget(sw_canvas)

        from .tools import ToolState, Tools
        from .overlay import CanvasOverlay

        state = ToolState()
        overlay = CanvasOverlay(container, state)
        absolute.addWidget(overlay)
        QtCore.QTimer.singleShot(0, overlay.fit_to_view)
        QtCore.QTimer.singleShot(100, overlay.fit_to_view)

        from PySide6 import QtWidgets as _QtWidgets
        absolute.setContentsMargins(0, 0, 0, 0)
        container.setSizePolicy(_QtWidgets.QSizePolicy.Policy.Expanding, _QtWidgets.QSizePolicy.Policy.Expanding)
        right.addWidget(container)
        right.setCurrentWidget(container)

        # Bind left tools buttons to overlay
        for child in tools_panel.findChildren(QtWidgets.QPushButton):
            tip = child.toolTip()
            if "Pan" in tip:
                child.toggled.connect(lambda checked, o=overlay: checked and o.set_tool(Tools.PAN))  # type: ignore[arg-type]
            elif "Brush" in tip:
                child.toggled.connect(lambda checked, o=overlay: checked and o.set_tool(Tools.BRUSH))  # type: ignore[arg-type]
            elif "Pen" in tip:
                child.toggled.connect(lambda checked, o=overlay: checked and o.set_tool(Tools.PEN))  # type: ignore[arg-type]
            elif "Artboard" in tip:
                child.toggled.connect(lambda checked, o=overlay: checked and o.set_tool(Tools.ARTBOARD))  # type: ignore[arg-type]
        # (removed Fit to View button; auto-fit occurs by default)

    # Console dock: starts with app and captures logs
    from .console import ConsoleWidget, QtLogHandler, StreamToLogger
    console = ConsoleWidget()
    dock = QtWidgets.QDockWidget("Console")
    dock.setObjectName("ConsoleDock")
    dock.setWidget(console)
    win.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)

    # Logging setup
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    qt_handler = QtLogHandler(console)
    root_logger.addHandler(qt_handler)
    # Also keep stderr output for visibility
    root_logger.addHandler(logging.StreamHandler(sys.stderr))
    # Redirect print/stdout to logging
    sys.stdout = StreamToLogger("STDOUT", level=logging.INFO)  # type: ignore[assignment]
    sys.stderr = StreamToLogger("STDERR", level=logging.ERROR)  # type: ignore[assignment]

    log = logging.getLogger("ui_qt")
    log.info("PicaDeli Qt starting")
    log.info("wgpu available: %s", wgpu_available)
    if not wgpu_available and wgpu_err:
        log.warning("wgpu import failed: %r", wgpu_err)

    # Detailed environment dump
    def dump_env_info():
        import platform
        import sys as _sys
        from PySide6 import QtCore as _QtCore
        log.info("Python: %s", _sys.version.replace("\n", " "))
        log.info("Python exec: %s", _sys.executable)
        log.info("Platform: %s", platform.platform())
        try:
            # PySide6 version and Qt runtime version
            qt_ver = _QtCore.qVersion()
            pyside_ver = getattr(_QtCore, "__version__", "unknown")
            log.info("PySide6: %s | Qt: %s", pyside_ver, qt_ver)
        except Exception as exc:
            log.warning("Qt version query failed: %r", exc)
        if wgpu_available:
            try:
                import wgpu as _wgpu
                log.info("wgpu: %s (%s)", getattr(_wgpu, "__version__", "unknown"), getattr(_wgpu, "__file__", "?"))
                # Adapter info if available
                if scene is not None:
                    adapter = getattr(scene.device, "adapter", None)
                    fmt = None
                    try:
                        fmt = canvas.get_preferred_format(adapter) if adapter else None
                    except Exception:
                        pass
                    info = getattr(adapter, "info", None)
                    log.info("wgpu adapter: %s", info if info is not None else repr(adapter))
                    if fmt:
                        log.info("wgpu preferred format: %s", fmt)
            except Exception as exc:
                log.warning("wgpu env query failed: %r", exc)

    dump_env_info()

    # Bottom bar with Console toggle
    statusbar = QtWidgets.QStatusBar()
    win.setStatusBar(statusbar)
    btn_console = QtWidgets.QPushButton("Console")
    btn_console.setCheckable(True)
    btn_console.setChecked(True)
    btn_console.clicked.connect(lambda checked: dock.setVisible(checked))  # type: ignore[arg-type]
    # Keep button state in sync if user hides the dock elsewhere
    dock.visibilityChanged.connect(lambda vis: btn_console.setChecked(bool(vis)))  # type: ignore[arg-type]
    statusbar.addPermanentWidget(btn_console)

    # Menu with ImGui demo (external window for now)
    menu = win.menuBar()
    view_menu = menu.addMenu("View")
    # Toggle console
    act_console = view_menu.addAction("Toggle Console")
    act_console.setCheckable(True)
    act_console.setChecked(True)
    act_console.triggered.connect(lambda checked: dock.setVisible(checked))  # type: ignore[arg-type]

    def open_imgui_demo():
        try:
            from imgui_bundle import immapp, imgui
        except Exception as exc:
            QtWidgets.QMessageBox.information(
                win,
                "ImGui not available",
                "Install with: pip install imgui-bundle\n\nDetails: {}".format(exc),
            )
            return

        def gui():
            imgui.text("ImGui is working (imgui-bundle demo)")
            imgui.separator()
            imgui.text("We will integrate overlay in a wgpu pass next.")

        immapp.run(gui_function=gui, window_title="PicaDeli ImGui Demo")

    act_imgui = view_menu.addAction("Open ImGui Demo")
    act_imgui.triggered.connect(open_imgui_demo)  # type: ignore[attr-defined]

    act_dump = view_menu.addAction("Dump Environment Info")
    act_dump.triggered.connect(lambda: dump_env_info())  # type: ignore[arg-type]

    win.setCentralWidget(central)
    win.show()
    log.info("Qt window shown; entering event loop")

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
