"""Create package markers and planned module routers."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PACKAGES = [
    "app/core",
    "app/common",
    "app/api",
    "app/api/v1",
    "app/modules",
    "app/modules/auth",
    "app/modules/tenants",
    "app/modules/platform",
    "app/modules/users",
    "app/modules/audit",
    "app/tasks",
    "app/cli",
]

MODULES = {
    "academics": "Programs, courses, semesters, and class sections.",
    "students": "Student records, enrollment, and academic identity.",
    "faculty": "Faculty profiles, assignments, and workload.",
    "attendance": "Class attendance capture and corrections.",
    "examinations": "Exam schedules, marks, and results.",
    "finance": "Fees, payments, and financial records.",
    "hr": "Staff records and HR operations.",
    "library": "Library catalog and circulation.",
    "hostel": "Hostel allocation and residence operations.",
}


def main() -> None:
    for package in PACKAGES:
        path = ROOT / package / "__init__.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text('"""Package marker."""\n', encoding="utf-8")

    for name, summary in MODULES.items():
        folder = ROOT / "app" / "modules" / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "__init__.py").write_text(f'"""{name} module."""\n', encoding="utf-8")
        title = "HR" if name == "hr" else name.replace("_", " ").title()
        router = (
            f'"""{title} module.\n\n'
            f"{summary}\n"
            "Endpoints for this module will be added as the domain is implemented.\n"
            '"""\n\n'
            "from fastapi import APIRouter\n\n"
            "router = APIRouter()\n"
        )
        (folder / "router.py").write_text(router, encoding="utf-8")
    print("packages ready")


if __name__ == "__main__":
    main()
