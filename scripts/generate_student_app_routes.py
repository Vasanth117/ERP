"""Generate Next.js page.tsx files for student portal screens (ST 00–08)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "frontend" / "src" / "app" / "student"

SCREENS: list[tuple[str, str]] = [
    ("portal-home", "home"),
    ("dashboard", "dashboard"),
    ("profile", "profile"),
    ("profile-personal", "profile/personal"),
    ("profile-academic", "profile/academic"),
    ("profile-contact", "profile/contact"),
    ("profile-guardian", "profile/guardian"),
    ("profile-edit", "profile/edit"),
    ("profile-activity", "profile/activity"),
    ("profile-update-requests", "profile/update-requests"),
    ("documents", "documents"),
    ("academics", "academics"),
    ("enrollment-status", "academics/enrollment-status"),
    ("enrollment-history", "academics/enrollment-history"),
    ("academic-eligibility", "academics/eligibility"),
    ("enrollment-requests", "academics/enrollment-requests"),
    ("new-enrollment-request", "academics/new-enrollment-request"),
    ("curriculum", "curriculum"),
    ("programme-curriculum", "curriculum/programme"),
    ("enrolled-courses", "curriculum/enrolled-courses"),
    ("semester-subjects", "curriculum/semester-subjects"),
    ("course-syllabus", "curriculum/course-syllabus"),
    ("learning-outcomes", "curriculum/learning-outcomes"),
    ("course-prerequisites", "curriculum/course-prerequisites"),
    ("course-information", "curriculum/course-information"),
    ("registration", "registration"),
    ("registration-eligibility", "registration/eligibility"),
    ("available-courses", "registration/available-courses"),
    ("elective-groups", "registration/elective-groups"),
    ("my-registrations", "registration/my-registrations"),
    ("submit-registration", "registration/submit"),
    ("registration-history", "registration/history"),
    ("timetable", "timetable"),
    ("daily-timetable", "timetable/daily"),
    ("weekly-timetable", "timetable/weekly"),
    ("semester-timetable", "timetable/semester"),
    ("academic-calendar", "timetable/calendar"),
    ("calendar-deadlines", "timetable/deadlines"),
    ("examination-schedule", "timetable/examinations"),
    ("timetable-changes", "timetable/changes"),
    ("timetable-notifications", "timetable/notifications"),
    ("cancelled-sessions", "timetable/cancelled-sessions"),
    ("attendance", "attendance"),
    ("attendance-subjects", "attendance/subjects"),
    ("attendance-daily", "attendance/daily"),
    ("attendance-history", "attendance/history"),
    ("attendance-shortages", "attendance/shortages"),
    ("attendance-eligibility", "attendance/eligibility"),
    ("attendance-export", "attendance/export"),
    ("discrepancy-requests", "attendance/discrepancy-requests"),
    ("new-discrepancy-request", "attendance/new-discrepancy"),
    ("cia", "cia"),
    ("cia-schedules", "cia/schedules"),
    ("cia-marks", "cia/marks"),
    ("cia-subject-marks", "cia/subject-marks"),
    ("cia-corrections", "cia/corrections"),
    ("cia-history", "cia/history"),
    ("cia-components", "cia/components"),
    ("assessments", "assessments"),
    ("assignments", "assessments/assignments"),
    ("assignment-detail", "assessments/assignment-detail"),
    ("quiz-schedules", "assessments/quiz-schedules"),
    ("quiz-results", "assessments/quiz-results"),
    ("assignment-marks", "assessments/marks"),
    ("submission-status", "assessments/submission-status"),
    ("assignment-feedback", "assessments/feedback"),
    ("resubmission-eligibility", "assessments/resubmission"),
]

TEMPLATE = """import { StudentScreen } from "@/features/student/components/student-screen";

export default function Page() {
  return <StudentScreen slug="__SLUG__" />;
}
"""

SUSPENSE_TEMPLATE = """import { Suspense } from "react";

import { StudentScreen } from "@/features/student/components/student-screen";

function PageInner() {
  return <StudentScreen slug="__SLUG__" />;
}

export default function Page() {
  return (
    <Suspense fallback={null}>
      <PageInner />
    </Suspense>
  );
}
"""

USE_SUSPENSE_SLUGS = {
    "course-syllabus",
    "learning-outcomes",
    "course-prerequisites",
    "course-information",
    "cia-components",
    "assignment-detail",
    "submission-status",
    "assignment-feedback",
    "resubmission-eligibility",
}


def main() -> None:
    for slug, rel_path in SCREENS:
        page_dir = APP / rel_path
        page_dir.mkdir(parents=True, exist_ok=True)
        page_file = page_dir / "page.tsx"
        body = SUSPENSE_TEMPLATE if slug in USE_SUSPENSE_SLUGS else TEMPLATE
        page_file.write_text(body.replace("__SLUG__", slug), encoding="utf-8")
        print(f"wrote {page_file.relative_to(ROOT)}")


if __name__ == "__main__":
    main()