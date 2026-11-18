"""Department Admin — academic and curriculum visibility/management (delegated)."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.academics.curriculum_models import CourseRecord, CurriculumRecord, SectionOffering, SubjectRecord
from app.modules.department_admin.audit_helpers import record_department_audit
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicProgramme, ConfigPublicationStatus
from app.modules.department_admin.department_scope import (
    assert_course_in_department,
    department_programme_codes,
    faculty_user_ids_in_department,
)
from app.modules.department_admin.models import DepartmentCourseOfferingRequest, DepartmentRequestStatus
from app.modules.department_admin.phase2_schemas import (
    AcademicProgressionSummary,
    CourseOfferingRead,
    CourseOfferingRequestCreate,
    CurriculumCoverageItem,
    CurriculumRead,
    ProgrammeCreate,
    ProgrammeRead,
    ProgrammeUpdate,
    SubjectRead,
)
from app.modules.department_admin.policy import resolve_authorized_department
from app.modules.faculty.models import CourseCoverage
from app.modules.students.enums import AcademicStanding
from app.modules.students.models import StudentAcademicRecord, StudentProfile


async def _programme_query(tenant_id: PydanticObjectId, central_id: PydanticObjectId, programme_codes: list[str]):
    if programme_codes:
        return AcademicProgramme.find(
            Eq(AcademicProgramme.tenant_id, tenant_id),
            In(AcademicProgramme.programme_code, programme_codes),
        )
    return AcademicProgramme.find(
        Eq(AcademicProgramme.tenant_id, tenant_id),
        Eq(AcademicProgramme.department_id, central_id),
    )


async def list_programmes(scope: AccessScope, user: User, *, pagination: Pagination) -> Page[ProgrammeRead]:
    authorize(scope, Permission.DEPARTMENT_ACADEMIC_READ)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    codes = await department_programme_codes(institution)
    query = await _programme_query(tenant_id, central_id, codes)
    total = await query.count()
    rows = await query.sort("+programme_code").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            ProgrammeRead(
                programme_id=str(r.id),
                programme_code=r.programme_code,
                name=r.name,
                department_id=str(r.department_id) if r.department_id else None,
                duration_semesters=r.duration_semesters,
                status=r.status,
                is_active=r.is_active,
            )
            for r in rows
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_programme(scope: AccessScope, user: User, programme_id: str) -> ProgrammeRead:
    authorize(scope, Permission.DEPARTMENT_ACADEMIC_READ)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await AcademicProgramme.get(to_object_id(programme_id, "programme_id"))
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Programme not found", status_code=404)
    allowed = await department_programme_codes(institution)
    if doc.programme_code not in allowed and doc.department_id != central_id:
        raise AppError(code="FORBIDDEN", message="Programme outside department", status_code=403)
    return ProgrammeRead(
        programme_id=str(doc.id),
        programme_code=doc.programme_code,
        name=doc.name,
        department_id=str(doc.department_id) if doc.department_id else None,
        duration_semesters=doc.duration_semesters,
        status=doc.status,
        is_active=doc.is_active,
    )


async def create_programme(scope: AccessScope, user: User, payload: ProgrammeCreate) -> ProgrammeRead:
    authorize(scope, Permission.DEPARTMENT_ACADEMIC_MANAGE)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    code = payload.programme_code.upper()
    if await AcademicProgramme.find_one(Eq(AcademicProgramme.tenant_id, tenant_id), Eq(AcademicProgramme.programme_code, code)):
        raise AppError(code="CONFLICT", message="Programme code exists", status_code=409)
    doc = AcademicProgramme(
        tenant_id=tenant_id,
        programme_code=code,
        name=payload.name,
        department_id=central_id,
        duration_semesters=payload.duration_semesters,
        credits_required=payload.credits_required,
        status=ConfigPublicationStatus.DRAFT,
        is_active=False,
    )
    await doc.insert()
    institution.programme_codes = sorted(set(institution.programme_codes + [code]))
    institution.updated_at = utcnow()
    await institution.save()
    await record_department_audit(
        actor_id=user.id,
        action="department.programme.create",
        resource_type="academic_programme",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return ProgrammeRead(
        programme_id=str(doc.id),
        programme_code=doc.programme_code,
        name=doc.name,
        department_id=str(doc.department_id),
        duration_semesters=doc.duration_semesters,
        status=doc.status,
        is_active=doc.is_active,
    )


async def update_programme(scope: AccessScope, user: User, programme_id: str, payload: ProgrammeUpdate) -> ProgrammeRead:
    authorize(scope, Permission.DEPARTMENT_ACADEMIC_MANAGE)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await AcademicProgramme.get(to_object_id(programme_id, "programme_id"))
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Programme not found", status_code=404)
    if doc.department_id != central_id:
        raise AppError(code="FORBIDDEN", message="Programme outside department", status_code=403)
    if doc.status == ConfigPublicationStatus.PUBLISHED:
        raise AppError(
            code="FORBIDDEN",
            message="Published programmes require college admin approval to change",
            status_code=403,
        )
    if payload.name is not None:
        doc.name = payload.name
    if payload.duration_semesters is not None:
        doc.duration_semesters = payload.duration_semesters
    if payload.credits_required is not None:
        doc.credits_required = payload.credits_required
    doc.updated_at = utcnow()
    await doc.save()
    return await get_programme(scope, user, programme_id)


async def list_curricula(
    scope: AccessScope,
    user: User,
    *,
    academic_year_label: str | None,
    semester_label: str | None,
) -> list[CurriculumRead]:
    authorize(scope, Permission.DEPARTMENT_ACADEMIC_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    courses = await CourseRecord.find(Eq(CourseRecord.tenant_id, tenant_id), Eq(CourseRecord.department_id, central_id)).to_list()
    course_ids = [c.course_id for c in courses]
    if not course_ids:
        return []
    filters: dict = {"tenant_id": tenant_id, "course_id": {"$in": course_ids}}
    if academic_year_label:
        filters["academic_year_label"] = academic_year_label
    if semester_label:
        filters["semester_label"] = semester_label
    rows = await CurriculumRecord.find(filters).to_list()
    return [
        CurriculumRead(
            curriculum_id=str(r.id),
            course_id=r.course_id,
            academic_year_label=r.academic_year_label,
            semester_label=r.semester_label,
            version=r.version,
            approved=r.approved,
            locked=r.locked,
        )
        for r in rows
    ]


async def list_subjects(scope: AccessScope, user: User) -> list[SubjectRead]:
    authorize(scope, Permission.DEPARTMENT_ACADEMIC_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    from app.modules.department_admin.department_scope import department_course_codes

    codes = await department_course_codes(tenant_id, central_id)
    courses = await CourseRecord.find(
        Eq(CourseRecord.tenant_id, tenant_id),
        In(CourseRecord.course_code, list(codes)),
    ).to_list()
    course_ids = [c.course_id for c in courses]
    subjects = await SubjectRecord.find(Eq(SubjectRecord.tenant_id, tenant_id)).to_list()
    course_by_id = {c.course_id: c.course_code for c in courses}
    items: list[SubjectRead] = []
    for s in subjects:
        linked = course_by_id.get(s.subject_id) or (course_by_id.get(s.subject_code.split("-")[0]) if s.subject_code else None)
        if course_ids:
            items.append(
                SubjectRead(
                    subject_id=s.subject_id,
                    subject_code=s.subject_code,
                    name=s.name,
                    course_code=linked,
                )
            )
    if not items:
        for c in courses:
            items.append(SubjectRead(subject_id=c.course_id, subject_code=c.course_code, name=c.name, course_code=c.course_code))
    return items


async def list_course_offerings(
    scope: AccessScope,
    user: User,
    *,
    academic_year_label: str | None,
    semester_label: str | None,
) -> list[CourseOfferingRead]:
    authorize(scope, Permission.DEPARTMENT_ACADEMIC_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    from app.modules.department_admin.department_scope import department_course_codes

    codes = list(await department_course_codes(tenant_id, central_id))
    if not codes:
        return []
    filters: dict = {"tenant_id": tenant_id, "course_code": {"$in": codes}}
    if academic_year_label:
        filters["academic_year_label"] = academic_year_label
    if semester_label:
        filters["semester_label"] = semester_label
    rows = await SectionOffering.find(filters).to_list()
    return [
        CourseOfferingRead(
            offering_id=str(r.id),
            section_id=r.section_id,
            course_code=r.course_code,
            section_code=r.section_code,
            batch_label=r.batch_label,
            academic_year_label=r.academic_year_label,
            semester_label=r.semester_label,
        )
        for r in rows
    ]


async def request_course_offering(scope: AccessScope, user: User, payload: CourseOfferingRequestCreate) -> dict:
    authorize(scope, Permission.DEPARTMENT_ACADEMIC_MANAGE)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    programmes = await department_programme_codes(institution)
    if payload.programme_code.upper() not in programmes:
        raise AppError(code="FORBIDDEN", message="Programme not in department", status_code=403)
    await assert_course_in_department(tenant_id, central_id, payload.course_code)
    if payload.idempotency_key:
        existing = await DepartmentCourseOfferingRequest.find_one(
            Eq(DepartmentCourseOfferingRequest.tenant_id, tenant_id),
            Eq(DepartmentCourseOfferingRequest.idempotency_key, payload.idempotency_key),
        )
        if existing:
            return {"request_id": str(existing.id), "status": existing.status.value}
    faculty_id = to_object_id(payload.faculty_user_id, "faculty_user_id") if payload.faculty_user_id else None
    if faculty_id:
        from app.modules.department_admin.department_scope import assert_faculty_visible_to_department

        await assert_faculty_visible_to_department(tenant_id, central_id, faculty_id)
    doc = DepartmentCourseOfferingRequest(
        tenant_id=tenant_id,
        institution_department_id=institution.id,
        central_department_id=central_id,
        programme_code=payload.programme_code.upper(),
        course_id=payload.course_id,
        course_code=payload.course_code.upper(),
        section_code=payload.section_code.upper(),
        batch_label=payload.batch_label,
        academic_year_label=payload.academic_year_label,
        semester_label=payload.semester_label,
        faculty_user_id=faculty_id,
        requested_by=user.id,
        idempotency_key=payload.idempotency_key,
    )
    await doc.insert()
    await record_department_audit(
        actor_id=user.id,
        action="department.course_offering.request",
        resource_type="department_course_offering_request",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return {"request_id": str(doc.id), "status": doc.status.value}


async def curriculum_coverage(scope: AccessScope, user: User) -> list[CurriculumCoverageItem]:
    authorize(scope, Permission.DEPARTMENT_ACADEMIC_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    faculty_ids = list(await faculty_user_ids_in_department(tenant_id, central_id, include_cross_teaching=False))
    if not faculty_ids:
        return []
    rows = await CourseCoverage.find(
        Eq(CourseCoverage.tenant_id, tenant_id),
        In(CourseCoverage.faculty_user_id, faculty_ids),
    ).to_list()
    return [
        CurriculumCoverageItem(
            course_code=r.course_code,
            section=r.section,
            faculty_user_id=str(r.faculty_user_id),
            percent_complete=r.percent_complete,
        )
        for r in rows
    ]


async def academic_progression(scope: AccessScope, user: User) -> list[AcademicProgressionSummary]:
    authorize(scope, Permission.DEPARTMENT_ACADEMIC_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    profiles = await StudentProfile.find(
        Eq(StudentProfile.tenant_id, tenant_id),
        Eq(StudentProfile.department_id, central_id),
    ).to_list()
    batches: dict[str | None, list[PydanticObjectId]] = {}
    for p in profiles:
        batches.setdefault(p.batch_label, []).append(p.user_id)
    summaries: list[AcademicProgressionSummary] = []
    for batch, user_ids in batches.items():
        at_risk = await StudentAcademicRecord.find(
            {
                "tenant_id": tenant_id,
                "user_id": {"$in": user_ids},
                "academic_standing": {"$in": [AcademicStanding.PROBATION.value, AcademicStanding.SUSPENDED.value]},
            }
        ).count()
        summaries.append(
            AcademicProgressionSummary(
                batch_label=batch,
                student_count=len(user_ids),
                probation_or_suspended_count=at_risk,
                note=None if at_risk else "No standing records for some students.",
            )
        )
    return summaries