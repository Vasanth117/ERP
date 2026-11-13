"""Load published results and credits for GPA computation."""

from beanie import PydanticObjectId

from app.modules.academics.curriculum_models import CourseRecord
from app.modules.examinations.examination_registration_enums import SemesterResultPublicationStatus
from app.modules.examinations.grading_gpa import (
    GradedSubjectLine,
    compute_cgpa,
    compute_semester_gpa,
    grade_point_for_letter,
    grade_point_from_percentage,
    policy_for_tenant,
)
from app.modules.examinations.grading import weighted_percentage
from app.modules.examinations.result_publication_models import SemesterResultPublication, SemesterResultSubjectMark
from app.modules.students.enums import AcademicStanding
from app.modules.students.models import StudentAcademicRecord


async def published_subject_lines(
    tenant_id: PydanticObjectId, user_id: PydanticObjectId
) -> list[SemesterResultSubjectMark]:
    return await SemesterResultSubjectMark.find(
        {"tenant_id": tenant_id, "student_user_id": user_id, "published": True}
    ).sort([("season_id", 1), ("course_code", 1)]).to_list()


async def published_publications(
    tenant_id: PydanticObjectId, user_id: PydanticObjectId
) -> list[SemesterResultPublication]:
    return await SemesterResultPublication.find(
        {
            "tenant_id": tenant_id,
            "student_user_id": user_id,
            "status": SemesterResultPublicationStatus.PUBLISHED,
        }
    ).sort("published_at").to_list()


async def credit_for_course(tenant_id: PydanticObjectId, course_code: str) -> float:
    course = await CourseRecord.find_one({"tenant_id": tenant_id, "course_code": course_code})
    return float(course.credit_units) if course else 0.0


async def to_graded_lines(
    tenant_id: PydanticObjectId, marks: list[SemesterResultSubjectMark]
) -> list[GradedSubjectLine]:
    if not marks:
        return []
    policy = await policy_for_tenant(tenant_id)
    pubs = {p.season_id: p for p in await published_publications(tenant_id, marks[0].student_user_id)}
    lines: list[GradedSubjectLine] = []
    for mark in marks:
        credits = mark.credit_units
        if credits is None:
            credits = await credit_for_course(tenant_id, mark.course_code)
        letter = mark.grade_letter
        points = mark.grade_points
        if points is None and letter:
            points = grade_point_for_letter(letter, policy)
        if letter is None and mark.total_obtained is not None and mark.total_max:
            letter, points = grade_point_from_percentage(
                weighted_percentage(mark.total_obtained, mark.total_max), policy
            )
        pub = pubs.get(mark.season_id)
        year = pub.academic_year_label if pub else ""
        semester = pub.semester_label if pub else ""
        lines.append(
            GradedSubjectLine(
                course_code=mark.course_code,
                season_id=mark.season_id,
                academic_year_label=year,
                semester_label=semester,
                credit_units=credits or 0.0,
                grade_letter=letter,
                grade_points=points,
                pass_fail=mark.pass_fail,
            )
        )
    return lines


async def lines_for_season(
    tenant_id: PydanticObjectId, user_id: PydanticObjectId, season_id: str
) -> list[GradedSubjectLine]:
    marks = await SemesterResultSubjectMark.find(
        {
            "tenant_id": tenant_id,
            "student_user_id": user_id,
            "season_id": season_id,
            "published": True,
        }
    ).to_list()
    return await to_graded_lines(tenant_id, marks)


async def academic_standing_record(
    tenant_id: PydanticObjectId, user_id: PydanticObjectId, year: str, semester: str
) -> StudentAcademicRecord | None:
    return await StudentAcademicRecord.find_one(
        {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "academic_year_label": year,
            "semester_label": semester,
        }
    )


def derive_standing(record: StudentAcademicRecord | None) -> AcademicStanding:
    if record is None:
        return AcademicStanding.UNKNOWN
    return record.academic_standing


async def semester_gpa_calculated(tenant_id: PydanticObjectId, user_id: PydanticObjectId, season_id: str) -> float | None:
    lines = await lines_for_season(tenant_id, user_id, season_id)
    return compute_semester_gpa(lines)


async def cgpa_calculated(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> float | None:
    marks = await published_subject_lines(tenant_id, user_id)
    lines = await to_graded_lines(tenant_id, marks)
    return compute_cgpa(lines)
