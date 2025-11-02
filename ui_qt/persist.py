from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any


def settings_path(doc_path: Path) -> Path:
    return doc_path / "ui" / "panel_settings.json"


def load_settings(doc_path: Path) -> Dict[str, Any]:
    try:
        p = settings_path(doc_path)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def save_settings(doc_path: Path, data: Dict[str, Any]) -> None:
    try:
        p = settings_path(doc_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        txt = json.dumps(data, indent=2)
        p.write_text(txt, encoding="utf-8")
    except Exception:
        # Best-effort; ignore write failures for now
        pass

