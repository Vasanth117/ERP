"""Read practical / laboratory / model examination data for enrolled students."""

from beanie import PydanticObjectId

from app.modules.academics.enums import SessionType
from app.modules.academics.models import ClassSession, ExaminationSchedule
from app.modules.examinations.enums import AssessmentComponentType, StudentMarkStatus
from app.modules.examinations.models import Assessment, AssessmentComponent, MarksCorrectionRequest, StudentAssessmentMark
from app.modules.students.examination_portal_enums import MODEL_EXAM_TYPES, PRACTICAL_EXAM_TYPES
from app.modules.students.integrations.assessment_reader import assessments_for_student, student_course_codes
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.integrations.timetable_reader import timetable_entries_for_student

_reader = StudentDataReader()
_PUBLISHED = frozenset({StudentMarkStatus.APPROVED, StudentMarkStatus.LOCKED})


def _normalize_exam_type(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


async def laboratory_subjects(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
) -> list[dict]:
    entries = await timetable_entries_for_student(
        tenant_id,
        user_id,
        year=year,
        semester=semester,
        session_type=SessionType.LABORATORY,
    )
    roster = await _reader.roster_entries(tenant_id, user_id, academic_year_label=year, semester_label=semester)
    roster_by_course = {r.course_code: r for r in roster}
    grouped: dict[tuple[str, str], dict] = {}
    for entry in entries:
        key = (entry.course_code, entry.section)
        row = grouped.setdefault(
            key,
            {
                "course_id": entry.course_id,
                "course_code": entry.course_code,
                "course_name": entry.course_name,
                "section": entry.section,
                "laboratory": entry.laboratory,
                "weekly_sessions": 0,
            },
        )
        row["weekly_sessions"] += 1
        if entry.laboratory:
            row["laboratory"] = entry.laboratory
    for r in roster:
        if (r.course_code, r.section_code) not in grouped:
            lab_entries = [
                e
                for e in entries
                if e.course_code == r.course_code and e.section == r.section_code
            ]
            if lab_entries:
                continue
        key = (r.course_code, r.section_code)
        if key not in grouped:
            grouped[key] = {
                "course_id": r.course_id,
                "course_code": r.course_code,
                "course_name": None,
                "section": r.section_code,
                "laboratory": None,
                "weekly_sessions": 0,
            }
    return list(grouped.values())


async def examination_schedules_by_types(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
    exam_types: frozenset[str],
) -> list[ExaminationSchedule]:
    codes = await student_course_codes(tenant_id, user_id, year=year, semester=semester)
    if not codes:
        return []
    rows = await ExaminationSchedule.find(
        {
            "tenant_id": tenant_id,
            "academic_year_label": year,
            "semester_label": semester,
            "course_code": {"$in": list(codes)},
        }
    ).sort("scheduled_at").to_list()
    filtered: list[ExaminationSchedule] = []
    for row in rows:
        if _normalize_exam_type(row.exam_type) in exam_types:
            filtered.append(row)
    return filtered


async def practical_class_sessions(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
) -> list[ClassSession]:
    from app.modules.students.integrations.timetable_reader import class_sessions_for_student

    sessions = await class_sessions_for_student(tenant_id, user_id, year=year, semester=semester)
    return [s for s in sessions if s.session_type == SessionType.LABORATORY]


async def practical_components(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
) -> list[tuple[Assessment, AssessmentComponent]]:
    assessments = await assessments_for_student(tenant_id, user_id, year=year, semester=semester)
    items: list[tuple[Assessment, AssessmentComponent]] = []
    for assessment in assessments:
        components = await AssessmentComponent.find(
            {"tenant_id": tenant_id, "assessment_id": assessment.assessment_id}
        ).to_list()
        for comp in components:
            if comp.component_type == AssessmentComponentType.PRACTICAL:
                items.append((assessment, comp))
    return items


async def model_examination_components(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
) -> list[tuple[Assessment, AssessmentComponent]]:
    """Model exams map to FINAL_EXAM components or metadata on assessments."""
    assessments = await assessments_for_student(tenant_id, user_id, year=year, semester=semester)
    items: list[tuple[Assessment, AssessmentComponent]] = []
    for assessment in assessments:
        if assessment.metadata.get("is_model_examination"):
            components = await AssessmentComponent.find(
                {"tenant_id": tenant_id, "assessment_id": assessment.assessment_id}
            ).to_list()
            items.extend((assessment, c) for c in components)
            continue
        components = await AssessmentComponent.find(
            {"tenant_id": tenant_id, "assessment_id": assessment.assessment_id}
        ).to_list()
        for comp in components:
            if comp.code.lower().startswith("model") or comp.name.lower().startswith("model"):
                items.append((assessment, comp))
    return items


async def student_practical_marks(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    published_only: bool,
) -> list[StudentAssessmentMark]:
    component_ids: set[str] = set()
    assessments = await Assessment.find({"tenant_id": tenant_id}).to_list()
    for assessment in assessments:
        components = await AssessmentComponent.find(
            {
                "tenant_id": tenant_id,
                "assessment_id": assessment.assessment_id,
                "component_type": AssessmentComponentType.PRACTICAL,
            }
        ).to_list()
        component_ids.update(c.component_id for c in components)
    if not component_ids:
        return []
    filters: dict = {
        "tenant_id": tenant_id,
        "student_user_id": user_id,
        "component_id": {"$in": list(component_ids)},
    }
    if published_only:
        filters["status"] = {"$in": list(_PUBLISHED)}
    return await StudentAssessmentMark.find(filters).sort("-updated_at").to_list()


async def student_model_marks(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
) -> list[StudentAssessmentMark]:
    pairs = await model_examination_components(tenant_id, user_id, year=year, semester=semester)
    if not pairs:
        return []
    component_ids = {comp.component_id for _, comp in pairs}
    return await StudentAssessmentMark.find(
        {
            "tenant_id": tenant_id,
            "student_user_id": user_id,
            "component_id": {"$in": list(component_ids)},
            "status": {"$in": list(_PUBLISHED)},
        }
    ).to_list()


async def corrections_for_student(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> list[MarksCorrectionRequest]:
    return await MarksCorrectionRequest.find(
        {"tenant_id": tenant_id, "student_user_id": user_id}
    ).sort("-created_at").to_list()
