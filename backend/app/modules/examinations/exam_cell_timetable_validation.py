"""Exam timetable venue and session validation."""

from datetime import datetime

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.ids import to_object_id
from app.core.exceptions import AppError
from app.modules.college_admin.operations_ext_models import InstitutionFacility
from app.modules.college_admin.repositories import InstitutionCampusRepository
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_timetable_enums import ExamTimetableStatus
from app.modules.examinations.exam_cell_timetable_models import ExamTimetable
from app.modules.examinations.semester_examination_models import ExaminationCentre
from app.modules.students.curriculum_models import CourseCatalogReference


_campus_repo = InstitutionCampusRepository()


async def assert_exam_session_for_timetable(tenant_id: PydanticObjectId, exam_session_id: PydanticObjectId) -> ExamSession:
    session = await ExamSession.find_one(Eq(ExamSession.tenant_id, tenant_id), Eq(ExamSession.id, exam_session_id))
    if session is None:
        raise AppError(code="NOT_FOUND", message="Exam session not found", status_code=404)
    return session


async def assert_editable_timetable(tenant_id: PydanticObjectId, timetable_id: PydanticObjectId) -> ExamTimetable:
    doc = await ExamTimetable.find_one(Eq(ExamTimetable.tenant_id, tenant_id), Eq(ExamTimetable.id, timetable_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Exam timetable not found", status_code=404)
    if doc.status not in {ExamTimetableStatus.DRAFT, ExamTimetableStatus.IN_REVIEW}:
        raise AppError(
            code="TIMETABLE_LOCKED",
            message="Timetable can only be edited in draft or in-review status",
            status_code=409,
        )
    return doc


async def assert_course_reference(
    tenant_id: PydanticObjectId,
    *,
    course_code: str,
    academic_year_label: str,
    semester_label: str,
    programme_code: str | None,
) -> None:
    filters: dict = {
        "tenant_id": tenant_id,
        "course_code": course_code.strip().upper(),
        "academic_year_label": academic_year_label,
        "semester_label": semester_label,
    }
    if programme_code:
        filters["programme_code"] = programme_code.strip().upper()
    row = await CourseCatalogReference.find_one(filters)
    if row is None:
        raise AppError(
            code="VALIDATION_ERROR",
            message=f"Course {course_code} is not in the academic catalogue for the given term",
            status_code=422,
        )


async def assert_venue_assignment(
    tenant_id: PydanticObjectId,
    *,
    centre_code: str | None,
    room_label: str | None,
    facility_id: str | None,
    campus_id: str | None,
) -> PydanticObjectId | None:
    campus_oid: PydanticObjectId | None = None
    if campus_id:
        campus_oid = to_object_id(campus_id, "campus_id")
        campus = await _campus_repo.get_by_id(tenant_id, campus_oid)
        if campus is None:
            raise AppError(code="VALIDATION_ERROR", message="Unknown campus", status_code=422)

    if facility_id:
        facility = await InstitutionFacility.find_one(
            Eq(InstitutionFacility.tenant_id, tenant_id),
            Eq(InstitutionFacility.facility_id, facility_id.strip()),
        )
        if facility is None or not facility.active:
            raise AppError(code="VALIDATION_ERROR", message="Unknown or inactive facility", status_code=422)
        if campus_oid and facility.campus_id and facility.campus_id != campus_oid:
            raise AppError(code="VALIDATION_ERROR", message="Facility does not belong to the selected campus", status_code=422)

    if centre_code:
        centre = await ExaminationCentre.find_one(
            Eq(ExaminationCentre.tenant_id, tenant_id),
            Eq(ExaminationCentre.centre_code, centre_code.strip().upper()),
        )
        if centre is None or not centre.is_active:
            raise AppError(code="VALIDATION_ERROR", message="Unknown or inactive examination centre", status_code=422)
        if room_label:
            normalized_room = room_label.strip().upper()
            allowed = {r.strip().upper() for r in centre.room_labels}
            if allowed and normalized_room not in allowed:
                raise AppError(
                    code="VALIDATION_ERROR",
                    message=f"Room {room_label} is not registered under centre {centre_code}",
                    status_code=422,
                )

    if not centre_code and not facility_id:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Assign either an examination centre room or an institution facility",
            status_code=422,
        )
    return campus_oid


def validate_entry_schedule(scheduled_start: datetime, scheduled_end: datetime) -> int:
    if scheduled_end <= scheduled_start:
        raise AppError(code="VALIDATION_ERROR", message="Examination end must be after start", status_code=422)
    return int((scheduled_end - scheduled_start).total_seconds() // 60)


def build_student_group_label(
    *,
    programme_code: str | None,
    batch_label: str | None,
    section: str | None,
    course_code: str,
) -> str:
    parts = [
        (programme_code or "ALL").strip().upper(),
        (batch_label or "ALL").strip().upper(),
        (section or "ALL").strip().upper(),
        course_code.strip().upper(),
    ]
    return ":".join(parts)