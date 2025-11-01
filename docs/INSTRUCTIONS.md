# ImageEditor – Development Instructions

These rules define how AI coding agents (and humans) work on this project.

---

## 1. Language & Stack

| Layer               | Language                     | Notes                                                    |
| ------------------- | ---------------------------- | -------------------------------------------------------- |
| Core Runtime        | Rust / C++                   | Performance-critical code; exposes C API for Python      |
| Scripting / Plugins | Python 3.12+                 | Primary extension language                               |
| GPU Rendering       | wgpu                         | Cross-platform abstraction (Vulkan, Metal, DX12, WebGPU) |
| UI                  | Qt + ImGui                   | Qt for docking, ImGui for panels and editors             |
| Networking          | Python (FastAPI, websockets) | For presence + collaboration                             |
| Packaging           | ZIP-based `.vxdoc`, `.vxlib` | JSON manifests; Git-aware                                |

---

## 2. Repository Layout

```
/core/              → Rust or C++ engine code (file format, runtime, wgpu core)
/ui/                → Qt + ImGui interface code
/node_engine/       → Node system and GPU evaluation
/plugins/           → Python plugins, nodes, and extensions
/cli/               → vxcli tool (document, render, presence)
/schemas/           → JSON schemas for nodes, layers, manifests
/docs/              → Developer and architecture docs
/tests/             → Unit + integration tests
/examples/          → Example documents and assets
```

---

## 3. Coding Conventions

* **Python:**

  * Follow PEP8, no semicolons, descriptive naming.
  * Modules should expose clear entrypoints (`register()`, `execute()`, etc.).
* **Rust/C++:**

  * Use RAII and prefer immutable references.
  * Ensure FFI-safe structs for Python bindings.
* **JSON:**

  * Must include `"version"` key at top level.
  * Use snake_case for fields.
* **Node Definitions:**

  * Each node JSON defines:

    ```json
    {
      "id": "uuid",
      "type": "image_blur",
      "inputs": { "image": "ref://node-id" },
      "params": { "radius": 10.0 },
      "gpu_capable": true
    }
    ```
* **Rendering:**

  * All GPU tasks go through wgpu compute or fragment shaders.
  * CPU fallback must mirror GPU result within tolerance.

---

## 4. Collaboration Model

* Use **WebSocket-based sync** for live editing.
* Maintain `/collab/presence.json` inside `.vxdoc` with current users.
* Use event-based change propagation (before render).
* CLI can act as a local or enterprise host.

---

## 5. File Format Guidelines

Each `.vxdoc` or `.vxlib` is a ZIP with:

```
/manifest.json
/layers/*.json
/nodes/*.json
/assets/*
/collab/presence.json (optional)
```

* All JSON files must be UTF-8 encoded.
* Keep binary assets separate from metadata for clean Git diffs.
* Document metadata should include:

  ```json
  {
    "app_version": "0.1.0",
    "created_with": "vxedit",
    "uuid": "doc-uuid",
    "linked_libraries": ["git+https://..."]
  }
  ```

---

## 6. Plugin API Design

Plugins must:

* Register via `vx.plugin.register(<manifest>)`
* Expose metadata: `name`, `version`, `type`, and `entrypoint`
* Operate in a sandboxed Python environment.
* Never block the UI thread; long ops should yield.

---

## 7. Testing & CI/CD

* Use `pytest` (Python) and `cargo test` (Rust).
* Each test case must have a minimal `.vxdoc` fixture.
* Run `vxcli validate` to ensure schema compliance.
* CI builds containers via Docker buildx.

---

## 8. Coding Style Summary

* Prefer composition over inheritance.
* Keep node and UI logic decoupled.
* Prioritize **action propagation before render** for collab UX.
* Follow the roadmap phases:

  1. Core + Node runtime
  2. GPU acceleration + Plugin API
  3. Animation + Library chaining
  4. Collaboration + CLI broker
  5. FFmpeg export + Web prototype
