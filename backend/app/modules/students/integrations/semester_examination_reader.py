"""Read semester examination authority for enrolled students."""

from datetime import datetime

from beanie import PydanticObjectId

from app.modules.examinations.enums import ExaminationAnnouncementAudience
from app.modules.examinations.semester_examination_models import (
    ExaminationAnnouncement,
    ExaminationCentre,
    ExaminationRegulation,
    ExaminationScheduleChange,
    SemesterExaminationSeason,
    SemesterExaminationSession,
    StudentExaminationEligibility,
)
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.integrations.assessment_reader import student_course_codes

_reader = StudentDataReader()


async def published_seasons(
    tenant_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
) -> list[SemesterExaminationSeason]:
    return await SemesterExaminationSeason.find(
        {
            "tenant_id": tenant_id,
            "academic_year_label": year,
            "semester_label": semester,
            "published": True,
        }
    ).sort("starts_at").to_list()


async def upcoming_sessions_for_student(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
    from_time: datetime | None = None,
) -> list[SemesterExaminationSession]:
    codes = await student_course_codes(tenant_id, user_id, year=year, semester=semester)
    if not codes:
        return []
    seasons = await published_seasons(tenant_id, year=year, semester=semester)
    if not seasons:
        return []
    season_ids = [s.season_id for s in seasons]
    filters: dict = {
        "tenant_id": tenant_id,
        "season_id": {"$in": season_ids},
        "published": True,
        "course_code": {"$in": list(codes)},
    }
    if from_time is not None:
        filters["scheduled_start"] = {"$gte": from_time}
    sections = await _reader.roster_entries(tenant_id, user_id, academic_year_label=year, semester_label=semester)
    section_by_course = {r.course_code: r.section_code for r in sections}
    rows = await SemesterExaminationSession.find(filters).sort("scheduled_start").to_list()
    result: list[SemesterExaminationSession] = []
    for row in rows:
        section = section_by_course.get(row.course_code)
        if row.section is not None and row.section != section:
            continue
        result.append(row)
    return result


async def session_by_code(tenant_id: PydanticObjectId, season_id: str, session_code: str) -> SemesterExaminationSession | None:
    return await SemesterExaminationSession.find_one(
        {
            "tenant_id": tenant_id,
            "season_id": season_id,
            "session_code": session_code,
            "published": True,
        }
    )


async def centres_for_student(
    tenant_id: PydanticObjectId,
    centre_codes: set[str],
) -> list[ExaminationCentre]:
    if not centre_codes:
        return []
    return await ExaminationCentre.find(
        {"tenant_id": tenant_id, "centre_code": {"$in": list(centre_codes)}, "is_active": True}
    ).to_list()


async def published_eligibility(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    season_id: str,
) -> StudentExaminationEligibility | None:
    return await StudentExaminationEligibility.find_one(
        {
            "tenant_id": tenant_id,
            "student_user_id": user_id,
            "season_id": season_id,
            "published": True,
        }
    )


async def published_regulations(
    tenant_id: PydanticObjectId,
    season_id: str | None = None,
) -> list[ExaminationRegulation]:
    filters: dict = {"tenant_id": tenant_id, "published": True}
    if season_id is not None:
        filters["$or"] = [{"season_id": season_id}, {"season_id": None}]
    return await ExaminationRegulation.find(filters).sort("-published_at").to_list()


async def student_announcements(
    tenant_id: PydanticObjectId,
    *,
    season_id: str | None = None,
    limit: int = 30,
) -> list[ExaminationAnnouncement]:
    filters: dict = {
        "tenant_id": tenant_id,
        "published": True,
        "audience": {"$in": [ExaminationAnnouncementAudience.STUDENTS, ExaminationAnnouncementAudience.ALL]},
    }
    if season_id:
        filters["$or"] = [{"season_id": season_id}, {"season_id": None}]
    return await ExaminationAnnouncement.find(filters).sort("-published_at").limit(limit).to_list()


async def schedule_changes(
    tenant_id: PydanticObjectId,
    *,
    season_id: str | None = None,
    course_codes: set[str] | None = None,
    limit: int = 40,
) -> list[ExaminationScheduleChange]:
    filters: dict = {"tenant_id": tenant_id, "published": True}
    if season_id:
        filters["season_id"] = season_id
    if course_codes:
        filters["$or"] = [
            {"course_code": {"$in": list(course_codes)}},
            {"course_code": None},
        ]
    return await ExaminationScheduleChange.find(filters).sort("-effective_at").limit(limit).to_list()


async def examination_history(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
    before: datetime,
    limit: int = 50,
) -> list[SemesterExaminationSession]:
    codes = await student_course_codes(tenant_id, user_id, year=year, semester=semester)
    if not codes:
        return []
    seasons = await published_seasons(tenant_id, year=year, semester=semester)
    season_ids = [s.season_id for s in seasons]
    if not season_ids:
        return []
    return (
        await SemesterExaminationSession.find(
            {
                "tenant_id": tenant_id,
                "season_id": {"$in": season_ids},
                "published": True,
                "course_code": {"$in": list(codes)},
                "scheduled_start": {"$lt": before},
            }
        )
        .sort("-scheduled_start")
        .limit(limit)
        .to_list()
    )
