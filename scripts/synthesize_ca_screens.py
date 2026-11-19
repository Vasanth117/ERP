"""Append CA06.03+ and CA07–CA24 screen catalog (API-bound) to college-admin-frames.json."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAMES_PATH = (
    ROOT / "frontend" / "src" / "features" / "college-admin" / "config" / "college-admin-frames.json"
)

# (screen, title, slug, viewType, apiPath)
MODULES: dict[str, tuple[str, str, list[tuple[str, str, str, str, str]]]] = {
    "06": (
        "students",
        "75:11520",
        [
            ("03", "Admissions List", "admissions-list", "list", "/college-admin/student-administration/admissions"),
            ("04", "Student Details", "student-details", "detail", "/college-admin/student-administration/students"),
            ("05", "Create Student", "create-student", "form", "/college-admin/student-administration/students"),
            ("06", "Academic History", "academic-history", "detail", "/college-admin/student-administration/students"),
            ("07", "Bulk Student Import", "bulk-student-import", "form", "/college-admin/student-administration/students/bulk"),
            ("08", "Profile Corrections", "profile-corrections", "form", "/college-admin/student-administration/profile-corrections/decide"),
            ("09", "Section Transfer Review", "section-transfer-review", "list", "/college-admin/student-administration/section-transfer-requests"),
        ],
    ),
    "07": (
        "faculty",
        "159:2198",
        [
            ("01", "Faculty & Employee Dashboard", "faculty-employee-dashboard", "dashboard", "/college-admin/faculty-administration/faculty"),
            ("02", "All Faculty List", "all-faculty-list", "list", "/college-admin/faculty-administration/faculty"),
            ("03", "Faculty Details", "faculty-details", "detail", "/college-admin/faculty-administration/faculty"),
            ("04", "Create Faculty", "create-faculty", "form", "/college-admin/faculty-administration/faculty"),
            ("05", "Workload Management", "workload-management", "detail", "/college-admin/faculty-administration/faculty"),
            ("06", "Teaching Assignments", "teaching-assignments", "form", "/college-admin/faculty-administration/faculty"),
            ("07", "Faculty Transfer", "faculty-transfer", "form", "/college-admin/faculty-administration/faculty"),
            ("08", "Faculty Documents", "faculty-documents", "form", "/college-admin/faculty-administration/faculty"),
            ("09", "Faculty History", "faculty-history", "detail", "/college-admin/faculty-administration/faculty"),
            ("10", "Bulk Faculty Import", "bulk-faculty-import", "form", "/college-admin/faculty-administration/faculty/bulk"),
        ],
    ),
    "08": (
        "attendance",
        "159:6843",
        [
            ("01", "Attendance Administration Dashboard", "attendance-dashboard", "dashboard", "/college-admin/attendance-administration/summaries/departments"),
            ("02", "Attendance Policies", "attendance-policies", "list", "/college-admin/attendance-administration/policies"),
            ("03", "Department Summaries", "department-summaries", "list", "/college-admin/attendance-administration/summaries/departments"),
            ("04", "Missing Submissions", "missing-submissions", "list", "/college-admin/attendance-administration/submissions/missing"),
            ("05", "Correction Requests", "correction-requests", "list", "/college-admin/attendance-administration/corrections"),
            ("06", "Attendance Shortages", "attendance-shortages", "list", "/college-admin/attendance-administration/shortages"),
            ("07", "Session History", "session-history", "list", "/college-admin/attendance-administration/history"),
            ("08", "Compliance Reports", "compliance-reports", "report", "/college-admin/attendance-administration/reports/compliance"),
        ],
    ),
    "09": (
        "examinations",
        "159:10707",
        [
            ("01", "Examination Dashboard", "examination-dashboard", "dashboard", "/college-admin/examination-administration/marks/pending"),
            ("02", "Exam Configuration", "exam-configuration", "form", "/college-admin/examination-administration/configurations"),
            ("03", "Exam Seasons", "exam-seasons", "form", "/college-admin/examination-administration/seasons"),
            ("04", "Eligibility Registry", "eligibility-registry", "list", "/college-admin/examination-administration/eligibility"),
            ("05", "Hall Tickets", "hall-tickets", "form", "/college-admin/examination-administration/hall-tickets"),
            ("06", "Pending Marks Review", "pending-marks-review", "list", "/college-admin/examination-administration/marks/pending"),
            ("07", "Results Publication", "results-publication", "form", "/college-admin/examination-administration/results/publish"),
            ("08", "Examination Reports", "examination-reports", "report", "/college-admin/examination-administration/reports"),
        ],
    ),
    "10": (
        "finance",
        "160:2198",
        [
            ("01", "Finance Dashboard", "finance-dashboard", "dashboard", "/college-admin/finance-administration/reports/summary"),
            ("02", "Fee Structures", "fee-structures", "form", "/college-admin/finance-administration/fee-structures"),
            ("03", "Fee Assessments", "fee-assessments", "form", "/college-admin/finance-administration/assessments"),
            ("04", "Transactions", "finance-transactions", "list", "/college-admin/finance-administration/transactions"),
            ("05", "Student Ledger", "student-ledger", "detail", "/college-admin/finance-administration/ledger"),
            ("06", "Concessions", "fee-concessions", "form", "/college-admin/finance-administration/concessions"),
            ("07", "Refunds", "refunds", "form", "/college-admin/finance-administration/refunds"),
            ("08", "Finance Summary Report", "finance-summary-report", "report", "/college-admin/finance-administration/reports/summary"),
        ],
    ),
    "11": (
        "hr",
        "160:7147",
        [
            ("01", "HR Dashboard", "hr-dashboard", "dashboard", "/college-admin/hr-administration/statistics"),
            ("02", "Pending Leave", "pending-leave", "list", "/college-admin/hr-administration/leave/pending"),
            ("03", "Payroll Status", "payroll-status", "report", "/college-admin/hr-administration/payroll/status"),
            ("04", "HR Statistics", "hr-statistics", "report", "/college-admin/hr-administration/statistics"),
            ("05", "HR Summary Report", "hr-summary-report", "report", "/college-admin/hr-administration/reports/summary"),
        ],
    ),
    "12": (
        "library",
        "160:11569",
        [
            ("01", "Library Dashboard", "library-dashboard", "dashboard", "/college-admin/library-administration/reports/summary"),
            ("02", "Circulation", "library-circulation", "list", "/college-admin/library-administration/circulation"),
            ("03", "Library Summary", "library-summary-report", "report", "/college-admin/library-administration/reports/summary"),
        ],
    ),
    "13": (
        "hostel",
        "161:2198",
        [
            ("01", "Hostel Dashboard", "hostel-dashboard", "dashboard", "/college-admin/hostel-administration/reports/occupancy"),
            ("02", "Waiting List", "hostel-waiting-list", "list", "/college-admin/hostel-administration/waiting-list"),
            ("03", "Occupancy Report", "occupancy-report", "report", "/college-admin/hostel-administration/reports/occupancy"),
        ],
    ),
    "14": (
        "communication",
        "161:6941",
        [
            ("01", "Communication Dashboard", "communication-dashboard", "dashboard", "/college-admin/communication-administration/reports/summary"),
            ("02", "Failed Deliveries", "failed-deliveries", "list", "/college-admin/communication-administration/deliveries/failed"),
            ("03", "Communication Summary", "communication-summary", "report", "/college-admin/communication-administration/reports/summary"),
        ],
    ),
    "15": (
        "lms",
        "161:11017",
        [
            ("01", "LMS Dashboard", "lms-dashboard", "dashboard", "/college-admin/lms-administration/statistics"),
            ("02", "LMS Settings", "lms-settings", "settings", "/college-admin/lms-administration/settings"),
            ("03", "Course Mappings", "course-mappings", "list", "/college-admin/lms-administration/course-mappings"),
            ("04", "Content Categories", "content-categories", "list", "/college-admin/lms-administration/content-categories"),
            ("05", "LMS Monitoring", "lms-monitoring", "report", "/college-admin/lms-administration/monitoring"),
            ("06", "LMS Configuration History", "lms-configuration-history", "list", "/college-admin/lms-administration/configuration-history"),
        ],
    ),
    "16": (
        "reports",
        "161:14938",
        [
            ("01", "Analytics Dashboard", "analytics-dashboard", "dashboard", "/college-admin/reports-analytics/dashboard"),
            ("02", "Report Definitions", "report-definitions", "list", "/college-admin/reports-analytics/definitions"),
            ("03", "Report Jobs", "report-jobs", "list", "/college-admin/reports-analytics/jobs"),
            ("04", "Analytics Snapshots", "analytics-snapshots", "list", "/college-admin/reports-analytics/snapshots"),
            ("05", "Export Downloads", "export-downloads", "report", "/college-admin/reports-analytics/exports/download"),
            ("06", "Failed Report Jobs", "failed-report-jobs", "list", "/college-admin/reports-analytics/failures"),
        ],
    ),
    "17": (
        "approvals",
        "161:19761",
        [
            ("01", "Approvals Dashboard", "approvals-dashboard", "dashboard", "/college-admin/workflow-administration/pending"),
            ("02", "Workflow Definitions", "workflow-definitions", "list", "/college-admin/workflow-administration/definitions"),
            ("03", "Pending Tasks", "pending-tasks", "list", "/college-admin/workflow-administration/pending"),
            ("04", "Workflow Escalations", "workflow-escalations", "list", "/college-admin/workflow-administration/escalations"),
            ("05", "Approval History", "approval-history", "detail", "/college-admin/workflow-administration/instances"),
        ],
    ),
    "18": (
        "security",
        "161:23475",
        [
            ("01", "Security Dashboard", "security-dashboard", "dashboard", "/college-admin/security-administration/reports/summary"),
            ("02", "Audit Logs", "audit-logs", "list", "/college-admin/security-administration/audit-logs"),
            ("03", "Security Events", "security-events", "list", "/college-admin/security-administration/security-events"),
            ("04", "Login Activity", "login-activity", "list", "/college-admin/security-administration/login-activity"),
            ("05", "Security Policies", "security-policies", "settings", "/college-admin/security-administration/policies"),
            ("06", "Integrity Check", "audit-integrity", "report", "/college-admin/security-administration/audit-integrity"),
        ],
    ),
    "19": (
        "data-import",
        "161:26820",
        [
            ("01", "Import Dashboard", "import-dashboard", "dashboard", "/college-admin/data-import/templates"),
            ("02", "Import Templates", "import-templates", "list", "/college-admin/data-import/templates"),
            ("03", "Import Jobs", "import-jobs", "detail", "/college-admin/data-import/jobs"),
            ("04", "Migration History", "migration-history", "list", "/college-admin/data-import/migration-history"),
            ("05", "Error Reports", "import-error-reports", "report", "/college-admin/data-import/error-reports/download"),
        ],
    ),
    "20": (
        "integrations",
        "161:30992",
        [
            ("01", "Integrations Dashboard", "integrations-dashboard", "dashboard", "/college-admin/integration-administration/integrations"),
            ("02", "Integration Registry", "integration-registry", "list", "/college-admin/integration-administration/integrations"),
            ("03", "Health Checks", "integration-health", "detail", "/college-admin/integration-administration/integrations"),
            ("04", "Sync History", "sync-history", "list", "/college-admin/integration-administration/integrations"),
        ],
    ),
    "21": (
        "helpdesk",
        "161:35018",
        [
            ("01", "Helpdesk Dashboard", "helpdesk-dashboard", "dashboard", "/college-admin/helpdesk/reports/performance"),
            ("02", "Support Categories", "support-categories", "list", "/college-admin/helpdesk/categories"),
            ("03", "Support Tickets", "support-tickets", "list", "/college-admin/helpdesk/tickets"),
            ("04", "Performance Report", "helpdesk-performance", "report", "/college-admin/helpdesk/reports/performance"),
            ("05", "Ticket SLA Status", "ticket-sla-status", "detail", "/college-admin/helpdesk/tickets"),
        ],
    ),
    "22": (
        "finance-extensions",
        "162:2198",
        [
            ("01", "Finance Extensions Dashboard", "finance-extensions-dashboard", "form", "/college-admin/finance-extensions/budgets"),
            ("02", "Budgets", "institutional-budgets", "form", "/college-admin/finance-extensions/budgets"),
            ("03", "Budget Utilization", "budget-utilization", "detail", "/college-admin/finance-extensions/budgets"),
            ("04", "Budget Report", "budget-report", "report", "/college-admin/finance-extensions/budgets"),
            ("05", "Expenses", "institutional-expenses", "form", "/college-admin/finance-extensions/expenses"),
            ("06", "Vendors", "vendors", "form", "/college-admin/finance-extensions/vendors"),
            ("07", "Purchase Requests", "purchase-requests", "form", "/college-admin/finance-extensions/purchase-requests"),
        ],
    ),
    "23": (
        "operations",
        "162:6804",
        [
            ("01", "Operations Dashboard", "operations-dashboard", "report", "/college-admin/operations-extensions/reports/summary"),
            ("02", "Assets", "campus-assets", "form", "/college-admin/operations-extensions/assets"),
            ("03", "Facilities", "facilities", "form", "/college-admin/operations-extensions/facilities"),
            ("04", "Maintenance", "maintenance-requests", "form", "/college-admin/operations-extensions/maintenance"),
            ("05", "Inventory", "operations-inventory", "form", "/college-admin/operations-extensions/inventory"),
            ("06", "Service Contracts", "service-contracts", "form", "/college-admin/operations-extensions/service-contracts"),
            ("07", "Operational Incidents", "operational-incidents", "form", "/college-admin/operations-extensions/incidents"),
            ("08", "Operations Summary", "operations-summary", "report", "/college-admin/operations-extensions/reports/summary"),
        ],
    ),
    "24": (
        "shared",
        "162:11303",
        [
            ("01", "Dialog & State Gallery", "dialog-state-gallery", "report", "/college-admin/dashboard"),
            ("02", "Shared Form Controls", "shared-form-controls", "report", "/college-admin/dashboard"),
            ("03", "Table & List Patterns", "table-list-patterns", "report", "/college-admin/dashboard"),
            ("04", "Empty & Error States", "empty-error-states", "report", "/college-admin/dashboard"),
        ],
    ),
}


def slugify(title: str) -> str:
    t = title.lower()
    t = re.sub(r"[^a-z0-9]+", "-", t)
    return t.strip("-")


def make_node(page_node: str, screen: str) -> str:
    base = page_node.split(":")[0]
    seq = 2200 + int(screen)
    return f"{base}:{seq}"


def main() -> None:
    data = json.loads(FRAMES_PATH.read_text(encoding="utf-8"))
    existing = {(f["module"], f["screen"]) for f in data["frames"]}
    added = 0
    for mod, (module_key, page_node, screens) in MODULES.items():
        base_route = f"/college-admin/{module_key}"
        for screen, title, slug, view_type, api_path in screens:
            key = (mod, screen)
            if key in existing:
                continue
            data["frames"].append(
                {
                    "figmaNodeId": make_node(page_node, screen),
                    "name": f"CA {mod}.{screen} – {title}",
                    "module": mod,
                    "screen": screen,
                    "moduleKey": module_key,
                    "title": title,
                    "slug": slug,
                    "route": f"{base_route}/{slug}",
                    "viewType": view_type,
                    "apiPath": api_path,
                    "synthetic": True,
                }
            )
            added += 1
            existing.add(key)
    data["frames"].sort(key=lambda f: (f["module"], f["screen"]))
    data["frameCount"] = len(data["frames"])
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    FRAMES_PATH.write_text(text, encoding="utf-8")
    mirror = ROOT / "design" / "college-admin-frames.json"
    mirror.write_text(text, encoding="utf-8")
    print(f"Added {added} screens; total {data['frameCount']}")


if __name__ == "__main__":
    main()