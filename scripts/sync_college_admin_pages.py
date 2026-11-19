"""One command: Figma registry + synthetic catalog + Next.js page.tsx generation."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def run(rel: str) -> None:
    script = ROOT / rel
    print(f"\n--- {rel} ---")
    subprocess.check_call([PY, str(script)], cwd=ROOT)


def main() -> None:
    run("scripts/bootstrap_figma_ca_metadata.py")
    run("scripts/build_college_admin_frame_registry.py")
    run("scripts/synthesize_ca_screens.py")
    run("scripts/enrich_registry_api_paths.py")
    run("scripts/generate_college_admin_app_routes.py")
    print("\nDone. Restart or refresh the Next.js dev server if it was already running.")


if __name__ == "__main__":
    main()