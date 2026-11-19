"""Generate Next.js page.tsx for each Figma frame route in college-admin-frames.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAMES = (
    ROOT
    / "frontend"
    / "src"
    / "features"
    / "college-admin"
    / "config"
    / "college-admin-frames.json"
)
APP = ROOT / "frontend" / "src" / "app"

SKIP_PREFIXES = (
    "/college-admin/dashboard",
    "/college-admin/institution",
)

PAGE_TEMPLATE = '''import {{ CollegeAdminFigmaScreen }} from "@/features/college-admin/components/college-admin-figma-screen";

export default function Page() {{
  return (
    <CollegeAdminFigmaScreen
      moduleKey="{module_key}"
      slug="{slug}"
      figmaNodeId="{figma_id}"
      title={title!r}
    />
  );
}}
'''


def main() -> None:
    payload = json.loads(FRAMES.read_text(encoding="utf-8"))
    created = 0
    for frame in payload["frames"]:
        route = frame["route"]
        if "[campusId]" in route or any(route.startswith(p) for p in SKIP_PREFIXES):
            continue
        rel = route.removeprefix("/").replace("[", "").replace("]", "")
        page_dir = APP / rel
        page_dir.mkdir(parents=True, exist_ok=True)
        page_file = page_dir / "page.tsx"
        content = PAGE_TEMPLATE.format(
            module_key=frame["moduleKey"],
            slug=frame["slug"],
            figma_id=frame["figmaNodeId"],
            title=frame["title"],
        )
        page_file.write_text(content, encoding="utf-8")
        created += 1

    # Module index redirects (first screen .01 per moduleKey)
    by_module: dict[str, str] = {}
    for frame in sorted(payload["frames"], key=lambda f: (f["moduleKey"], f["screen"])):
        key = frame["moduleKey"]
        if key not in by_module and frame.get("screen") == "01":
            by_module[key] = frame["route"]
    for folder, target in by_module.items():
        idx = APP / "college-admin" / folder / "page.tsx"
        idx.parent.mkdir(parents=True, exist_ok=True)
        idx.write_text(
            f'import {{ redirect }} from "next/navigation";\n'
            f'export default function Page() {{ redirect("{target}"); }}\n',
            encoding="utf-8",
        )

    print(f"Generated/updated {created} frame pages")


if __name__ == "__main__":
    main()