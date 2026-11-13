"""Student administration services."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.roles import Role
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.core.exceptions import AppError
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.student_admin_models import (
    AdmissionStatus,
    StudentAdmission,
    StudentGuardianRelationship,
    StudentLifecycleStatus,
    StudentPromotionRecord,
    StudentRecord,
    StudentStatusHistory,
    StudentTransfer,
    TransferStatus,
)
from app.modules.college_admin.student_admin_schemas import (
    AdmissionCreate,
    AdmissionRead,
    BulkStudentImport,
    EnrollmentAssign,
    GuardianCreate,
    ProfileCorrectionDecision,
    PromotionCreate,
    StudentAcademicHistoryRead,
    StudentRecordCreate,
    StudentRecordRead,
    StudentRecordUpdate,
    StudentStatusChange,
    TransferCreate,
)
from app.modules.students.enums import StudentEnrollmentStatus
from app.modules.students.models import StudentEnrollment, StudentProfile
from app.modules.students.student_portal_enums import StudentDocumentRequestStatus
from app.modules.students.student_portal_models import StudentProfileCorrectionRequest
from app.repositories.user_repository import UserRepository

_user_repo = UserRepository()


async def _sync_profile(record: StudentRecord, user: User) -> None:
    profile = await StudentProfile.find_one(Eq(StudentProfile.tenant_id, record.tenant_id), Eq(StudentProfile.user_id, user.id))
    if profile is None:
        profile = StudentProfile(tenant_id=record.tenant_id, user_id=user.id)
    profile.student_id = record.student_id
    profile.roll_number = record.roll_number
    profile.admission_number = record.admission_number
    profile.department_id = record.department_id
    profile.programme_code = record.programme_code
    profile.batch_label = record.batch_label
    profile.section_code = record.section_code
    profile.contact_phone = record.contact_phone
    profile.official_locked = True
    profile.updated_at = utcnow()
    if profile.id is None:
        await profile.insert()
    else:
        await profile.save()


async def _append_status_history(
    *,
    tenant_id: PydanticObjectId,
    record: StudentRecord,
    from_status: str,
    to_status: str,
    actor_id: PydanticObjectId | None,
    reason: str | None,
) -> None:
    await StudentStatusHistory(
        tenant_id=tenant_id,
        student_record_id=record.id,
        user_id=record.user_id,
        from_status=from_status,
        to_status=to_status,
        reason=reason,
        actor_id=actor_id,
    ).insert()


async def create_admission(scope: AccessScope, payload: AdmissionCreate) -> AdmissionRead:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    number = payload.admission_number.upper()
    if await StudentAdmission.find_one(Eq(StudentAdmission.tenant_id, tenant_id), Eq(StudentAdmission.admission_number, number)):
        raise AppError(code="CONFLICT", message="Admission number already exists", status_code=409)
    doc = StudentAdmission(
        tenant_id=tenant_id,
        admission_number=number,
        applicant_name=payload.applicant_name.strip(),
        applicant_email=str(payload.applicant_email).lower(),
        programme_code=payload.programme_code.upper(),
        department_id=to_object_id(payload.department_id, "department_id") if payload.department_id else None,
        batch_label=payload.batch_label,
        academic_year_code=payload.academic_year_code,
        updated_by=scope.user_id,
    )
    await doc.insert()
    return AdmissionRead.from_document(doc)


async def list_admissions(scope: AccessScope, pagination: Pagination) -> Page[AdmissionRead]:
    authorize(scope, Permission.STUDENT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    total = await StudentAdmission.find(Eq(StudentAdmission.tenant_id, tenant_id)).count()
    rows = await StudentAdmission.find(Eq(StudentAdmission.tenant_id, tenant_id)).sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[AdmissionRead.from_document(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def confirm_admission(scope: AccessScope, admission_id: PydanticObjectId) -> AdmissionRead:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    admission = await StudentAdmission.get(admission_id)
    if admission is None or admission.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Admission not found", status_code=404)
    admission.status = AdmissionStatus.CONFIRMED
    admission.updated_at = utcnow()
    admission.updated_by = scope.user_id
    await admission.save()
    return AdmissionRead.from_document(admission)


async def create_student_record(scope: AccessScope, payload: StudentRecordCreate) -> StudentRecordRead:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    email = str(payload.email).lower()
    if await _user_repo.find_by_email_in_tenant(email, tenant_id):
        raise AppError(code="CONFLICT", message="Email already exists", status_code=409)

    if payload.roll_number:
        dup_roll = await StudentRecord.find_one(Eq(StudentRecord.tenant_id, tenant_id), Eq(StudentRecord.roll_number, payload.roll_number))
        if dup_roll:
            raise AppError(code="CONFLICT", message="Roll number already assigned", status_code=409)
    if payload.student_id:
        dup_id = await StudentRecord.find_one(Eq(StudentRecord.tenant_id, tenant_id), Eq(StudentRecord.student_id, payload.student_id))
        if dup_id:
            raise AppError(code="CONFLICT", message="Student identifier already assigned", status_code=409)

    admission = None
    if payload.admission_id:
        admission = await StudentAdmission.get(to_object_id(payload.admission_id, "admission_id"))
        if admission is None or admission.tenant_id != tenant_id:
            raise AppError(code="NOT_FOUND", message="Admission not found", status_code=404)

    user = User(
        email=email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        role=Role.STUDENT,
        tenant_id=tenant_id,
        department_id=to_object_id(payload.department_id, "department_id") if payload.department_id else (admission.department_id if admission else None),
    )
    await user.insert()

    record = StudentRecord(
        tenant_id=tenant_id,
        user_id=user.id,
        student_id=payload.student_id,
        roll_number=payload.roll_number,
        admission_id=admission.id if admission else None,
        admission_number=admission.admission_number if admission else None,
        department_id=user.department_id,
        programme_code=(payload.programme_code or (admission.programme_code if admission else None)),
        batch_label=payload.batch_label or (admission.batch_label if admission else None),
        section_code=payload.section_code,
        lifecycle_status=StudentLifecycleStatus.ACTIVE,
        updated_by=scope.user_id,
    )
    await record.insert()
    await _sync_profile(record, user)
    if admission and admission.status == AdmissionStatus.PENDING:
        admission.status = AdmissionStatus.CONFIRMED
        admission.confirmed_user_id = user.id
        await admission.save()
    await _append_status_history(
        tenant_id=tenant_id,
        record=record,
        from_status="none",
        to_status=record.lifecycle_status.value,
        actor_id=scope.user_id,
        reason="Student record created",
    )
    return StudentRecordRead.from_parts(record, full_name=user.full_name, email=user.email)


async def get_student_record(scope: AccessScope, record_id: PydanticObjectId) -> StudentRecordRead:
    authorize(scope, Permission.STUDENT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    record = await StudentRecord.get(record_id)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Student record not found", status_code=404)
    user = await _user_repo.get(record.user_id)
    if user is None:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    return StudentRecordRead.from_parts(record, full_name=user.full_name, email=user.email)


async def list_student_records(scope: AccessScope, pagination: Pagination) -> Page[StudentRecordRead]:
    authorize(scope, Permission.STUDENT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    total = await StudentRecord.find(Eq(StudentRecord.tenant_id, tenant_id)).count()
    records = await StudentRecord.find(Eq(StudentRecord.tenant_id, tenant_id)).sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    items: list[StudentRecordRead] = []
    for record in records:
        user = await _user_repo.get(record.user_id)
        if user:
            items.append(StudentRecordRead.from_parts(record, full_name=user.full_name, email=user.email))
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def update_student_record(scope: AccessScope, record_id: PydanticObjectId, payload: StudentRecordUpdate) -> StudentRecordRead:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    record = await StudentRecord.get(record_id)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Student record not found", status_code=404)
    if payload.roll_number and payload.roll_number != record.roll_number:
        if await StudentRecord.find_one(Eq(StudentRecord.tenant_id, tenant_id), Eq(StudentRecord.roll_number, payload.roll_number)):
            raise AppError(code="CONFLICT", message="Roll number already assigned", status_code=409)
        record.roll_number = payload.roll_number
    if payload.programme_code is not None:
        record.programme_code = payload.programme_code.upper()
    if payload.batch_label is not None:
        record.batch_label = payload.batch_label
    if payload.section_code is not None:
        record.section_code = payload.section_code
    if payload.department_id is not None:
        record.department_id = to_object_id(payload.department_id, "department_id")
    if payload.contact_phone is not None:
        record.contact_phone = payload.contact_phone
    record.updated_at = utcnow()
    record.updated_by = scope.user_id
    await record.save()
    user = await _user_repo.get(record.user_id)
    if user and record.department_id:
        user.department_id = record.department_id
        await user.save()
    if user:
        await _sync_profile(record, user)
    return StudentRecordRead.from_parts(record, full_name=user.full_name if user else "", email=user.email if user else "")


async def change_student_status(scope: AccessScope, record_id: PydanticObjectId, payload: StudentStatusChange) -> StudentRecordRead:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    record = await StudentRecord.get(record_id)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Student record not found", status_code=404)
    previous = record.lifecycle_status.value
    record.lifecycle_status = payload.lifecycle_status
    if payload.lifecycle_status in (StudentLifecycleStatus.WITHDRAWN, StudentLifecycleStatus.DISCONTINUED):
        record.enrollment_status = StudentEnrollmentStatus.WITHDRAWN
    record.updated_at = utcnow()
    await record.save()
    user = await _user_repo.get(record.user_id)
    if user:
        user.is_active = payload.lifecycle_status == StudentLifecycleStatus.ACTIVE
        await user.save()
        await _sync_profile(record, user)
    await _append_status_history(
        tenant_id=tenant_id,
        record=record,
        from_status=previous,
        to_status=payload.lifecycle_status.value,
        actor_id=scope.user_id,
        reason=payload.reason,
    )
    return StudentRecordRead.from_parts(record, full_name=user.full_name if user else "", email=user.email if user else "")


async def enroll_student(scope: AccessScope, record_id: PydanticObjectId, payload: EnrollmentAssign) -> dict:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    record = await StudentRecord.get(record_id)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Student record not found", status_code=404)
    existing = await StudentEnrollment.find_one(
        {
            "tenant_id": tenant_id,
            "user_id": record.user_id,
            "academic_year_label": payload.academic_year_label,
            "semester_label": payload.semester_label,
            "course_code": payload.course_code.upper(),
        }
    )
    if existing:
        raise AppError(code="CONFLICT", message="Enrollment already exists", status_code=409)
    doc = StudentEnrollment(
        tenant_id=tenant_id,
        user_id=record.user_id,
        academic_year_label=payload.academic_year_label,
        semester_label=payload.semester_label,
        course_id=payload.course_id,
        course_code=payload.course_code.upper(),
        course_name=payload.course_name,
        section_code=payload.section_code.upper(),
        department_id=record.department_id,
        status=StudentEnrollmentStatus.ACTIVE,
        approved_at=utcnow(),
    )
    await doc.insert()
    return {"enrollment_id": str(doc.id)}


async def process_transfer(scope: AccessScope, record_id: PydanticObjectId, payload: TransferCreate) -> dict:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    record = await StudentRecord.get(record_id)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Student record not found", status_code=404)
    transfer = StudentTransfer(
        tenant_id=tenant_id,
        user_id=record.user_id,
        from_department_id=record.department_id,
        to_department_id=to_object_id(payload.to_department_id, "to_department_id") if payload.to_department_id else None,
        from_programme_code=record.programme_code,
        to_programme_code=payload.to_programme_code.upper() if payload.to_programme_code else None,
        reason=payload.reason,
        status=TransferStatus.APPROVED,
        effective_date=payload.effective_date,
        actor_id=scope.user_id,
    )
    await transfer.insert()
    if transfer.to_department_id:
        record.department_id = transfer.to_department_id
    if transfer.to_programme_code:
        record.programme_code = transfer.to_programme_code
    record.lifecycle_status = StudentLifecycleStatus.TRANSFERRED
    record.updated_at = utcnow()
    await record.save()
    user = await _user_repo.get(record.user_id)
    if user:
        if transfer.to_department_id:
            user.department_id = transfer.to_department_id
        await user.save()
        await _sync_profile(record, user)
    transfer.status = TransferStatus.COMPLETED
    transfer.completed_at = utcnow()
    await transfer.save()
    return {"transfer_id": str(transfer.id)}


async def process_promotion(scope: AccessScope, record_id: PydanticObjectId, payload: PromotionCreate) -> dict:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    record = await StudentRecord.get(record_id)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Student record not found", status_code=404)
    promotion = StudentPromotionRecord(
        tenant_id=tenant_id,
        user_id=record.user_id,
        from_academic_year=record.batch_label or "unknown",
        from_semester=record.section_code or "unknown",
        to_academic_year=payload.to_academic_year,
        to_semester=payload.to_semester,
        decision=payload.decision,
        actor_id=scope.user_id,
    )
    await promotion.insert()
    record.batch_label = payload.to_academic_year
    record.section_code = payload.to_semester
    record.updated_at = utcnow()
    await record.save()
    user = await _user_repo.get(record.user_id)
    if user:
        await _sync_profile(record, user)
    return {"promotion_id": str(promotion.id)}


async def add_guardian(scope: AccessScope, record_id: PydanticObjectId, payload: GuardianCreate) -> dict:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    record = await StudentRecord.get(record_id)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Student record not found", status_code=404)
    doc = StudentGuardianRelationship(
        tenant_id=tenant_id,
        user_id=record.user_id,
        guardian_name=payload.guardian_name,
        relationship=payload.relationship,
        phone=payload.phone,
        email=str(payload.email).lower() if payload.email else None,
        portal_access_allowed=payload.portal_access_allowed,
    )
    await doc.insert()
    profile = await StudentProfile.find_one(Eq(StudentProfile.tenant_id, tenant_id), Eq(StudentProfile.user_id, record.user_id))
    if profile and payload.portal_access_allowed:
        from app.modules.students.models import EmergencyContact

        profile.emergency_contacts.append(
            EmergencyContact(name=payload.guardian_name, phone=payload.phone, relationship=payload.relationship)
        )
        profile.updated_at = utcnow()
        await profile.save()
    return {"guardian_id": str(doc.id)}


async def decide_profile_correction(scope: AccessScope, payload: ProfileCorrectionDecision) -> dict:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    row = await StudentProfileCorrectionRequest.find_one(
        Eq(StudentProfileCorrectionRequest.tenant_id, tenant_id),
        Eq(StudentProfileCorrectionRequest.request_id, payload.request_id),
    )
    if row is None:
        raise AppError(code="NOT_FOUND", message="Correction request not found", status_code=404)
    if payload.approve:
        row.status = StudentDocumentRequestStatus.APPROVED
        profile = await StudentProfile.find_one(Eq(StudentProfile.tenant_id, tenant_id), Eq(StudentProfile.user_id, row.user_id))
        record = await StudentRecord.find_one(Eq(StudentRecord.tenant_id, tenant_id), Eq(StudentRecord.user_id, row.user_id))
        if profile and row.field_name in {"roll_number", "programme_name", "section_code"}:
            if row.field_name == "roll_number":
                profile.roll_number = row.proposed_value
                if record:
                    record.roll_number = row.proposed_value
            elif row.field_name == "section_code":
                profile.section_code = row.proposed_value
                if record:
                    record.section_code = row.proposed_value
            await profile.save()
            if record:
                await record.save()
    else:
        row.status = StudentDocumentRequestStatus.REJECTED
    row.updated_at = utcnow()
    await row.save()
    return {"status": row.status.value}


async def student_academic_history(scope: AccessScope, record_id: PydanticObjectId) -> StudentAcademicHistoryRead:
    authorize(scope, Permission.STUDENT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    record = await StudentRecord.get(record_id)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Student record not found", status_code=404)
    status_rows = await StudentStatusHistory.find(Eq(StudentStatusHistory.tenant_id, tenant_id), Eq(StudentStatusHistory.user_id, record.user_id)).sort("-created_at").to_list()
    promo_rows = await StudentPromotionRecord.find(Eq(StudentPromotionRecord.tenant_id, tenant_id), Eq(StudentPromotionRecord.user_id, record.user_id)).sort("-created_at").to_list()
    transfer_rows = await StudentTransfer.find(Eq(StudentTransfer.tenant_id, tenant_id), Eq(StudentTransfer.user_id, record.user_id)).sort("-created_at").to_list()
    enroll_rows = await StudentEnrollment.find(Eq(StudentEnrollment.tenant_id, tenant_id), Eq(StudentEnrollment.user_id, record.user_id)).sort("-created_at").to_list()
    return StudentAcademicHistoryRead(
        status_history=[{"from": r.from_status, "to": r.to_status, "at": r.created_at.isoformat()} for r in status_rows],
        promotions=[{"decision": r.decision, "at": r.created_at.isoformat()} for r in promo_rows],
        transfers=[{"status": r.status.value, "at": r.created_at.isoformat()} for r in transfer_rows],
        enrollments=[{"course_code": r.course_code, "section": r.section_code, "at": r.created_at.isoformat()} for r in enroll_rows],
    )


async def bulk_import_students(scope: AccessScope, payload: BulkStudentImport) -> list[StudentRecordRead]:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    created: list[StudentRecordRead] = []
    for row in payload.students:
        try:
            created.append(await create_student_record(scope, row))
        except AppError as exc:
            if exc.code != "CONFLICT":
                raise
    return created
