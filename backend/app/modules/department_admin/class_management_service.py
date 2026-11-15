"""Department Admin — batches, sections, class structure, transfers."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.academics.curriculum_models import SectionOffering
from app.modules.academics.models import AcademicYearContext
from app.modules.department_admin.audit_helpers import record_department_audit
from app.modules.auth.models import User
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.college_admin.student_admin_models import StudentRecord
from app.modules.department_admin.class_management_helpers import (
    assert_programme_in_department,
    section_enrolled_count,
)
from app.modules.department_admin.department_scope import assert_faculty_visible_to_department, department_programme_codes
from app.modules.department_admin.models import (
    DepartmentBatch,
    DepartmentBatchStatus,
    DepartmentSection,
    DepartmentSectionStatus,
)
from app.modules.department_admin.phase3_schemas import (
    BatchCreate,
    BatchRead,
    BatchUpdate,
    ClassStrengthSummary,
    ClassStructureNode,
    SectionCreate,
    SectionRead,
    SectionUpdate,
)
from app.modules.department_admin.policy import resolve_authorized_department
from app.modules.faculty.enums import AssignmentStatus
from app.modules.faculty.models import FacultyAssignment
from app.modules.students.models import StudentProfile


async def list_batches(scope: AccessScope, user: User, *, pagination: Pagination) -> Page[BatchRead]:
    authorize(scope, Permission.DEPARTMENT_CLASS_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    query = DepartmentBatch.find(
        Eq(DepartmentBatch.tenant_id, tenant_id),
        Eq(DepartmentBatch.central_department_id, central_id),
    )
    total = await query.count()
    rows = await query.sort("+programme_code", "+batch_label").skip(pagination.offset).limit(pagination.limit).to_list()
    items: list[BatchRead] = []
    for row in rows:
        sections = await DepartmentSection.find(Eq(DepartmentSection.department_batch_id, row.id)).count()
        students = await StudentProfile.find(
            {
                "tenant_id": tenant_id,
                "department_id": central_id,
                "programme_code": row.programme_code,
                "batch_label": row.batch_label,
            }
        ).count()
        items.append(
            BatchRead(
                batch_id=str(row.id),
                programme_code=row.programme_code,
                batch_label=row.batch_label,
                admission_year=row.admission_year,
                expected_completion_year=row.expected_completion_year,
                curriculum_version=row.curriculum_version,
                academic_year_label=row.academic_year_label,
                status=row.status,
                student_count=students,
                section_count=sections,
                updated_at=row.updated_at,
            )
        )
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def create_batch(scope: AccessScope, user: User, payload: BatchCreate) -> BatchRead:
    authorize(scope, Permission.DEPARTMENT_CLASS_MANAGE)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    code = payload.programme_code.upper()
    await assert_programme_in_department(institution, code)
    label = payload.batch_label.strip()
    if await DepartmentBatch.find_one(
        Eq(DepartmentBatch.tenant_id, tenant_id),
        Eq(DepartmentBatch.central_department_id, central_id),
        Eq(DepartmentBatch.programme_code, code),
        Eq(DepartmentBatch.batch_label, label),
    ):
        raise AppError(code="CONFLICT", message="Batch already exists", status_code=409)
    doc = DepartmentBatch(
        tenant_id=tenant_id,
        institution_department_id=institution.id,
        central_department_id=central_id,
        programme_code=code,
        batch_label=label,
        admission_year=payload.admission_year,
        expected_completion_year=payload.expected_completion_year,
        curriculum_version=payload.curriculum_version,
        academic_year_label=payload.academic_year_label,
        status=payload.status or DepartmentBatchStatus.DRAFT,
        updated_by=user.id,
    )
    await doc.insert()
    await record_department_audit(
        actor_id=user.id,
        action="department.batch.create",
        resource_type="department_batch",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    page = await list_batches(scope, user, pagination=Pagination(limit=1, offset=0))
    for item in page.items:
        if item.batch_id == str(doc.id):
            return item
    return BatchRead(
        batch_id=str(doc.id),
        programme_code=doc.programme_code,
        batch_label=doc.batch_label,
        admission_year=doc.admission_year,
        expected_completion_year=doc.expected_completion_year,
        curriculum_version=doc.curriculum_version,
        academic_year_label=doc.academic_year_label,
        status=doc.status,
        updated_at=doc.updated_at,
    )


async def get_batch(scope: AccessScope, user: User, batch_id: str) -> BatchRead:
    authorize(scope, Permission.DEPARTMENT_CLASS_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentBatch.get(to_object_id(batch_id, "batch_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Batch not found", status_code=404)
    page = await list_batches(scope, user, pagination=Pagination(limit=1000, offset=0))
    for item in page.items:
        if item.batch_id == batch_id:
            return item
    raise AppError(code="NOT_FOUND", message="Batch not found", status_code=404)


async def update_batch(scope: AccessScope, user: User, batch_id: str, payload: BatchUpdate) -> BatchRead:
    authorize(scope, Permission.DEPARTMENT_CLASS_MANAGE)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentBatch.get(to_object_id(batch_id, "batch_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Batch not found", status_code=404)
    if doc.status == DepartmentBatchStatus.ARCHIVED:
        raise AppError(code="FORBIDDEN", message="Archived batch cannot be modified", status_code=403)
    for field in ("admission_year", "expected_completion_year", "curriculum_version", "academic_year_label", "status"):
        value = getattr(payload, field)
        if value is not None:
            setattr(doc, field, value)
    doc.revision += 1
    doc.updated_at = utcnow()
    doc.updated_by = user.id
    await doc.save()
    return await get_batch(scope, user, batch_id)


async def _section_read(
    tenant_id: PydanticObjectId,
    central_id: PydanticObjectId,
    batch: DepartmentBatch,
    section: DepartmentSection,
) -> SectionRead:
    enrolled = await section_enrolled_count(
        tenant_id,
        central_id,
        programme_code=batch.programme_code,
        batch_label=batch.batch_label,
        section_code=section.section_code,
    )
    return SectionRead(
        section_id=str(section.id),
        batch_id=str(batch.id),
        section_code=section.section_code,
        name=section.name,
        capacity=section.capacity,
        enrolled_count=enrolled,
        capacity_available=max(section.capacity - enrolled, 0),
        coordinator_user_id=str(section.coordinator_user_id) if section.coordinator_user_id else None,
        status=section.status,
        over_capacity=enrolled > section.capacity,
    )


async def list_sections(scope: AccessScope, user: User, batch_id: str) -> list[SectionRead]:
    authorize(scope, Permission.DEPARTMENT_CLASS_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    batch = await DepartmentBatch.get(to_object_id(batch_id, "batch_id"))
    if batch is None or batch.tenant_id != tenant_id or batch.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Batch not found", status_code=404)
    rows = await DepartmentSection.find(Eq(DepartmentSection.department_batch_id, batch.id)).sort("+section_code").to_list()
    return [await _section_read(tenant_id, central_id, batch, row) for row in rows]


async def create_section(scope: AccessScope, user: User, batch_id: str, payload: SectionCreate) -> SectionRead:
    authorize(scope, Permission.DEPARTMENT_CLASS_MANAGE)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    batch = await DepartmentBatch.get(to_object_id(batch_id, "batch_id"))
    if batch is None or batch.tenant_id != tenant_id or batch.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Batch not found", status_code=404)
    code = payload.section_code.upper()
    if await DepartmentSection.find_one(
        Eq(DepartmentSection.tenant_id, tenant_id),
        Eq(DepartmentSection.department_batch_id, batch.id),
        Eq(DepartmentSection.section_code, code),
    ):
        raise AppError(code="CONFLICT", message="Section code already exists in batch", status_code=409)
    coordinator = (
        to_object_id(payload.coordinator_user_id, "coordinator_user_id") if payload.coordinator_user_id else None
    )
    if coordinator:
        await assert_faculty_visible_to_department(tenant_id, central_id, coordinator)
    doc = DepartmentSection(
        tenant_id=tenant_id,
        department_batch_id=batch.id,
        central_department_id=central_id,
        section_code=code,
        name=payload.name,
        capacity=payload.capacity,
        coordinator_user_id=coordinator,
        status=payload.status or DepartmentSectionStatus.DRAFT,
        updated_by=user.id,
    )
    await doc.insert()
    await record_department_audit(
        actor_id=user.id,
        action="department.section.create",
        resource_type="department_section",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return await _section_read(tenant_id, central_id, batch, doc)


async def get_section(scope: AccessScope, user: User, section_id: str) -> SectionRead:
    authorize(scope, Permission.DEPARTMENT_CLASS_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    section = await DepartmentSection.get(to_object_id(section_id, "section_id"))
    if section is None or section.tenant_id != tenant_id or section.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Section not found", status_code=404)
    batch = await DepartmentBatch.get(section.department_batch_id)
    if batch is None:
        raise AppError(code="NOT_FOUND", message="Batch not found", status_code=404)
    return await _section_read(tenant_id, central_id, batch, section)


async def update_section(scope: AccessScope, user: User, section_id: str, payload: SectionUpdate) -> SectionRead:
    authorize(scope, Permission.DEPARTMENT_CLASS_MANAGE)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    section = await DepartmentSection.get(to_object_id(section_id, "section_id"))
    if section is None or section.tenant_id != tenant_id or section.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Section not found", status_code=404)
    if section.status == DepartmentSectionStatus.ARCHIVED:
        raise AppError(code="FORBIDDEN", message="Archived section cannot be modified", status_code=403)
    if payload.name is not None:
        section.name = payload.name
    if payload.capacity is not None:
        section.capacity = payload.capacity
    if payload.coordinator_user_id is not None:
        coord = to_object_id(payload.coordinator_user_id, "coordinator_user_id")
        await assert_faculty_visible_to_department(tenant_id, central_id, coord)
        section.coordinator_user_id = coord
    if payload.status is not None:
        section.status = payload.status
    section.revision += 1
    section.updated_at = utcnow()
    section.updated_by = user.id
    await section.save()
    batch = await DepartmentBatch.get(section.department_batch_id)
    assert batch is not None
    return await _section_read(tenant_id, central_id, batch, section)


async def class_structure(scope: AccessScope, user: User) -> list[ClassStructureNode]:
    authorize(scope, Permission.DEPARTMENT_CLASS_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    ctx = await AcademicYearContext.find_one(Eq(AcademicYearContext.tenant_id, tenant_id), Eq(AcademicYearContext.is_current, True))
    year = ctx.academic_year_label if ctx else None
    semester = ctx.semester_label if ctx else None
    batches = await DepartmentBatch.find(
        Eq(DepartmentBatch.tenant_id, tenant_id),
        Eq(DepartmentBatch.central_department_id, central_id),
    ).to_list()
    nodes: list[ClassStructureNode] = []
    for batch in batches:
        sections = await list_sections(scope, user, str(batch.id))
        offer_filters: dict = {"tenant_id": tenant_id, "batch_label": batch.batch_label}
        if year:
            offer_filters["academic_year_label"] = year
        if semester:
            offer_filters["semester_label"] = semester
        offerings = await SectionOffering.find(offer_filters).count()
        assign_filters: dict = {
            "tenant_id": tenant_id,
            "status": AssignmentStatus.ACTIVE,
        }
        if year:
            assign_filters["academic_year_label"] = year
        if semester:
            assign_filters["semester_label"] = semester
        assignments = await FacultyAssignment.find(assign_filters).count()
        nodes.append(
            ClassStructureNode(
                programme_code=batch.programme_code,
                batch_label=batch.batch_label,
                batch_status=batch.status,
                sections=sections,
                offerings_count=offerings,
                faculty_assignments_count=assignments,
            )
        )
    return nodes


async def class_strength(scope: AccessScope, user: User) -> list[ClassStrengthSummary]:
    authorize(scope, Permission.DEPARTMENT_CLASS_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    summaries: list[ClassStrengthSummary] = []
    batches = await DepartmentBatch.find(
        Eq(DepartmentBatch.tenant_id, tenant_id),
        Eq(DepartmentBatch.central_department_id, central_id),
    ).to_list()
    for batch in batches:
        sections = await DepartmentSection.find(Eq(DepartmentSection.department_batch_id, batch.id)).to_list()
        batch_total = await StudentProfile.find(
            {
                "tenant_id": tenant_id,
                "department_id": central_id,
                "programme_code": batch.programme_code,
                "batch_label": batch.batch_label,
            }
        ).count()
        allocated = 0
        for section in sections:
            enrolled = await section_enrolled_count(
                tenant_id,
                central_id,
                programme_code=batch.programme_code,
                batch_label=batch.batch_label,
                section_code=section.section_code,
            )
            allocated += enrolled
            summaries.append(
                ClassStrengthSummary(
                    programme_code=batch.programme_code,
                    batch_label=batch.batch_label,
                    section_code=section.section_code,
                    enrolled=enrolled,
                    capacity=section.capacity,
                    unallocated_in_batch=0,
                )
            )
        summaries.append(
            ClassStrengthSummary(
                programme_code=batch.programme_code,
                batch_label=batch.batch_label,
                section_code=None,
                enrolled=batch_total,
                capacity=None,
                unallocated_in_batch=max(batch_total - allocated, 0),
            )
        )
    return summaries

