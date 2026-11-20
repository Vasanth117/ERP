"""Smoke-check College Admin GET paths referenced from the frontend resolver against FastAPI routes."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "frontend" / "src" / "features" / "college-admin" / "config" / "module-endpoint-resolver.ts"
BACKEND = ROOT / "backend" / "app" / "modules" / "college_admin"


def collect_backend_get_paths() -> set[str]:
    out: set[str] = set()
    for path in BACKEND.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r'@router\.get\(\s*"([^"]+)"', text):
            out.add(m.group(1).split("{")[0].rstrip("/"))
        if path.name == "router.py":
            for m in re.finditer(r'@router\.get\(\s*"([^"]+)"', text):
                out.add(m.group(1).split("{")[0].rstrip("/"))
    return out


def collect_frontend_paths() -> list[str]:
    text = FRONT.read_text(encoding="utf-8")
    paths: list[str] = []
    for m in re.finditer(r'"(/college-admin/[^"?]+)', text):
        paths.append(m.group(1))
    return paths


def main() -> int:
    backend = collect_backend_get_paths()
    missing: list[str] = []
    for raw in collect_frontend_paths():
        # map to path suffix under /college-admin mount
        suffix = raw.removeprefix("/college-admin")
        if not suffix:
            suffix = "/dashboard"
        # strip trailing action segments for param routes
        candidates = [suffix]
        parts = suffix.strip("/").split("/")
        while len(parts) > 1:
            parts.pop()
            candidates.append("/" + "/".join(parts))
        if not any(c.rstrip("/") in backend or c in backend for c in candidates):
            missing.append(raw)
    if missing:
        print("Paths in resolver with no obvious backend GET route:")
        for p in sorted(set(missing)):
            print(" ", p)
        return 1
    print("All resolver paths matched at least one backend GET prefix.")
    return 0


if __name__ == "__main__":
    sys.exit(main())