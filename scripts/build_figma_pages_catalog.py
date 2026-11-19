"""Regenerate design/figma-pages.json from Figma MCP page list (stdin JSON array)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

FILE_KEY = "Hy7qeZdVNmzD6PN0ZkgBfK"
FILE_NAME = "ERP"

PREFIX_MAP = {
    "00": "platform",
    "01": "platform",
    "02": "platform",
    "03": "platform",
    "04": "platform",
    "05": "platform",
    "06": "platform",
    "07": "platform",
    "08": "platform",
    "09": "platform",
    "10": "platform",
    "11": "platform",
    "12": "platform",
    "CA": "collegeAdmin",
    "DA": "departmentAdmin",
    "FP": "facultyPortal",
    "PP": "parentPortal",
    "LP": "library",
    "EX": "examination",
    "HR": "hr",
    "FN": "finance",
    "ST": "studentPortal",
    "HA": "hostel",
}


def figma_url(node_id: str) -> str:
    slug = node_id.replace(":", "-")
    return f"https://www.figma.com/design/{FILE_KEY}/{FILE_NAME}?node-id={slug}"


def module_key(name: str) -> str:
    m = re.match(r"^(\d{2}|CA|DA|FP|PP|LP|EX|HR|FN|ST|HA)\b", name)
    if m:
        return PREFIX_MAP.get(m.group(1), "other")
    lower = name.lower()
    if "library" in lower:
        return "library"
    if "exam" in lower:
        return "examination"
    if "hr" in lower:
        return "hr"
    return "legacyCanvas"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    default_raw = root / "design" / "_figma_pages_raw.json"
    if not sys.stdin.isatty():
        pages = json.load(sys.stdin)
    elif default_raw.is_file():
        payload = json.loads(default_raw.read_text(encoding="utf-8"))
        pages = payload if isinstance(payload, list) else payload.get("pages", [])
    else:
        raise SystemExit("Pass pages JSON on stdin or write design/_figma_pages_raw.json")
    by_module: dict[str, list[dict]] = {}
    for p in pages:
        if p.get("type") != "PAGE":
            continue
        key = module_key(p["name"])
        entry = {
            "id": p["id"],
            "name": p["name"],
            "url": figma_url(p["id"]),
        }
        by_module.setdefault(key, []).append(entry)

    catalog = {
        "fileKey": FILE_KEY,
        "fileName": FILE_NAME,
        "pageCount": sum(len(v) for v in by_module.values()),
        "modules": {
            k: {"pages": sorted(v, key=lambda x: x["name"])}
            for k, v in sorted(by_module.items())
        },
        "moduleOrder": [
            "platform",
            "collegeAdmin",
            "departmentAdmin",
            "facultyPortal",
            "studentPortal",
            "parentPortal",
            "library",
            "examination",
            "hr",
            "finance",
            "hostel",
            "legacyCanvas",
            "other",
        ],
    }
    out = Path(__file__).resolve().parents[1] / "design" / "figma-pages.json"
    out.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out} ({catalog['pageCount']} pages)")


if __name__ == "__main__":
    main()