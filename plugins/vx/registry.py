from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass(frozen=True)
class PluginSpec:
    name: str
    version: str
    type: str
    entrypoint: str


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: Dict[str, PluginSpec] = {}

    def register(self, spec: Dict[str, Any]) -> None:
        required = {"name", "version", "type", "entrypoint"}
        missing = [k for k in required if k not in spec]
        if missing:
            raise ValueError(f"missing keys: {missing}")
        name = spec["name"]
        if name in self._plugins:
            raise ValueError(f"plugin already registered: {name}")
        self._plugins[name] = PluginSpec(
            name=spec["name"],
            version=spec["version"],
            type=spec["type"],
            entrypoint=spec["entrypoint"],
        )

    def list(self, type: str | None = None) -> List[PluginSpec]:
        items = list(self._plugins.values())
        if type is None:
            return items
        return [p for p in items if p.type == type]


_GLOBAL_REGISTRY = PluginRegistry()


def register(spec: Dict[str, Any]) -> None:
    """Register a plugin into the global registry.

    Example:
        register({"name": "blur_plus", "version": "1.0.0", "type": "node", "entrypoint": "blur_plus.execute"})
    """
    _GLOBAL_REGISTRY.register(spec)


def get_registry() -> PluginRegistry:
    return _GLOBAL_REGISTRY

