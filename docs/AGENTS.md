# ImageEditor – AI Agents Overview

This document defines the key AI agents working on the ImageEditor project and how they collaborate.
All agents share the same repository context and communicate through file diffs, structured PRs, and structured reasoning.

---

## 1. Build Agent (Core)

**Purpose:**
Implements and maintains the low-level core of the editor — including document lifecycle, ZIP file I/O, node serialization, and runtime architecture.

**Primary Stack:**
Rust or C++ for performance-critical components, Python bindings for scripting.

**Responsibilities:**

* Implement `.vxdoc` and `.vxlib` formats (ZIP + JSON manifest system).
* Manage file diffs, patching, and commit metadata.
* Expose a stable host API for Python and other plugin layers.
* Maintain the CLI (`vxcli`) and command-line service host.
* Provide interfaces for WebSocket collaboration (presence file + event broadcast).

**Handoff:**
Provides SDK headers / Python bindings for the Node Engine and UI Agents.

---

## 2. Node Engine Agent

**Purpose:**
Owns the node-based dataflow engine that powers procedural operations, compositing, effects, and animation.

**Primary Stack:**
Python + Rust backend (wgpu bindings).

**Responsibilities:**

* Define and maintain the node schema and serialization.
* Manage dataflow execution (CPU and GPU paths).
* Handle caching and dirty-state propagation.
* Support typed ports (image2D, vectorPath, mask, transform, timeline, JSON/meta, etc.).
* Integrate GPU evaluation via wgpu.
* Provide developer hooks for custom node registration.

**Handoff:**
Outputs runtime node APIs for the UI Agent and Python Plugin Agent.

---

## 3. UI Agent

**Purpose:**
Implements the visual interface of the editor using Qt for structure and ImGui for dynamic panels.

**Primary Stack:**
C++/Python hybrid (PySide6 or C++ Qt + ImGui embedding).

**Responsibilities:**

* Create dockable layout system.
* Integrate canvas viewports (wgpu surfaces).
* Manage tool system (brushes, vector editing, transforms).
* Implement Node Graph Editor (drag-drop, wire connect, inspect nodes).
* Build basic animation timeline editor.
* Expose extension points for custom panels (Python plugin API).

**Handoff:**
Connects with Node Engine for graph display, Build Agent for document state, and Plugin Agent for scripting.

---

## 4. Plugin Agent

**Purpose:**
Maintains the scripting and extensibility layer (Python).

**Responsibilities:**

* Implement plugin registration system for nodes, tools, panels, and exporters.
* Manage Python sandbox and runtime environment.
* Provide a stable API to query or modify the document.
* Expose hooks for automation, batch renders, and pipelines.

**Handoff:**
Extends the Node Engine and UI Agent capabilities.

---

## 5. Collaboration Agent

**Purpose:**
Implements the distributed editing model and network synchronization.

**Primary Stack:**
Python (FastAPI or websockets).

**Responsibilities:**

* Manage presence via `/collab/presence.json` inside document.
* Coordinate live actions via WebSocket broadcast.
* Prioritize **action propagation before render**.
* Enable P2P or brokered hosting modes.
* Integrate with CLI for enterprise hosting.

**Handoff:**
Communicates with Build Agent and UI Agent for live updates.

---

## 6. DevOps / Integrator Agent

**Purpose:**
Coordinates CI/CD, builds, packaging, and versioning.

**Responsibilities:**

* Configure buildx pipelines and container targets.
* Maintain developer docs and testing harnesses.
* Run automated regression tests on `.vxdoc` and `.vxlib` formats.
* Ensure binary compatibility across platforms.
* Build nightly editor artifacts.

---

### Agent Collaboration Diagram (Conceptual)

```
[UI Agent] ⇆ [Node Engine Agent] ⇆ [Build Agent]
     ↑               ↑                  ↑
 [Plugin Agent]   [Collab Agent]     [DevOps Agent]
```

---

### Summary

* All agents must **respect the `.vxdoc` format** as the single source of truth.
* Agents must exchange data through **defined APIs and JSON schemas**.
* No agent modifies another’s domain directly — they use exposed APIs.
* All major changes must preserve **non-destructive, node-based** workflows.
