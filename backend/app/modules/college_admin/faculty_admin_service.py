"""Faculty and employee administration services."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.roles import Role
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import (
    EmployeeRecord,
    FacultyDepartmentAssignment,
    FacultyDocumentReference,
    FacultyEmploymentHistory,
    FacultyEmploymentStatus,
    FacultyRecord,
    FacultyTeachingAssignment,
    FacultyWorkloadRecord,
)
from app.modules.college_admin.faculty_admin_schemas import (
    BulkFacultyImport,
    DepartmentAssignmentCreate,
    FacultyDocumentCreate,
    FacultyHistoryRead,
    FacultyRecordCreate,
    FacultyRecordRead,
    FacultyRecordUpdate,
    FacultyTransferCreate,
    TeachingAssignmentCreate,
    WorkloadAllocate,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.faculty.models import FacultyAssignment, FacultyProfile, FacultyWorkload
from app.modules.hr.models import EmployeeProfileSnapshot
from app.modules.tenants.models import Department
from app.repositories.user_repository import UserRepository

_user_repo = UserRepository()

_ADMIN_UPDATABLE = frozenset(
    {
        "faculty_code",
        "designation",
        "department_id",
        "campus_id",
        "specialization",
        "qualifications",
        "experience_years",
        "employment_status",
    }
)


async def _sync_faculty_profile(record: FacultyRecord, user: User, *, contact_phone: str | None = None, office_location: str | None = None) -> None:
    profile = await FacultyProfile.find_one(
        Eq(FacultyProfile.tenant_id, record.tenant_id),
        Eq(FacultyProfile.user_id, user.id),
    )
    if profile is None:
        profile = FacultyProfile(tenant_id=record.tenant_id, user_id=user.id)
    if record.employee_record_id:
        employee = await EmployeeRecord.get(record.employee_record_id)
        if employee and employee.employee_id:
            profile.employee_id = employee.employee_id
    profile.faculty_code = record.faculty_code
    profile.designation = record.designation
    profile.department_id = record.department_id
    profile.specialization = record.specialization
    profile.qualifications = record.qualifications
    if contact_phone is not None:
        profile.contact_phone = contact_phone
    if office_location is not None:
        profile.office_location = office_location
    profile.updated_at = utcnow()
    if profile.id is None:
        await profile.insert()
    else:
        await profile.save()


async def _sync_employee_snapshot(employee: EmployeeRecord) -> None:
    dept_name = None
    if employee.department_id:
        dept = await Department.get(employee.department_id)
        if dept and dept.tenant_id == employee.tenant_id:
            dept_name = dept.name
    snapshot = await EmployeeProfileSnapshot.find_one(
        Eq(EmployeeProfileSnapshot.tenant_id, employee.tenant_id),
        Eq(EmployeeProfileSnapshot.employee_user_id, employee.user_id),
    )
    if snapshot is None:
        snapshot = EmployeeProfileSnapshot(tenant_id=employee.tenant_id, employee_user_id=employee.user_id)
    snapshot.employee_id = employee.employee_id
    snapshot.designation = employee.designation
    snapshot.department_name = dept_name
    snapshot.joining_date = employee.joining_date
    snapshot.employment_type = employee.employment_type
    snapshot.permitted_fields = {
        "employee_id": employee.employee_id,
        "designation": employee.designation,
        "department_name": dept_name,
        "joining_date": employee.joining_date.isoformat() if employee.joining_date else None,
        "employment_type": employee.employment_type,
    }
    snapshot.updated_at = utcnow()
    if snapshot.id is None:
        await snapshot.insert()
    else:
        await snapshot.save()


async def create_faculty_record(scope: AccessScope, payload: FacultyRecordCreate) -> FacultyRecordRead:
    authorize(scope, Permission.FACULTY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    email = str(payload.email).lower()
    if await _user_repo.find_by_email_in_tenant(email, tenant_id):
        raise AppError(code="CONFLICT", message="Email already exists", status_code=409)
    if payload.employee_id:
        if await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.employee_id, payload.employee_id)):
            raise AppError(code="CONFLICT", message="Employee identifier already assigned", status_code=409)
    if payload.faculty_code:
        if await FacultyRecord.find_one(Eq(FacultyRecord.tenant_id, tenant_id), Eq(FacultyRecord.faculty_code, payload.faculty_code)):
            raise AppError(code="CONFLICT", message="Faculty code already assigned", status_code=409)

    dept_id = to_object_id(payload.department_id, "department_id") if payload.department_id else None
    if dept_id:
        dept = await Department.get(dept_id)
        if dept is None or dept.tenant_id != tenant_id:
            raise AppError(code="VALIDATION_ERROR", message="Invalid department", status_code=422)

    campus_id = to_object_id(payload.campus_id, "campus_id") if payload.campus_id else None
    user = User(
        email=email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        role=Role.FACULTY,
        tenant_id=tenant_id,
        department_id=dept_id,
    )
    await user.insert()

    employee = EmployeeRecord(
        tenant_id=tenant_id,
        user_id=user.id,
        employee_id=payload.employee_id,
        employment_type=payload.employment_type,
        joining_date=payload.joining_date,
        designation=payload.designation,
        department_id=dept_id,
        campus_id=campus_id,
        is_faculty=True,
        updated_by=scope.user_id,
    )
    await employee.insert()

    record = FacultyRecord(
        tenant_id=tenant_id,
        user_id=user.id,
        employee_record_id=employee.id,
        faculty_code=payload.faculty_code,
        designation=payload.designation,
        department_id=dept_id,
        campus_id=campus_id,
        specialization=payload.specialization,
        updated_by=scope.user_id,
    )
    await record.insert()
    await _sync_faculty_profile(record, user)
    await _sync_employee_snapshot(employee)
    if dept_id:
        await FacultyDepartmentAssignment(
            tenant_id=tenant_id,
            user_id=user.id,
            department_id=dept_id,
            campus_id=campus_id,
            is_primary=True,
            actor_id=scope.user_id,
        ).insert()
    await FacultyEmploymentHistory(
        tenant_id=tenant_id,
        user_id=user.id,
        event_type="hired",
        to_status=FacultyEmploymentStatus.ACTIVE.value,
        actor_id=scope.user_id,
        note="Faculty record created",
    ).insert()
    from app.modules.audit.service import record_audit

    await record_audit(
        actor_id=scope.user_id,
        action="college.faculty.created",
        resource_type="faculty_record",
        resource_id=str(record.id),
        tenant_id=tenant_id,
    )
    return FacultyRecordRead.from_parts(record, employee, full_name=user.full_name, email=user.email)


async def get_faculty_record(scope: AccessScope, record_id: PydanticObjectId) -> FacultyRecordRead:
    authorize(scope, Permission.FACULTY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    record = await FacultyRecord.get(record_id)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Faculty record not found", status_code=404)
    user = await _user_repo.get(record.user_id)
    if user is None:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, record.user_id))
    return FacultyRecordRead.from_parts(record, employee, full_name=user.full_name, email=user.email)


async def list_faculty_records(scope: AccessScope, pagination: Pagination) -> Page[FacultyRecordRead]:
    authorize(scope, Permission.FACULTY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    total = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).count()
    rows = (
        await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id))
        .sort("-created_at")
        .skip(pagination.offset)
        .limit(pagination.limit)
        .to_list()
    )
    items: list[FacultyRecordRead] = []
    for record in rows:
        user = await _user_repo.get(record.user_id)
        if user:
            employee = await EmployeeRecord.find_one(
                Eq(EmployeeRecord.tenant_id, tenant_id),
                Eq(EmployeeRecord.user_id, record.user_id),
            )
            items.append(FacultyRecordRead.from_parts(record, employee, full_name=user.full_name, email=user.email))
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def update_faculty_record(scope: AccessScope, record_id: PydanticObjectId, payload: FacultyRecordUpdate) -> FacultyRecordRead:
    authorize(scope, Permission.FACULTY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    record = await FacultyRecord.get(record_id)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Faculty record not found", status_code=404)
    data = payload.model_dump(exclude_none=True)
    if "faculty_code" in data and data["faculty_code"] != record.faculty_code:
        dup = await FacultyRecord.find_one(Eq(FacultyRecord.tenant_id, tenant_id), Eq(FacultyRecord.faculty_code, data["faculty_code"]))
        if dup and dup.id != record.id:
            raise AppError(code="CONFLICT", message="Faculty code already assigned", status_code=409)
    contact_phone = data.pop("contact_phone", None)
    office_location = data.pop("office_location", None)
    for key in list(data.keys()):
        if key not in _ADMIN_UPDATABLE:
            data.pop(key, None)
    if "department_id" in data:
        data["department_id"] = to_object_id(data["department_id"], "department_id")
    if "campus_id" in data:
        data["campus_id"] = to_object_id(data["campus_id"], "campus_id")
    for key, value in data.items():
        setattr(record, key, value)
    record.updated_at = utcnow()
    record.updated_by = scope.user_id
    await record.save()

    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, record.user_id))
    if employee:
        if record.designation:
            employee.designation = record.designation
        if record.department_id:
            employee.department_id = record.department_id
        if record.campus_id:
            employee.campus_id = record.campus_id
        if payload.employment_status:
            employee.employment_status = payload.employment_status
        employee.updated_at = utcnow()
        await employee.save()
        await _sync_employee_snapshot(employee)

    user = await _user_repo.get(record.user_id)
    if user and record.department_id:
        user.department_id = record.department_id
        await user.save()
    if user:
        await _sync_faculty_profile(record, user, contact_phone=contact_phone, office_location=office_location)
    if user is None:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    return FacultyRecordRead.from_parts(record, employee, full_name=user.full_name, email=user.email)


async def assign_department(scope: AccessScope, record_id: PydanticObjectId, payload: DepartmentAssignmentCreate) -> dict:
    authorize(scope, Permission.FACULTY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    record = await FacultyRecord.get(record_id)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Faculty record not found", status_code=404)
    dept_id = to_object_id(payload.department_id, "department_id")
    dept = await Department.get(dept_id)
    if dept is None or dept.tenant_id != tenant_id:
        raise AppError(code="VALIDATION_ERROR", message="Invalid department", status_code=422)
    campus_id = to_object_id(payload.campus_id, "campus_id") if payload.campus_id else None
    if payload.is_primary:
        for prev in await FacultyDepartmentAssignment.find(
            Eq(FacultyDepartmentAssignment.tenant_id, tenant_id),
            Eq(FacultyDepartmentAssignment.user_id, record.user_id),
            Eq(FacultyDepartmentAssignment.is_primary, True),
        ).to_list():
            prev.is_primary = False
            prev.effective_to = utcnow().date()
            await prev.save()
        record.department_id = dept_id
        record.campus_id = campus_id
        await record.save()
        user = await _user_repo.get(record.user_id)
        if user:
            user.department_id = dept_id
            await user.save()
            await _sync_faculty_profile(record, user)
    row = FacultyDepartmentAssignment(
        tenant_id=tenant_id,
        user_id=record.user_id,
        department_id=dept_id,
        campus_id=campus_id,
        is_primary=payload.is_primary,
        effective_from=payload.effective_from,
        actor_id=scope.user_id,
    )
    await row.insert()
    return {"assignment_id": str(row.id)}


async def assign_teaching(scope: AccessScope, record_id: PydanticObjectId, payload: TeachingAssignmentCreate) -> dict:
    authorize(scope, Permission.FACULTY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    record = await FacultyRecord.get(record_id)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Faculty record not found", status_code=404)
    assignment = FacultyAssignment(
        tenant_id=tenant_id,
        user_id=record.user_id,
        academic_year_label=payload.academic_year_label,
        semester_label=payload.semester_label,
        course_id=payload.course_id,
        course_code=payload.course_code.upper(),
        course_name=payload.course_name,
        subject_id=payload.subject_id,
        subject_code=payload.subject_code,
        subject_name=payload.subject_name,
        section=payload.section.upper(),
        allocation_locked=True,
        change_note="Assigned by college admin",
    )
    await assignment.insert()
    log = FacultyTeachingAssignment(
        tenant_id=tenant_id,
        user_id=record.user_id,
        faculty_assignment_id=assignment.id,
        academic_year_label=payload.academic_year_label,
        semester_label=payload.semester_label,
        course_code=assignment.course_code,
        section=assignment.section,
        actor_id=scope.user_id,
    )
    await log.insert()
    return {"assignment_id": str(assignment.id), "log_id": str(log.id)}


async def allocate_workload(scope: AccessScope, record_id: PydanticObjectId, payload: WorkloadAllocate) -> dict:
    authorize(scope, Permission.FACULTY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    record = await FacultyRecord.get(record_id)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Faculty record not found", status_code=404)
    total = payload.lecture_hours + payload.lab_hours + payload.tutorial_hours
    workload = await FacultyWorkload.find_one(
        Eq(FacultyWorkload.tenant_id, tenant_id),
        Eq(FacultyWorkload.user_id, record.user_id),
        Eq(FacultyWorkload.academic_year_label, payload.academic_year_label),
        Eq(FacultyWorkload.semester_label, payload.semester_label),
    )
    if workload is None:
        workload = FacultyWorkload(
            tenant_id=tenant_id,
            user_id=record.user_id,
            academic_year_label=payload.academic_year_label,
            semester_label=payload.semester_label,
        )
    workload.lecture_hours = payload.lecture_hours
    workload.lab_hours = payload.lab_hours
    workload.tutorial_hours = payload.tutorial_hours
    workload.total_hours = total
    workload.credit_units = payload.credit_units
    workload.computed_at = utcnow()
    if workload.id is None:
        await workload.insert()
    else:
        await workload.save()
    hist = FacultyWorkloadRecord(
        tenant_id=tenant_id,
        user_id=record.user_id,
        academic_year_label=payload.academic_year_label,
        semester_label=payload.semester_label,
        lecture_hours=payload.lecture_hours,
        lab_hours=payload.lab_hours,
        tutorial_hours=payload.tutorial_hours,
        total_hours=total,
        credit_units=payload.credit_units,
        note=payload.note,
        actor_id=scope.user_id,
    )
    await hist.insert()
    return {"workload_id": str(workload.id), "history_id": str(hist.id)}


async def get_workload(scope: AccessScope, record_id: PydanticObjectId, *, academic_year_label: str, semester_label: str) -> dict:
    authorize(scope, Permission.FACULTY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    record = await FacultyRecord.get(record_id)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Faculty record not found", status_code=404)
    workload = await FacultyWorkload.find_one(
        Eq(FacultyWorkload.tenant_id, tenant_id),
        Eq(FacultyWorkload.user_id, record.user_id),
        Eq(FacultyWorkload.academic_year_label, academic_year_label),
        Eq(FacultyWorkload.semester_label, semester_label),
    )
    if workload is None:
        return {"total_hours": 0, "lecture_hours": 0, "lab_hours": 0, "tutorial_hours": 0, "credit_units": 0}
    return {
        "total_hours": workload.total_hours,
        "lecture_hours": workload.lecture_hours,
        "lab_hours": workload.lab_hours,
        "tutorial_hours": workload.tutorial_hours,
        "credit_units": workload.credit_units,
        "computed_at": workload.computed_at,
    }


async def process_faculty_transfer(scope: AccessScope, record_id: PydanticObjectId, payload: FacultyTransferCreate) -> dict:
    authorize(scope, Permission.FACULTY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    record = await FacultyRecord.get(record_id)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Faculty record not found", status_code=404)
    to_dept = to_object_id(payload.to_department_id, "to_department_id")
    dept = await Department.get(to_dept)
    if dept is None or dept.tenant_id != tenant_id:
        raise AppError(code="VALIDATION_ERROR", message="Invalid department", status_code=422)
    from_status = record.employment_status.value
    campus_id = to_object_id(payload.campus_id, "campus_id") if payload.campus_id else None
    record.department_id = to_dept
    record.campus_id = campus_id
    record.employment_status = FacultyEmploymentStatus.TRANSFERRED
    record.updated_at = utcnow()
    await record.save()
    user = await _user_repo.get(record.user_id)
    if user:
        user.department_id = to_dept
        await user.save()
        await _sync_faculty_profile(record, user)
    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, record.user_id))
    if employee:
        employee.department_id = to_dept
        employee.campus_id = campus_id
        employee.employment_status = FacultyEmploymentStatus.TRANSFERRED
        employee.updated_at = utcnow()
        await employee.save()
        await _sync_employee_snapshot(employee)
    await FacultyDepartmentAssignment(
        tenant_id=tenant_id,
        user_id=record.user_id,
        department_id=to_dept,
        campus_id=campus_id,
        is_primary=True,
        effective_from=payload.effective_date,
        actor_id=scope.user_id,
    ).insert()
    await FacultyEmploymentHistory(
        tenant_id=tenant_id,
        user_id=record.user_id,
        event_type="transfer",
        from_status=from_status,
        to_status=FacultyEmploymentStatus.TRANSFERRED.value,
        note=payload.reason,
        effective_date=payload.effective_date,
        actor_id=scope.user_id,
    ).insert()
    return {"record_id": str(record.id)}


async def add_faculty_document(scope: AccessScope, record_id: PydanticObjectId, payload: FacultyDocumentCreate) -> dict:
    authorize(scope, Permission.FACULTY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    record = await FacultyRecord.get(record_id)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Faculty record not found", status_code=404)
    doc = FacultyDocumentReference(
        tenant_id=tenant_id,
        user_id=record.user_id,
        label=payload.label,
        file_id=payload.file_id,
        document_type=payload.document_type,
        actor_id=scope.user_id,
    )
    await doc.insert()
    return {"document_id": str(doc.id)}


async def faculty_history(scope: AccessScope, record_id: PydanticObjectId) -> FacultyHistoryRead:
    authorize(scope, Permission.FACULTY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    record = await FacultyRecord.get(record_id)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Faculty record not found", status_code=404)
    employment = await FacultyEmploymentHistory.find(Eq(FacultyEmploymentHistory.tenant_id, tenant_id), Eq(FacultyEmploymentHistory.user_id, record.user_id)).sort("-created_at").to_list()
    depts = await FacultyDepartmentAssignment.find(
        Eq(FacultyDepartmentAssignment.tenant_id, tenant_id),
        Eq(FacultyDepartmentAssignment.user_id, record.user_id),
    ).sort("-created_at").to_list()
    teaching = await FacultyTeachingAssignment.find(
        Eq(FacultyTeachingAssignment.tenant_id, tenant_id),
        Eq(FacultyTeachingAssignment.user_id, record.user_id),
    ).sort("-created_at").to_list()
    workload = await FacultyWorkloadRecord.find(
        Eq(FacultyWorkloadRecord.tenant_id, tenant_id),
        Eq(FacultyWorkloadRecord.user_id, record.user_id),
    ).sort("-created_at").to_list()
    return FacultyHistoryRead(
        employment=[e.model_dump(mode="json") for e in employment],
        department_assignments=[d.model_dump(mode="json") for d in depts],
        teaching=[t.model_dump(mode="json") for t in teaching],
        workload=[w.model_dump(mode="json") for w in workload],
    )


async def bulk_import_faculty(scope: AccessScope, payload: BulkFacultyImport) -> list[FacultyRecordRead]:
    authorize(scope, Permission.FACULTY_ADMIN_MANAGE)
    if len(payload.items) > 100:
        raise AppError(code="VALIDATION_ERROR", message="Maximum 100 rows per import", status_code=422)
    created: list[FacultyRecordRead] = []
    for item in payload.items:
        created.append(await create_faculty_record(scope, item))
    return created
