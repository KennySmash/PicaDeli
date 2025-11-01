# 🖌️ PicaDeli

### A Modern, Collaborative 2D Creation Suite

PicaDeli is an open, node-based image editor that blends **raster, vector, and procedural** workflows into a single unified environment.
Think of it as *"Blender for 2D"* — fast, scriptable, collaborative, and deeply version-controlled.

Yes, for now this is vibe coded for a proof of concept, software out the door is worth twice in theory

---

## ✨ Core Idea

Traditional image editors treat files as static binaries.
PicaDeli treats them as **living documents** — tiny repositories made of layers, nodes, and assets.
Every brush stroke, vector shape, and procedural effect is **tracked, shareable, and reproducible**.

Each project file (`.vxdoc`) is a **ZIP-based micro-repo** containing:

* `manifest.json` → metadata & linked libraries
* `nodes/*.json` → node graph definitions
* `layers/*.json` → layer data (raster, vector, procedural)
* `assets/` → embedded resources
* `collab/presence.json` → current collaborators (when active)

This makes version control, collaboration, and automation first-class citizens — not afterthoughts.

---

## 🧩 Major Systems

| Area              | Description                                                                       |
| ----------------- | --------------------------------------------------------------------------------- |
| **Core Runtime**  | Fast C++/Rust host that manages documents, file I/O, and plugin interfaces        |
| **Node Engine**   | Global DAG for effects, animation, and exports (GPU-accelerated via `wgpu`)       |
| **UI Layer**      | Qt + ImGui hybrid interface for canvases, node graphs, and timelines              |
| **Plugin System** | Python-based scripting and automation layer for nodes, tools, and exporters       |
| **Collaboration** | Real-time P2P or brokered editing via WebSocket service and presence files        |
| **CLI Tools**     | `vxcli` for rendering, converting, validating, and hosting collaborative sessions |

---

## 🧠 Design Philosophy

* **Non-destructive editing** — every operation is a node in the graph.
* **Scriptable first** — Python is used for automation, pipelines, and extensions.
* **Transparent data** — all metadata is JSON and human-readable.
* **Collaborative by default** — WebSocket presence and change propagation before render.
* **Version-aware** — every document can live comfortably inside Git.
* **GPU everywhere** — powered by `wgpu` for Vulkan/Metal/DX12/WebGPU support.

---

## 🧱 Repository Layout

```
/core/          → Runtime engine (Rust/C++)
/ui/            → Qt + ImGui editor UI
/node_engine/   → Node system and GPU evaluation
/plugins/       → Python plugin SDK and built-ins
/cli/           → vxcli command-line utilities
/schemas/       → JSON schema definitions
/docs/          → Design docs, agent specs, and dev guides
/tests/         → Automated test suites
/examples/      → Sample projects and assets
```

---

## 🚀 Getting Started (Developers)

### Prerequisites

* Python 3.12+
* Rust or C++17 toolchain
* Node.js (for UI asset pipeline, optional)
* CMake / Ninja
* Git + Docker (for CI or container builds)

### Building

```bash
git clone https://github.com/your-org/picadeli.git
cd picadeli
make build
```

### Running

```bash
./vxcli serve example.vxdoc
```

### Editing

```bash
python scripts/dev_ui.py
```

---

## 🤝 Collaboration Model

* Each open `.vxdoc` tracks current users in `/collab/presence.json`.
* All edits are broadcast over WebSocket channels.
* Render happens locally; **action propagation comes first** to keep UX responsive.
* Enterprise mode: a CLI broker can act as a host for multiple editors.

---

## 🧩 Extending PicaDeli

PicaDeli is built for extension.
You can write plugins in Python that register new nodes, tools, exporters, or panels.

Example:

```python
import vx

def register():
    vx.plugin.register({
        "name": "blur_plus",
        "version": "1.0.0",
        "type": "node",
        "entrypoint": "blur_plus.execute"
    })
```

---

## 📘 Documentation

* [`docs/agents.md`](./docs/agents.md) — AI agent roles and division of labor
* [`docs/instructions.md`](./docs/instructions.md) — technical conventions and repo rules

---

## 🧪 Roadmap

1. **Core + Node runtime**
2. **GPU acceleration + Plugin API**
3. **Animation + Library chaining**
4. **Collaboration + CLI broker**
5. **FFmpeg export + Web prototype**

---

## 🧑‍💻 Vision

PicaDeli is not just another editor — it’s a **creative ecosystem**:

* Open, modular, and version-controlled by design.
* Seamlessly scriptable and extensible.
* Built for artists and developers who believe tools should evolve with them.

Welcome to the future of 2D creation.
**Welcome to PicaDeli.**
