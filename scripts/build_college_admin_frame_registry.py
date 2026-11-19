"""Extract CA NN.MM screen frames from Figma metadata XML and emit registry + Next routes."""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
META_DIR = ROOT / "design" / "_figma_ca_metadata"
REGISTRY_MIRROR = (
    ROOT
    / "frontend"
    / "src"
    / "features"
    / "college-admin"
    / "config"
    / "college-admin-frames.json"
)
DEFAULT_META = (
    Path.home()
    / ".cursor/projects/e-ERPSYSTEM/agent-tools/7c00a35b-093e-4aa7-ad2f-970f7bedca1c.txt"
)

MODULE_SLUG = {
    "01": ("dashboard", "dashboard"),
    "02": ("institution", "institution"),
    "03": ("users", "users"),
    "04": ("organization", "organization"),
    "05": ("academics", "academics"),
    "06": ("students", "students"),
    "07": ("faculty", "faculty"),
    "08": ("attendance", "attendance"),
    "09": ("examinations", "examinations"),
    "10": ("finance", "finance"),
    "11": ("hr", "hr"),
    "12": ("library", "library"),
    "13": ("hostel", "hostel"),
    "14": ("communication", "communication"),
    "15": ("lms", "lms"),
    "16": ("reports", "reports"),
    "17": ("approvals", "approvals"),
    "18": ("security", "security"),
    "19": ("data-import", "data-import"),
    "20": ("integrations", "integrations"),
    "21": ("helpdesk", "helpdesk"),
    "22": ("finance-extensions", "finance-extensions"),
    "23": ("operations", "operations"),
    "24": ("shared", "shared"),
}


def slugify_title(title: str) -> str:
    t = title.lower()
    t = re.sub(r"[^a-z0-9]+", "-", t)
    return t.strip("-")


def frame_slug(name: str) -> tuple[str, str, str, str]:
    """Return module_num, screen_num, title_suffix, url_slug."""
    m = re.match(r"CA (\d{2})\.(\d{2})\s*[–-]\s*(.+)", name)
    if not m:
        raise ValueError(f"Unexpected frame name: {name}")
    mod, screen, title = m.group(1), m.group(2), m.group(3).strip()
    return mod, screen, title, slugify_title(title)


def route_for(mod: str, screen: str, title_slug: str) -> str:
    base, _ = MODULE_SLUG[mod]
    if mod == "01" and screen == "01":
        return "/college-admin/dashboard"
    if mod == "01":
        return f"/college-admin/dashboard/{title_slug}"
    if mod == "02" and title_slug == "institution-profile":
        return "/college-admin/institution/profile"
    if mod == "02":
        known = {
            "institution-information": "/college-admin/institution/information",
            "college-logo-branding": "/college-admin/institution/branding",
            "campus-management-dashboard": "/college-admin/institution/campuses",
            "academic-institution-settings": "/college-admin/institution/academic-settings",
            "institutional-policies": "/college-admin/institution/policies",
            "academic-year-configuration": "/college-admin/institution/academic-year",
            "institutional-calendar-settings": "/college-admin/institution/calendar",
            "campus-configuration-history": "/college-admin/institution/configuration-history",
        }
        if title_slug in known:
            return known[title_slug]
        if "campus-details" in title_slug:
            return "/college-admin/institution/campuses/[campusId]"
        if "campus-address" in title_slug:
            return "/college-admin/institution/campuses/[campusId]/contact"
        return f"/college-admin/institution/{title_slug}"
    return f"/college-admin/{base}/{title_slug}"


def parse_frames(metadata_path: Path) -> list[dict]:
    text = metadata_path.read_text(encoding="utf-8", errors="ignore")
    pat = re.compile(r'<frame id="([^"]+)" name="(CA \d+\.\d+[^"]+)"')
    frames: list[dict] = []
    seen_names: set[str] = set()
    for frame_id, raw_name in pat.findall(text):
        name = html.unescape(raw_name)
        if name in seen_names:
            continue
        seen_names.add(name)
        mod, screen, title, title_slug = frame_slug(name)
        base, module_key = MODULE_SLUG.get(mod, ("other", "other"))
        frames.append(
            {
                "figmaNodeId": frame_id,
                "name": name,
                "module": mod,
                "screen": screen,
                "moduleKey": module_key,
                "title": title,
                "slug": title_slug,
                "route": route_for(mod, screen, title_slug),
            }
        )
    frames.sort(key=lambda f: (f["module"], f["screen"]))
    return frames


def merge_synthetic_catalog(figma_frames: list[dict]) -> list[dict]:
    """Keep API-bound catalog entries when Figma XML only covers CA01–CA06."""
    if not REGISTRY_MIRROR.is_file():
        return figma_frames
    try:
        previous = json.loads(REGISTRY_MIRROR.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return figma_frames
    keys = {(f["module"], f["screen"]) for f in figma_frames}
    merged = list(figma_frames)
    kept = 0
    for frame in previous.get("frames", []):
        if not frame.get("synthetic"):
            continue
        key = (frame["module"], frame["screen"])
        if key in keys:
            continue
        merged.append(frame)
        keys.add(key)
        kept += 1
    merged.sort(key=lambda f: (f["module"], f["screen"]))
    if kept:
        print(f"Preserved {kept} synthetic catalog frame(s) (CA06.03+ / CA07–CA24)")
    return merged


def write_registry(frames: list[dict]) -> Path:
    payload = {
        "source": "Figma metadata",
        "frameCount": len(frames),
        "frames": frames,
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    out = ROOT / "design" / "college-admin-frames.json"
    out.write_text(text, encoding="utf-8")
    mirror = (
        ROOT
        / "frontend"
        / "src"
        / "features"
        / "college-admin"
        / "config"
        / "college-admin-frames.json"
    )
    mirror.write_text(text, encoding="utf-8")
    return out


def collect_metadata_paths() -> list[Path]:
    paths: list[Path] = []
    if META_DIR.is_dir():
        paths.extend(sorted(META_DIR.glob("*.txt")))
        paths.extend(sorted(META_DIR.glob("agent-tools-*.txt")))
    if DEFAULT_META.is_file() and DEFAULT_META not in paths:
        paths.append(DEFAULT_META)
    extra = Path.home() / ".cursor/projects/e-ERPSYSTEM/agent-tools"
    if extra.is_dir():
        for p in sorted(extra.glob("*.txt")):
            if p not in paths:
                paths.append(p)
    return paths


def main() -> None:
    if len(sys.argv) > 1:
        paths = [Path(sys.argv[1])]
    else:
        paths = collect_metadata_paths()
    if not paths:
        raise SystemExit("No Figma metadata files found")
    merged: list[dict] = []
    seen: set[str] = set()
    for meta in paths:
        if not meta.is_file():
            continue
        for frame in parse_frames(meta):
            key = frame["name"]
            if key in seen:
                continue
            seen.add(key)
            merged.append(frame)
    merged = merge_synthetic_catalog(merged)
    out = write_registry(merged)
    print(f"Wrote {out} ({len(merged)} frames) from {len(paths)} metadata file(s)")
    print(
        "Next: py scripts/synthesize_ca_screens.py  # fill gaps until Figma XML is exported\n"
        "      py scripts/generate_college_admin_app_routes.py"
    )


if __name__ == "__main__":
    main()