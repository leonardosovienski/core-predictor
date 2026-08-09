"""Audit legacy vendored copies and print migration guidance.

This tool is intentionally read-only. Package installation is the supported
distribution mechanism; no command in this module writes to consumer repos.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
PACKAGE_ROOT = ROOT / "src" / "predictor_core"
MANIFEST_NAME = "CORE_MANIFEST.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def payload_files(root: Path = PACKAGE_ROOT) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def manifest(root: Path = PACKAGE_ROOT) -> dict[str, object]:
    files = {path.relative_to(root).as_posix(): _sha256(path) for path in payload_files(root)}
    aggregate = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    return {"files": files, "aggregate": aggregate}


def consumers(workspace: Path = WORKSPACE) -> list[Path]:
    return sorted(
        path
        for path in workspace.iterdir()
        if path.is_dir() and (path / "vendor" / "predictor_core").is_dir()
    )


def audit(workspace: Path = WORKSPACE) -> int:
    found = consumers(workspace)
    if not found:
        print("No legacy vendor/predictor_core copies found.")
        return 0
    canonical = manifest(PACKAGE_ROOT)
    for consumer in found:
        vendor = consumer / "vendor" / "predictor_core"
        legacy = manifest(vendor)
        state = "MATCH" if legacy["aggregate"] == canonical["aggregate"] else "DRIFT"
        print(f"{consumer.name}: {state}; migrate to predictor-core==2.2.0 and remove vendor")
    return (
        1
        if any(
            manifest(c / "vendor" / "predictor_core")["aggregate"] != canonical["aggregate"]
            for c in found
        )
        else 0
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only legacy vendor auditor")
    parser.add_argument("--audit", "--check", action="store_true", help="audit legacy copies")
    parser.add_argument("--write", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.write:
        parser.error("--write was removed; install the predictor-core wheel instead")
    if not args.audit:
        parser.error("pass --audit")
    return audit()


if __name__ == "__main__":
    raise SystemExit(main())
