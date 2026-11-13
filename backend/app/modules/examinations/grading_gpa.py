"""GPA and CGPA from institutional grading policy and published results."""

from dataclasses import dataclass

from app.modules.examinations.grading import get_grading_policy, letter_grade, weighted_percentage
from app.modules.examinations.models import GradingPolicy


DEFAULT_GRADE_POINTS: dict[str, float] = {
    "O": 10.0,
    "A+": 9.5,
    "A": 9.0,
    "B+": 8.5,
    "B": 8.0,
    "C": 7.0,
    "D": 6.0,
    "E": 5.0,
    "F": 0.0,
    "PASS": 5.0,
    "FAIL": 0.0,
}


def grade_point_for_letter(grade_letter: str | None, policy: GradingPolicy) -> float | None:
    if not grade_letter:
        return None
    key = grade_letter.strip().upper()
    for band in policy.grade_bands:
        if str(band.get("grade", "")).upper() == key and band.get("points") is not None:
            return float(band["points"])
    return DEFAULT_GRADE_POINTS.get(key)


def grade_point_from_percentage(percentage: float, policy: GradingPolicy) -> tuple[str, float]:
    letter = letter_grade(percentage, policy)
    points = grade_point_for_letter(letter, policy)
    if points is None:
        points = round(percentage / 10, 2)
    return letter, points


@dataclass
class GradedSubjectLine:
    course_code: str
    season_id: str
    academic_year_label: str
    semester_label: str
    credit_units: float
    grade_letter: str | None
    grade_points: float | None
    pass_fail: str | None


def compute_semester_gpa(lines: list[GradedSubjectLine]) -> float | None:
    weighted = 0.0
    credits = 0.0
    for line in lines:
        if line.grade_points is None or line.credit_units <= 0:
            continue
        weighted += line.grade_points * line.credit_units
        credits += line.credit_units
    if credits <= 0:
        return None
    return round(weighted / credits, 2)


def compute_cgpa(all_lines: list[GradedSubjectLine]) -> float | None:
    """Best attempt per course for CGPA (latest season wins by caller ordering)."""
    by_course: dict[str, GradedSubjectLine] = {}
    for line in all_lines:
        by_course[line.course_code] = line
    return compute_semester_gpa(list(by_course.values()))


def gpa_breakdown_lines(lines: list[GradedSubjectLine]) -> list[dict]:
    return [
        {
            "course_code": line.course_code,
            "credit_units": line.credit_units,
            "grade_letter": line.grade_letter,
            "grade_points": line.grade_points,
            "quality_points": round((line.grade_points or 0) * line.credit_units, 2),
        }
        for line in lines
        if line.credit_units > 0
    ]


async def policy_for_tenant(tenant_id) -> GradingPolicy:
    return await get_grading_policy(tenant_id)
