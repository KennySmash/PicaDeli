import argparse
import json
import sys
from pathlib import Path


def validate_path(path: Path) -> bool:
    """Minimal validator for a directory-style .vxdoc.

    Checks for manifest.json and required subfolders/files referenced by README.
    """
    if not path.exists():
        print(f"error: path not found: {path}", file=sys.stderr)
        return False

    if path.is_file():
        print("error: expected a directory-style .vxdoc for now", file=sys.stderr)
        return False

    manifest = path / "manifest.json"
    nodes_dir = path / "nodes"
    layers_dir = path / "layers"
    assets_dir = path / "assets"
    collab_dir = path / "collab"

    missing = [p for p in [manifest, nodes_dir, layers_dir, assets_dir, collab_dir] if not p.exists()]
    if missing:
        for m in missing:
            print(f"error: missing required entry: {m}", file=sys.stderr)
        return False

    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"error: manifest.json not valid JSON: {exc}", file=sys.stderr)
        return False

    required_keys = ["name", "schema_version", "type"]
    for key in required_keys:
        if key not in data:
            print(f"error: manifest missing key: {key}", file=sys.stderr)
            return False

    if data.get("type") != "vxdoc":
        print("error: manifest.type must be 'vxdoc'", file=sys.stderr)
        return False

    # Basic presence check for at least one node/layer file
    has_node = any(nodes_dir.glob("*.json"))
    has_layer = any(layers_dir.glob("*.json"))
    if not (has_node and has_layer):
        print("error: expected at least one node and one layer JSON", file=sys.stderr)
        return False

    # If presence file exists, ensure it's JSON
    presence = collab_dir / "presence.json"
    try:
        json.loads(presence.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"error: collab/presence.json invalid JSON: {exc}", file=sys.stderr)
        return False

    return True


def cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.path)
    ok = validate_path(path)
    print("valid" if ok else "invalid")
    return 0 if ok else 1


def cmd_serve(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if not validate_path(path):
        print("error: cannot serve invalid document", file=sys.stderr)
        return 1
    print(f"Serving {path} (stub) — press Ctrl+C to quit")
    # In a future iteration, start a WebSocket and file watcher here.
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="vxcli", description="PicaDeli CLI (scaffold)")
    sub = p.add_subparsers(dest="cmd", required=True)

    pv = sub.add_parser("validate", help="Validate a directory-style .vxdoc")
    pv.add_argument("path", help="Path to .vxdoc directory")
    pv.set_defaults(func=cmd_validate)

    ps = sub.add_parser("serve", help="Serve a .vxdoc (stub)")
    ps.add_argument("path", help="Path to .vxdoc directory")
    ps.set_defaults(func=cmd_serve)

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

