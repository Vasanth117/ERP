"""Fetch CA 01–24 canvas trees from Figma REST API and write metadata for the registry builder.

Requires environment variable FIGMA_ACCESS_TOKEN (Personal access token).
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
META = ROOT / "design" / "_figma_ca_metadata"
PAGES = ROOT / "design" / "figma-pages.json"
FILE_KEY = "Hy7qeZdVNmzD6PN0ZkgBfK"
CA_FRAME = re.compile(r"^CA \d{2}\.\d{2}\s*[–-]")


def fetch_nodes(token: str, node_id: str) -> dict:
    url = f"https://api.figma.com/v1/files/{FILE_KEY}/nodes?ids={node_id}&depth=6"
    req = urllib.request.Request(url, headers={"X-Figma-Token": token})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def walk(node: dict, out: list[tuple[str, str]]) -> None:
    name = node.get("name", "")
    if node.get("type") == "FRAME" and CA_FRAME.match(name):
        out.append((node["id"], name))
    for child in node.get("children") or []:
        walk(child, out)


def write_xml_snippet(path: Path, frames: list[tuple[str, str]]) -> None:
    lines = ['<canvas id="export" name="REST export">']
    for fid, name in frames:
        safe = name.replace('"', "&quot;")
        lines.append(f'  <frame id="{fid}" name="{safe}" />')
    lines.append("</canvas>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_token() -> str:
    token = os.environ.get("FIGMA_ACCESS_TOKEN", "").strip()
    if token:
        return token
    env_file = ROOT / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("FIGMA_ACCESS_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def main() -> None:
    token = load_token()
    if not token:
        raise SystemExit(
            "Set FIGMA_ACCESS_TOKEN in the environment or in e:\\ERPSYSTEM\\.env, then re-run."
        )
    pages = json.loads(PAGES.read_text(encoding="utf-8"))["modules"]["collegeAdmin"]["pages"]
    META.mkdir(parents=True, exist_ok=True)
    total = 0
    for page in pages:
        node_id = page["id"]
        label = re.sub(r"[^\w.-]+", "_", page["name"])[:60]
        try:
            payload = fetch_nodes(token, node_id)
        except urllib.error.HTTPError as exc:
            print(f"Skip {label}: HTTP {exc.code}", file=sys.stderr)
            continue
        doc = payload.get("nodes", {}).get(node_id, {}).get("document")
        if not doc:
            print(f"Skip {label}: empty document", file=sys.stderr)
            continue
        frames: list[tuple[str, str]] = []
        walk(doc, frames)
        raw = META / f"{label}.json"
        raw.write_text(json.dumps(doc, indent=2)[:500_000], encoding="utf-8")
        xml = META / f"{label}.txt"
        write_xml_snippet(xml, frames)
        total += len(frames)
        print(f"{label}: {len(frames)} CA frame(s)")
    print(f"Wrote metadata to {META}; {total} frame name(s) total")


if __name__ == "__main__":
    main()