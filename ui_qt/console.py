from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from PySide6 import QtCore, QtWidgets, QtGui


class ConsoleWidget(QtWidgets.QPlainTextEdit):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.setReadOnly(True)
        # Wrap long lines to the widget width for readability
        try:
            self.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.WidgetWidth)
        except Exception:
            # Fallback in case of API differences
            self.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)  # type: ignore[attr-defined]
        # Prefer wrapping anywhere to avoid horizontal scrolling
        try:
            self.setWordWrapMode(QtGui.QTextOption.WrapAnywhere)
        except Exception:
            pass
        self.document().setMaximumBlockCount(2000)
        font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
        self.setFont(font)

    @QtCore.Slot(str)
    def append_line(self, text: str) -> None:
        self.appendPlainText(text.rstrip("\n"))


class _LogEmitter(QtCore.QObject):
    message = QtCore.Signal(str)


class QtLogHandler(logging.Handler):
    """A logging handler that forwards records to a ConsoleWidget via signals."""

    def __init__(self, console: ConsoleWidget, level=logging.INFO):
        super().__init__(level)
        self.console = console
        self.emitter = _LogEmitter()
        self.emitter.message.connect(self.console.append_line)
        self.setFormatter(logging.Formatter("[%(levelname)s %(asctime)s] %(name)s: %(message)s", "%H:%M:%S"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self.emitter.message.emit(msg)
        except Exception:
            self.handleError(record)


class StreamToLogger:
    """File-like object that redirects writes to logging."""

    def __init__(self, logger_name: str, level=logging.INFO):
        self.logger = logging.getLogger(logger_name)
        self.level = level
        self._buffer = ""

    def write(self, message):
        self._buffer += str(message)
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            if line:
                self.logger.log(self.level, line)

    def flush(self):
        if self._buffer:
            self.logger.log(self.level, self._buffer)
            self._buffer = ""
