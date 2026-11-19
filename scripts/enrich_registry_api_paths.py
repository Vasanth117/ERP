"""Attach apiPath/viewType to Figma-derived frames (CA05–CA06) when missing."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAMES_PATH = (
    ROOT / "frontend" / "src" / "features" / "college-admin" / "config" / "college-admin-frames.json"
)

ACADEMICS: dict[str, tuple[str, str]] = {
    "academic-configuration-dashboard": ("dashboard", "/college-admin/academic-config/years"),
    "academic-year-management": ("list", "/college-admin/academic-config/years"),
    "semester-management": ("list", "/college-admin/academic-config/terms"),
    "programme-management": ("list", "/college-admin/academic-config/programmes"),
    "course-configuration": ("form", "/college-admin/academic-config/courses"),
    "curriculum-management": ("form", "/college-admin/academic-config/programmes"),
    "subject-management": ("form", "/college-admin/academic-config/courses"),
    "credit-configuration": ("form", "/college-admin/academic-config/programmes"),
    "regulation-management": ("form", "/college-admin/academic-config/regulations"),
    "grading-system-configuration": ("settings", "/college-admin/academic-config/regulations"),
    "academic-calendar-configuration": ("form", "/college-admin/academic-config/calendars"),
    "batch-section-configuration": ("form", "/college-admin/academic-config/sections"),
    "academic-configuration-history": ("list", "/college-admin/academic-config/configuration-history"),
}

STUDENTS: dict[str, tuple[str, str]] = {
    "student-administration-dashboard": ("dashboard", "/college-admin/student-administration/students"),
    "all-students-list": ("list", "/college-admin/student-administration/students"),
}


def main() -> None:
    data = json.loads(FRAMES_PATH.read_text(encoding="utf-8"))
    updated = 0
    for frame in data["frames"]:
        if frame.get("synthetic"):
            continue
        slug = frame.get("slug", "")
        if frame["module"] == "05" and slug in ACADEMICS and not frame.get("apiPath"):
            vt, path = ACADEMICS[slug]
            frame["viewType"] = vt
            frame["apiPath"] = path
            updated += 1
        if frame["module"] == "06" and slug in STUDENTS and not frame.get("apiPath"):
            vt, path = STUDENTS[slug]
            frame["viewType"] = vt
            frame["apiPath"] = path
            updated += 1
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    FRAMES_PATH.write_text(text, encoding="utf-8")
    (ROOT / "design" / "college-admin-frames.json").write_text(text, encoding="utf-8")
    print(f"Enriched {updated} frame(s) with apiPath/viewType")


if __name__ == "__main__":
    main()