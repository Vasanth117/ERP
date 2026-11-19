"""Set apiPath and viewType on CA 07–24 frames from Figma registry + backend route map."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAMES_PATH = (
    ROOT / "frontend" / "src" / "features" / "college-admin" / "config" / "college-admin-frames.json"
)

MODULE_LIST_GET: dict[str, str] = {
    "07": "/college-admin/faculty-administration/faculty",
    "08": "/college-admin/attendance-administration/policies",
    "09": "/college-admin/examination-administration/marks/pending",
    "10": "/college-admin/finance-administration/fee-structures",
    "11": "/college-admin/hr-administration/leave/pending",
    "12": "/college-admin/library-administration/circulation",
    "13": "/college-admin/hostel-administration/waiting-list",
    "14": "/college-admin/communication-administration/deliveries/failed",
    "15": "/college-admin/lms-administration/course-mappings",
    "16": "/college-admin/reports-analytics/definitions",
    "17": "/college-admin/workflow-administration/pending",
    "18": "/college-admin/security-administration/audit-logs",
    "19": "/college-admin/data-import/templates",
    "20": "/college-admin/integration-administration/integrations",
    "21": "/college-admin/helpdesk/tickets",
    "22": "/college-admin/finance-extensions/budgets",
    "23": "/college-admin/operations-extensions/assets",
    "24": "/college-admin/dashboard",
}

SLUG_ENDPOINT: dict[str, str] = {
    # CA 07
    "faculty-directory": "/college-admin/faculty-administration/faculty",
    "employee-directory": "/college-admin/faculty-administration/faculty",
    "faculty-employee-dashboard": "/college-admin/faculty-administration/faculty",
    # CA 08
    "attendance-dashboard": "/college-admin/attendance-administration/summaries/departments",
    "department-attendance-summary": "/college-admin/attendance-administration/summaries/departments",
    "missing-attendance-sessions": "/college-admin/attendance-administration/submissions/missing",
    # add high-value slugs as needed
}


def infer_view_type(slug: str, title: str) -> str:
    s = f"{slug} {title}".lower()
    if "dashboard" in s or s.startswith("overview"):
        return "dashboard"
    if any(k in s for k in ("report", "analytics", "summary", "compliance")):
        return "report"
    if any(
        k in s
        for k in (
            "add ",
            "create",
            "edit",
            "new ",
            "configuration",
            "assign",
            "allocation",
            "publish",
            "import",
            "verification",
            "settings",
        )
    ):
        return "form"
    if any(k in s for k in ("profile", "detail", "history", "view ")):
        return "detail"
    return "list"


def main() -> None:
    data = json.loads(FRAMES_PATH.read_text(encoding="utf-8"))
    updated = 0
    for frame in data["frames"]:
        mod = frame["module"]
        if mod < "07":
            continue
        slug = frame.get("slug", "")
        if slug in SLUG_ENDPOINT:
            path = SLUG_ENDPOINT[slug]
        else:
            path = MODULE_LIST_GET.get(mod, "/college-admin/dashboard")
        vt = infer_view_type(slug, frame.get("title", ""))
        if frame.get("apiPath") != path or frame.get("viewType") != vt:
            frame["apiPath"] = path
            frame["viewType"] = vt
            updated += 1
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    FRAMES_PATH.write_text(text, encoding="utf-8")
    (ROOT / "design" / "college-admin-frames.json").write_text(text, encoding="utf-8")
    print(f"Updated apiPath/viewType on {updated} frame(s) (CA 07–24)")


if __name__ == "__main__":
    main()