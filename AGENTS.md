# Repository Guidelines

This guide helps contributors work effectively on PicaDeli, a modular 2D creation suite with a Rust/C++ core, a Python plugin layer, and a Qt/ImGui UI.

## Project Structure & Module Organization
- `core/` – Runtime engine (Rust/C++), file I/O, host APIs.
- `node_engine/` – DAG execution (CPU/GPU, `wgpu`).
- `ui/` – Qt + ImGui editor.
- `plugins/` – Python SDK and built‑ins.
- `cli/` – `vxcli` tools.
- `schemas/` – JSON Schemas for `.vxdoc`/`.vxlib`.
- `tests/` – Automated suites across stacks.
- `examples/` – Sample `.vxdoc` projects and assets.
- `docs/` – Design docs and agent specs.

## Build, Test, and Development Commands
- Build all: `make build` – orchestrates CMake/Cargo where applicable.
- Core (Rust): `cargo build -p core` | tests: `cargo test -p core`.
- Core/UI (CMake): `cmake -S core -B build && cmake --build build` | tests: `ctest --test-dir build`.
- Python plugins: `pytest -q` (from repo root or `plugins/`).
- Run CLI: `./vxcli serve examples/basic.vxdoc`.
- Dev UI: `python scripts/dev_ui.py` (hot‑reload panels/assets).

## Coding Style & Naming Conventions
- Rust: `rustfmt` + `clippy --all-targets --all-features`.
- C++: `clang-format` (file‑scoped; keep includes ordered). Prefer RAII and `span`/`string_view` over raw pointers.
- Python: `black` (88 cols) + `ruff` for linting/import order.
- JSON: 2‑space indent; validate against `schemas/`.
- Naming: snake_case for files and Python; PascalCase for types; camelCase for fields; node/plugin IDs are snake_case (e.g., `blur_plus`).

## Testing Guidelines
- Place Rust tests alongside modules or under `core/**/tests/`.
- Python tests live in `tests/` or `plugins/**/tests/` as `test_*.py`.
- C++ tests via CTest/GTest in `core/**/tests/`.
- Aim for meaningful coverage on core serialization, node eval, and schema changes. Include regression cases for `.vxdoc` round‑trip.

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`.
- Keep commits scoped and descriptive; reference issues (`#123`).
- PRs must include: summary, rationale, test plan, affected modules; UI changes add screenshots/gifs; core changes note performance impact; schema changes update `schemas/` and docs.

## Working Method: JSON Tickets
- Location: `projects/<name>/tickets/` with `finished/` subfolder.
- One task per JSON file: `PD-123-add-node-cache.json`.
- Complete by PR: reference ticket ID in branch/commit (e.g., `feat(PD-123): …`).
- Move on done: `git mv projects/app/tickets/PD-123-add-node-cache.json projects/app/tickets/finished/`.

Minimal ticket schema example:
```json
{
  "id": "PD-123",
  "title": "Implement node cache invalidation",
  "why": "Reduce redundant GPU eval; speed interactive edits",
  "what": ["Add dirty-prop to node graph", "Cache by node+inputs hash"],
  "acceptance": ["Cache hit rate metric exposed", "No correctness regressions"],
  "owner": "@handle",
  "links": ["#456"],
  "created": "2025-01-15"
}
```

Conventions:
- Keep tickets small (1–3 days). Group epics under `projects/<name>/epics/PD-100.json` if needed.
- Prefer concrete acceptance criteria; include benchmarks when performance-related.
- Record key decisions under `why`; if trade-offs occur during implementation, update the ticket before moving to `finished/`.

## Security & Configuration Tips
- Never commit secrets; use `.env.local` and example templates.
- Keep large binaries out of Git; place sample assets in `examples/`.
- Prefer deterministic builds (`--locked`, pinned deps). Validate `.vxdoc` with `vxcli validate` when available.
