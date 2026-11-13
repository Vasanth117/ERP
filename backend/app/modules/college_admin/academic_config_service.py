"""Academic configuration services (college admin)."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.core.exceptions import AppError
from app.modules.academics.curriculum_models import CourseRecord, SectionOffering
from app.modules.academics.models import AcademicCalendarEvent, AcademicYearContext
from app.modules.attendance.models import AttendancePolicyReference, AttendancePolicyRules
from app.modules.college_admin.academic_config_models import (
    AcademicCalendar,
    AcademicCalendarEventEmbed,
    AcademicConfigurationVersion,
    AcademicProgramme,
    AcademicRegulation,
    AcademicTerm,
    AcademicYear,
    ConfigPublicationStatus,
)
from app.modules.college_admin.academic_config_schemas import (
    AcademicCalendarCreate,
    AcademicCalendarRead,
    AcademicTermCreate,
    AcademicTermRead,
    AcademicYearCreate,
    AcademicYearRead,
    AcademicYearUpdate,
    ConfigHistoryRead,
    CourseAdminCreate,
    CourseAdminRead,
    ProgrammeCreate,
    ProgrammeRead,
    RegulationRead,
    RegulationUpsert,
    SectionCreate,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.examinations.models import GradingPolicy


async def _record_version(
    *,
    tenant_id: PydanticObjectId,
    scope: str,
    resource_id: str,
    version_number: int,
    snapshot: dict,
    actor_id: PydanticObjectId,
) -> None:
    await AcademicConfigurationVersion(
        tenant_id=tenant_id,
        scope=scope,
        resource_id=resource_id,
        version_number=version_number,
        snapshot=snapshot,
        published_by=actor_id,
    ).insert()


async def create_academic_year(scope: AccessScope, payload: AcademicYearCreate) -> AcademicYearRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    code = payload.year_code.strip()
    if await AcademicYear.find_one(Eq(AcademicYear.tenant_id, tenant_id), Eq(AcademicYear.year_code, code)):
        raise AppError(code="CONFLICT", message="Academic year code already exists", status_code=409)
    doc = AcademicYear(
        tenant_id=tenant_id,
        year_code=code,
        label=payload.label,
        start_date=payload.start_date,
        end_date=payload.end_date,
        is_current=payload.is_current,
        updated_by=scope.user_id,
    )
    await doc.insert()
    return AcademicYearRead.from_document(doc)


async def list_academic_years(scope: AccessScope) -> list[AcademicYearRead]:
    authorize(scope, Permission.ACADEMIC_CONFIG_READ)
    tenant_id = require_college_tenant_scope(scope)
    rows = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-year_code").to_list()
    return [AcademicYearRead.from_document(row) for row in rows]


async def update_academic_year(scope: AccessScope, year_id: PydanticObjectId, payload: AcademicYearUpdate) -> AcademicYearRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    doc = await AcademicYear.get(year_id)
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Academic year not found", status_code=404)
    if doc.status == ConfigPublicationStatus.PUBLISHED:
        raise AppError(code="FORBIDDEN", message="Published academic years are immutable", status_code=403)
    data = payload.model_dump(exclude_none=True)
    for key, value in data.items():
        setattr(doc, key, value)
    doc.version += 1
    doc.updated_at = utcnow()
    doc.updated_by = scope.user_id
    await doc.save()
    return AcademicYearRead.from_document(doc)


async def publish_academic_year(scope: AccessScope, year_id: PydanticObjectId) -> AcademicYearRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    doc = await AcademicYear.get(year_id)
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Academic year not found", status_code=404)
    if doc.is_current:
        for other in await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id), Eq(AcademicYear.is_current, True)).to_list():
            if other.id != doc.id:
                other.is_current = False
                await other.save()
        ctx = await AcademicYearContext.find_one(Eq(AcademicYearContext.tenant_id, tenant_id), Eq(AcademicYearContext.is_current, True))
        term = await AcademicTerm.find_one(Eq(AcademicTerm.tenant_id, tenant_id), Eq(AcademicTerm.is_current, True))
        semester_label = term.label if term else "Semester-1"
        if ctx is None:
            ctx = AcademicYearContext(
                tenant_id=tenant_id,
                academic_year_label=doc.label,
                semester_label=semester_label,
                is_current=True,
            )
            await ctx.insert()
        else:
            ctx.academic_year_label = doc.label
            if term:
                ctx.semester_label = term.label
            ctx.updated_at = utcnow()
            await ctx.save()
    doc.status = ConfigPublicationStatus.PUBLISHED
    doc.updated_at = utcnow()
    await doc.save()
    await _record_version(
        tenant_id=tenant_id,
        scope="academic_year",
        resource_id=str(doc.id),
        version_number=doc.version,
        snapshot=doc.model_dump(mode="json"),
        actor_id=scope.user_id,
    )
    return AcademicYearRead.from_document(doc)


async def create_academic_term(scope: AccessScope, payload: AcademicTermCreate) -> AcademicTermRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    year_id = to_object_id(payload.academic_year_id, "academic_year_id")
    year = await AcademicYear.get(year_id)
    if year is None or year.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Academic year not found", status_code=404)
    code = payload.term_code.upper()
    doc = AcademicTerm(
        tenant_id=tenant_id,
        academic_year_id=year_id,
        term_code=code,
        label=payload.label,
        start_date=payload.start_date,
        end_date=payload.end_date,
        is_current=payload.is_current,
    )
    await doc.insert()
    return AcademicTermRead.from_document(doc)


async def list_academic_terms(scope: AccessScope, *, academic_year_id: str | None = None) -> list[AcademicTermRead]:
    authorize(scope, Permission.ACADEMIC_CONFIG_READ)
    tenant_id = require_college_tenant_scope(scope)
    query = AcademicTerm.find(Eq(AcademicTerm.tenant_id, tenant_id))
    if academic_year_id:
        query = query.find(Eq(AcademicTerm.academic_year_id, to_object_id(academic_year_id, "academic_year_id")))
    rows = await query.sort("+term_code").to_list()
    return [AcademicTermRead.from_document(row) for row in rows]


async def create_calendar(scope: AccessScope, payload: AcademicCalendarCreate) -> AcademicCalendarRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    year_id = to_object_id(payload.academic_year_id, "academic_year_id")
    term_id = to_object_id(payload.academic_term_id, "academic_term_id") if payload.academic_term_id else None
    events = [AcademicCalendarEventEmbed.model_validate(event) for event in payload.events]
    doc = AcademicCalendar(
        tenant_id=tenant_id,
        academic_year_id=year_id,
        academic_term_id=term_id,
        title=payload.title,
        events=events,
    )
    await doc.insert()
    return AcademicCalendarRead.from_document(doc)


async def publish_calendar(scope: AccessScope, calendar_id: PydanticObjectId) -> AcademicCalendarRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    doc = await AcademicCalendar.get(calendar_id)
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Calendar not found", status_code=404)
    for event in doc.events:
        await AcademicCalendarEvent(
            tenant_id=tenant_id,
            title=event.title,
            description=event.description,
            event_at=event.event_at,
            event_type=event.event_type,
            audience=event.audience,
        ).insert()
    doc.status = ConfigPublicationStatus.PUBLISHED
    doc.published_at = utcnow()
    doc.version += 1
    await doc.save()
    await _record_version(
        tenant_id=tenant_id,
        scope="academic_calendar",
        resource_id=str(doc.id),
        version_number=doc.version,
        snapshot=doc.model_dump(mode="json"),
        actor_id=scope.user_id,
    )
    return AcademicCalendarRead.from_document(doc)


async def upsert_programme(scope: AccessScope, payload: ProgrammeCreate) -> ProgrammeRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    code = payload.programme_code.upper()
    existing = await AcademicProgramme.find_one(Eq(AcademicProgramme.tenant_id, tenant_id), Eq(AcademicProgramme.programme_code, code))
    dept_id = to_object_id(payload.department_id, "department_id") if payload.department_id else None
    if existing:
        existing.name = payload.name
        existing.department_id = dept_id
        existing.duration_semesters = payload.duration_semesters
        existing.credits_required = payload.credits_required
        existing.updated_at = utcnow()
        await existing.save()
        return ProgrammeRead.from_document(existing)
    doc = AcademicProgramme(
        tenant_id=tenant_id,
        programme_code=code,
        name=payload.name,
        department_id=dept_id,
        duration_semesters=payload.duration_semesters,
        credits_required=payload.credits_required,
    )
    await doc.insert()
    return ProgrammeRead.from_document(doc)


async def list_programmes(scope: AccessScope) -> list[ProgrammeRead]:
    authorize(scope, Permission.ACADEMIC_CONFIG_READ)
    tenant_id = require_college_tenant_scope(scope)
    rows = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).sort("+programme_code").to_list()
    return [ProgrammeRead.from_document(row) for row in rows]


async def upsert_regulation(scope: AccessScope, payload: RegulationUpsert) -> RegulationRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    doc = await AcademicRegulation.find_one(Eq(AcademicRegulation.tenant_id, tenant_id), Eq(AcademicRegulation.scope_key, payload.scope_key))
    if doc is None:
        doc = AcademicRegulation(
            tenant_id=tenant_id,
            scope_key=payload.scope_key,
            rules=payload.rules,
            effective_from=payload.effective_from,
            updated_by=scope.user_id,
        )
        await doc.insert()
    else:
        if doc.status == ConfigPublicationStatus.PUBLISHED:
            doc = AcademicRegulation(
                tenant_id=tenant_id,
                scope_key=payload.scope_key,
                rules=payload.rules,
                effective_from=payload.effective_from,
                version=doc.version + 1,
                updated_by=scope.user_id,
            )
            await doc.insert()
        else:
            doc.rules = payload.rules
            doc.effective_from = payload.effective_from
            doc.version += 1
            doc.updated_by = scope.user_id
            doc.updated_at = utcnow()
            await doc.save()
    return RegulationRead.from_document(doc)


async def publish_regulation(scope: AccessScope, regulation_id: PydanticObjectId) -> RegulationRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    doc = await AcademicRegulation.get(regulation_id)
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Regulation not found", status_code=404)
    if doc.scope_key == "grading":
        policy = await GradingPolicy.find_one(Eq(GradingPolicy.tenant_id, tenant_id))
        if policy is None:
            policy = GradingPolicy(tenant_id=tenant_id)
        policy.grade_bands = doc.rules.get("grade_bands", policy.grade_bands)
        policy.pass_percentage = float(doc.rules.get("pass_percentage", policy.pass_percentage))
        policy.low_performance_threshold = float(doc.rules.get("low_performance_threshold", policy.low_performance_threshold))
        policy.updated_at = utcnow()
        await policy.save()
    elif doc.scope_key == "attendance":
        policy = await AttendancePolicyReference.find_one(Eq(AttendancePolicyReference.tenant_id, tenant_id))
        rules = AttendancePolicyRules.model_validate(doc.rules.get("rules", {}))
        if policy is None:
            policy = AttendancePolicyReference(tenant_id=tenant_id, rules=rules)
            await policy.insert()
        else:
            policy.rules = rules
            policy.updated_at = utcnow()
            await policy.save()
    doc.status = ConfigPublicationStatus.PUBLISHED
    doc.updated_at = utcnow()
    await doc.save()
    await _record_version(
        tenant_id=tenant_id,
        scope=f"regulation_{doc.scope_key}",
        resource_id=str(doc.id),
        version_number=doc.version,
        snapshot=doc.model_dump(mode="json"),
        actor_id=scope.user_id,
    )
    return RegulationRead.from_document(doc)


async def create_course(scope: AccessScope, payload: CourseAdminCreate) -> CourseAdminRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    code = payload.course_code.upper()
    if await CourseRecord.find_one({"tenant_id": tenant_id, "course_code": code}):
        raise AppError(code="CONFLICT", message="Course code exists", status_code=409)
    course_id = code.lower().replace(" ", "-")
    doc = CourseRecord(
        tenant_id=tenant_id,
        course_id=course_id,
        course_code=code,
        name=payload.name,
        credit_units=payload.credit_units,
        department_id=to_object_id(payload.department_id, "department_id") if payload.department_id else None,
    )
    await doc.insert()
    return CourseAdminRead(course_id=doc.course_id, course_code=doc.course_code, name=doc.name, credit_units=doc.credit_units, is_active=doc.is_active)


async def create_section(scope: AccessScope, payload: SectionCreate) -> dict:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    section_id = f"{payload.course_code}-{payload.section_code}-{payload.academic_year_label}"
    doc = SectionOffering(
        tenant_id=tenant_id,
        section_id=section_id,
        course_id=payload.course_id,
        course_code=payload.course_code.upper(),
        section_code=payload.section_code.upper(),
        batch_label=payload.batch_label,
        academic_year_label=payload.academic_year_label,
        semester_label=payload.semester_label,
    )
    await doc.insert()
    return {"section_id": section_id}


async def configuration_history(scope: AccessScope, *, limit: int = 50) -> list[ConfigHistoryRead]:
    authorize(scope, Permission.ACADEMIC_CONFIG_READ)
    tenant_id = require_college_tenant_scope(scope)
    rows = await (
        AcademicConfigurationVersion.find(Eq(AcademicConfigurationVersion.tenant_id, tenant_id))
        .sort("-published_at")
        .limit(limit)
        .to_list()
    )
    return [
        ConfigHistoryRead(
            scope=row.scope,
            resource_id=row.resource_id,
            version_number=row.version_number,
            published_at=row.published_at,
        )
        for row in rows
    ]
