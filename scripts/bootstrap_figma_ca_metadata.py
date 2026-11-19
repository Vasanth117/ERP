"""Copy cached Figma MCP XML dumps into design/_figma_ca_metadata/."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
META = ROOT / "design" / "_figma_ca_metadata"
AGENT_TOOLS = Path.home() / ".cursor/projects/e-ERPSYSTEM/agent-tools"


def main() -> None:
    META.mkdir(parents=True, exist_ok=True)
    copied = 0
    if AGENT_TOOLS.is_dir():
        for src in sorted(AGENT_TOOLS.glob("*.txt")):
            text = src.read_text(encoding="utf-8", errors="ignore")
            if 'name="CA ' not in text:
                continue
            dest = META / f"agent-tools-{src.name}"
            if not dest.exists() or dest.stat().st_mtime < src.stat().st_mtime:
                shutil.copy2(src, dest)
                copied += 1
    print(f"Metadata folder: {META} ({copied} file(s) updated)")


if __name__ == "__main__":
    main()