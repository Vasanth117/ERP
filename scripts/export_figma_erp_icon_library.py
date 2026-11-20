"""Export ERP Icon Library (Lucide) from Figma into frontend TSX components.

Figma page: ERP Icon Library (Lucide) — canvas 354:213, frame 354:214.
Output: frontend/src/components/icons/erp/generated/*.tsx + manifest + index.

Requires FIGMA_ACCESS_TOKEN in environment or .env at repo root.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE_KEY = "Hy7qeZdVNmzD6PN0ZkgBfK"
LIBRARY_FRAME = "354:214"
OUT_DIR = ROOT / "frontend" / "src" / "components" / "icons" / "erp"
GENERATED = OUT_DIR / "generated"
MANIFEST = OUT_DIR / "manifest.json"
PROGRESS = OUT_DIR / "export-progress.json"
BATCH_SIZE = 50


def load_token() -> str:
    token = os.environ.get("FIGMA_ACCESS_TOKEN", "").strip()
    if token:
        return token
    env_file = ROOT / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("FIGMA_ACCESS_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("FIGMA_ACCESS_TOKEN missing")


def figma_get(path: str, token: str) -> dict:
    url = f"https://api.figma.com/v1{path}"
    req = urllib.request.Request(url, headers={"X-Figma-Token": token})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 503) and attempt < 5:
                time.sleep(2 ** attempt)
                continue
            raise


def fetch_library_tree(token: str) -> dict:
    return figma_get(
        f"/files/{FILE_KEY}/nodes?ids={urllib.parse.quote(LIBRARY_FRAME)}&depth=8",
        token,
    )


def collect_icons(doc: dict) -> list[dict]:
    icons: list[dict] = []

    def component_child(tile: dict) -> dict | None:
        for child in tile.get("children") or []:
            if child.get("type") == "COMPONENT" and str(child.get("name", "")).startswith(
                "lucide/"
            ):
                return child
        return None

    def walk(node: dict, category: str | None = None) -> None:
        name = node.get("name", "")
        if node.get("type") == "FRAME" and name.startswith("Section · "):
            category = name.replace("Section · ", "", 1)
        if node.get("type") == "FRAME" and name.startswith("Grid · "):
            category = category or name.replace("Grid · ", "", 1)
            for tile in node.get("children") or []:
                if tile.get("type") != "FRAME":
                    continue
                slug = tile.get("name", "").strip()
                if not slug or not re.match(r"^[a-z0-9][a-z0-9-]*$", slug):
                    continue
                comp = component_child(tile)
                if not comp:
                    continue
                icons.append(
                    {
                        "name": slug,
                        "category": category,
                        "nodeId": comp["id"],
                        "componentName": comp.get("name", ""),
                    }
                )
            return
        for child in node.get("children") or []:
            walk(child, category)

    walk(doc)
    by_name = {i["name"]: i for i in icons}
    return [by_name[k] for k in sorted(by_name)]


def pascal_case(slug: str) -> str:
    return "".join(part.capitalize() for part in slug.split("-")) + "Icon"


def export_svgs(token: str, icons: list[dict]) -> dict[str, str]:
    urls: dict[str, str] = {}
    ids = [i["nodeId"] for i in icons]
    batch_starts = list(range(0, len(ids), BATCH_SIZE))
    for bi, start in enumerate(batch_starts, start=1):
        batch = ids[start : start + BATCH_SIZE]
        id_param = ",".join(urllib.parse.quote(i, safe=":,") for i in batch)
        payload = figma_get(
            f"/images/{FILE_KEY}?ids={id_param}&format=svg&svg_outline_text=false&svg_include_id=false",
            token,
        )
        images = payload.get("images") or {}
        urls.update(images)
        print(f"  Figma image batch {bi}/{len(batch_starts)} ({len(images)} urls)", flush=True)
        time.sleep(0.4)
    return urls


def download_text(url: str) -> str:
    if not url:
        return ""
    req = urllib.request.Request(url)
    for attempt in range(10):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return resp.read().decode("utf-8")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            if attempt < 9:
                time.sleep(min(2 ** attempt, 45))
                continue
            return ""
    return ""


def normalize_svg(svg: str) -> tuple[str, str]:
    svg = svg.strip()
    viewbox_m = re.search(r'viewBox="([^"]+)"', svg)
    viewbox = viewbox_m.group(1) if viewbox_m else "0 0 24 24"
    inner_m = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.DOTALL | re.IGNORECASE)
    inner = inner_m.group(1).strip() if inner_m else svg
    inner = re.sub(r"<script[\s\S]*?</script>", "", inner, flags=re.IGNORECASE)
    for attr in (
        "stroke",
        "stroke-width",
        "stroke-linecap",
        "stroke-linejoin",
        "fill",
    ):
        inner = re.sub(rf'\s{attr}="[^"]*"', "", inner)
    return viewbox, inner


def write_tsx(icon: dict, viewbox: str, inner: str) -> None:
    comp = pascal_case(icon["name"])
    path = GENERATED / f"{icon['name']}.tsx"
    content = f'''import type {{ SVGProps }} from "react";

import {{ cn }} from "@/lib/utils";

export function {comp}({{ className, ...props }}: SVGProps<SVGSVGElement>) {{
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="{viewbox}"
      fill="none"
      stroke="currentColor"
      strokeWidth={{2}}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={{cn("size-6 shrink-0", className)}}
      aria-hidden
      {{...props}}
    >
{indent_svg(inner, 6)}
    </svg>
  );
}}
'''
    path.write_text(content, encoding="utf-8")


def indent_svg(inner: str, spaces: int) -> str:
    pad = " " * spaces
    lines = [line.rstrip() for line in inner.splitlines() if line.strip()]
    return "\n".join(pad + line for line in lines) + ("\n" if lines else "")


def fix_existing_tsx() -> int:
    """Strip duplicate kebab-case stroke attrs from icon paths (not the root <svg>)."""
    fixed = 0
    for path in GENERATED.glob("*.tsx"):
        text = path.read_text(encoding="utf-8")
        parts = text.split("<svg", 1)
        if len(parts) != 2:
            continue
        head, rest = parts
        body, tail = rest.split(">", 1)
        inner = tail.rsplit("</svg>", 1)[0]
        footer = tail[len(inner) :]
        for attr in (
            "stroke-width",
            "stroke-linecap",
            "stroke-linejoin",
            "stroke",
            "fill",
        ):
            inner = re.sub(rf"\s{attr}=\"[^\"]*\"", "", inner)
        if 'fill="none"' not in body:
            body = body.replace(
                'viewBox="0 0 24 24"',
                'viewBox="0 0 24 24"\n      fill="none"\n      stroke="currentColor"',
                1,
            )
        updated = head + "<svg" + body + ">" + inner + footer
        updated = re.sub(r"\n\s*\n\s*strokeWidth", "\n      strokeWidth", updated)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            fixed += 1
    return fixed


def save_progress(done: int, total: int, last: str) -> None:
    PROGRESS.write_text(
        json.dumps({"done": done, "total": total, "last": last}, indent=2),
        encoding="utf-8",
    )


def write_index(icons: list[dict]) -> None:
    lines = [
        "/** Auto-generated from Figma ERP Icon Library (Lucide). Do not edit by hand. */",
        "",
    ]
    for icon in icons:
        comp = pascal_case(icon["name"])
        lines.append(f'export {{ {comp} }} from "./generated/{icon["name"]}";')
    (OUT_DIR / "index.ts").write_text("\n".join(lines) + "\n", encoding="utf-8")

    names = [i["name"] for i in icons]
    registry = (
        "/** Auto-generated icon name union. */\n"
        f"export type ErpIconName =\n  | "
        + "\n  | ".join(f'"{n}"' for n in names)
        + ";\n"
    )
    (OUT_DIR / "names.ts").write_text(registry, encoding="utf-8")

    reg_lines = [
        "/** Auto-generated registry — slug to component. */",
        "import type { ComponentType, SVGProps } from \"react\";",
        "",
        "import type { ErpIconName } from \"./names\";",
        "",
    ]
    for icon in icons:
        comp = pascal_case(icon["name"])
        reg_lines.append(f'import {{ {comp} }} from "./generated/{icon["name"]}";')
    reg_lines.append("")
    reg_lines.append(
        "export const erpIconRegistry: Record<ErpIconName, ComponentType<SVGProps<SVGSVGElement>>> = {"
    )
    for icon in icons:
        comp = pascal_case(icon["name"])
        reg_lines.append(f'  "{icon["name"]}": {comp},')
    reg_lines.append("};")
    reg_lines.append("")
    (OUT_DIR / "registry.ts").write_text("\n".join(reg_lines) + "\n", encoding="utf-8")


def write_base_files() -> None:
    base = OUT_DIR / "erp-icon.tsx"
    if base.is_file():
        return
    base.write_text(
        '''import type { SVGProps } from "react";

import type { ErpIconName } from "./names";
import { erpIconRegistry } from "./registry";

export type ErpIconProps = SVGProps<SVGSVGElement> & {
  name: ErpIconName;
};

/** Render an icon from the ERP Figma icon library by Lucide slug (e.g. `circle-user`). */
export function ErpIcon({ name, ...props }: ErpIconProps) {
  const Icon = erpIconRegistry[name];
  if (!Icon) return null;
  return <Icon {...props} />;
}
''',
        encoding="utf-8",
    )

    readme = OUT_DIR / "README.md"
    if not readme.is_file():
        readme.write_text(
            """# ERP icon library (from Figma)

Source: Figma page **ERP Icon Library (Lucide)** (`354:213`).

- Per-icon components live in `generated/*.tsx` (kebab-case filenames, PascalCase exports).
- Regenerate after Figma updates: `py -3 scripts/export_figma_erp_icon_library.py` from repo root.

```tsx
import { ErpIcon } from "@/components/icons/erp/erp-icon";
import { CircleUserIcon } from "@/components/icons/erp";
```
""",
            encoding="utf-8",
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export Figma ERP icon library to TSX")
    parser.add_argument(
        "--refresh-manifest",
        action="store_true",
        help="Re-fetch icon manifest from Figma (slow)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max pending icons to export this run (0 = all pending)",
    )
    parser.add_argument(
        "--index-only",
        action="store_true",
        help="Regenerate index/registry from manifest + existing TSX only",
    )
    parser.add_argument(
        "--fix-existing",
        action="store_true",
        help="Repair root svg attrs and strip duplicate path stroke attrs",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    token = load_token()
    GENERATED.mkdir(parents=True, exist_ok=True)

    if args.fix_existing:
        n = fix_existing_tsx()
        print(f"Fixed {n} existing TSX files")
        if args.index_only:
            args.index_only = True
        elif n and not args.index_only:
            pass

    if args.refresh_manifest or not MANIFEST.is_file():
        tree = fetch_library_tree(token)
        doc = tree["nodes"][LIBRARY_FRAME]["document"]
        icons = collect_icons(doc)
        print(f"Collected {len(icons)} icons from Figma")
        MANIFEST.write_text(json.dumps(icons, indent=2), encoding="utf-8")
    else:
        icons = json.loads(MANIFEST.read_text(encoding="utf-8"))
        print(f"Loaded manifest: {len(icons)} icons")

    def on_disk(name: str) -> bool:
        return (GENERATED / f"{name}.tsx").is_file()

    completed = [i for i in icons if on_disk(i["name"])]
    pending = [i for i in icons if not on_disk(i["name"])]
    print(f"Completed: {len(completed)} | Pending: {len(pending)}")

    missing: list[str] = []
    if not args.index_only and pending:
        work = pending[: args.limit] if args.limit > 0 else pending
        print(f"Exporting {len(work)} icons this run…")
        for batch_start in range(0, len(work), BATCH_SIZE):
            batch = work[batch_start : batch_start + BATCH_SIZE]
            url_map = export_svgs(token, batch)
            for idx, icon in enumerate(batch, start=batch_start + 1):
                url = url_map.get(icon["nodeId"])
                if not url:
                    missing.append(icon["name"])
                    continue
                svg = download_text(url)
                if not svg:
                    missing.append(icon["name"])
                    continue
                viewbox, inner = normalize_svg(svg)
                write_tsx(icon, viewbox, inner)
                if idx % 25 == 0 or idx == len(work):
                    on_disk_n = len([i for i in icons if on_disk(i["name"])])
                    save_progress(on_disk_n, len(icons), icon["name"])
                    print(f"  wrote {idx}/{len(work)} — on disk {on_disk_n}", flush=True)
                time.sleep(0.03)

    completed = [i for i in icons if on_disk(i["name"])]
    write_index(completed if len(completed) < len(icons) else icons)
    write_base_files()

    still_pending = len(icons) - len(completed)
    if missing:
        report = OUT_DIR / "export-missing.txt"
        report.write_text("\n".join(missing), encoding="utf-8")
        print(f"Failed this run: {len(missing)} — see {report}")

    print(f"Total TSX on disk: {len(completed)}/{len(icons)}")
    if still_pending:
        print(f"Re-run: py -3 scripts/export_figma_erp_icon_library.py")
        sys.exit(0 if still_pending == 0 else 2)
    print("Export complete.")


if __name__ == "__main__":
    main()