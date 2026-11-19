"""Employment change, probation, and contract services."""

from datetime import date, timedelta
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.hr.assignment_sync import ensure_current_assignment
from app.modules.hr.employee_profile_models import HrEmployeeProfile
from app.modules.hr.employee_sync import log_hr_activity
from app.modules.hr.employment_change_models import HrContractRecord, HrEmploymentChangeRequest, HrProbationReview
from app.modules.hr.employment_change_schemas import (
    ContractRecordRead,
    ContractUpsert,
    EmploymentChangeCreate,
    EmploymentChangeDetailRead,
    EmploymentChangeOverview,
    EmploymentChangeRead,
    EmploymentChangeReview,
    ProbationApproachingItem,
    ProbationReviewRead,
    ProbationReviewUpsert,
)
from app.modules.hr.enums import HrEmploymentChangeStatus, HrEmploymentChangeType, HrProbationReviewStatus, HrResignationStatus
from app.modules.hr.hr_notification_dispatch import enqueue_hr_notification
from app.modules.hr.offboarding_models import HrResignationRequest
from app.modules.hr.policy import authorize_hr_employment_change_manage, authorize_hr_employment_change_read, require_hr_tenant_scope
from app.modules.hr.structure_models import HrEmployeeAssignmentHistory


async def employment_change_overview(scope: AccessScope) -> EmploymentChangeOverview:
    authorize_hr_employment_change_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    stats = EmploymentChangeOverview()
    rows = await HrEmploymentChangeRequest.find(Eq(HrEmploymentChangeRequest.tenant_id, tenant_id)).to_list()
    today = date.today()
    pending_statuses = {
        HrEmploymentChangeStatus.SUBMITTED,
        HrEmploymentChangeStatus.PENDING_MANAGER,
        HrEmploymentChangeStatus.PENDING_HR,
        HrEmploymentChangeStatus.PENDING_MANAGEMENT,
        HrEmploymentChangeStatus.RETURNED,
    }
    for r in rows:
        if r.status in pending_statuses:
            stats.pending += 1
        if r.status in {HrEmploymentChangeStatus.APPROVED, HrEmploymentChangeStatus.APPLIED}:
            stats.approved += 1
        if r.status == HrEmploymentChangeStatus.SCHEDULED or (
            r.status == HrEmploymentChangeStatus.APPROVED and r.effective_date > today
        ):
            stats.awaiting_effective_date += 1
        active_change = r.status not in {HrEmploymentChangeStatus.REJECTED, HrEmploymentChangeStatus.CANCELLED, HrEmploymentChangeStatus.APPLIED}
        if active_change:
            if r.change_type == HrEmploymentChangeType.DEPARTMENT_TRANSFER:
                stats.department_transfers += 1
            elif r.change_type in {HrEmploymentChangeType.DESIGNATION_CHANGE, HrEmploymentChangeType.PROMOTION, HrEmploymentChangeType.DEMOTION}:
                stats.designation_changes += 1
            elif r.change_type == HrEmploymentChangeType.REPORTING_MANAGER_CHANGE:
                stats.reporting_manager_changes += 1
            elif r.change_type == HrEmploymentChangeType.EMPLOYMENT_TYPE_CHANGE:
                stats.employment_type_changes += 1
            elif r.change_type in {HrEmploymentChangeType.CONTRACT_EXTENSION, HrEmploymentChangeType.CONTRACT_RENEWAL}:
                stats.contract_extensions += 1
            elif r.change_type == HrEmploymentChangeType.SALARY_REVISION or r.proposed_details.get("salary_revision") is not None:
                stats.salary_related_requests += 1
    stats.probation_approaching_end = len(await list_probation_approaching(scope, within_days=30))
    soon = today + timedelta(days=30)
    contracts = await HrContractRecord.find(Eq(HrContractRecord.tenant_id, tenant_id)).to_list()
    stats.contracts_expiring_soon = sum(1 for c in contracts if c.end_date and today <= c.end_date <= soon and c.status == "active")
    stats.probation_items = await HrProbationReview.find(
        Eq(HrProbationReview.tenant_id, tenant_id),
        Eq(HrProbationReview.status, HrProbationReviewStatus.PENDING_HR),
    ).count()
    resignations = await HrResignationRequest.find(Eq(HrResignationRequest.tenant_id, tenant_id)).to_list()
    for res in resignations:
        if res.status in {HrResignationStatus.SUBMITTED, HrResignationStatus.UNDER_REVIEW, HrResignationStatus.AWAITING_MANAGER_APPROVAL, HrResignationStatus.AWAITING_HR_APPROVAL}:
            stats.resignations_active += 1
        elif res.status == HrResignationStatus.NOTICE_PERIOD:
            stats.notice_period += 1
        elif res.status == HrResignationStatus.EXIT_IN_PROGRESS:
            stats.exit_in_progress += 1
        elif res.status == HrResignationStatus.COMPLETED:
            stats.completed_exits += 1
    return stats


async def _snapshot_employee(tenant_id: PydanticObjectId, employee_user_id: PydanticObjectId) -> dict:
    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, employee_user_id))
    profile = await HrEmployeeProfile.find_one(Eq(HrEmployeeProfile.tenant_id, tenant_id), Eq(HrEmployeeProfile.user_id, employee_user_id))
    if employee is None:
        raise AppError(code="NOT_FOUND", message="Employee not found", status_code=404)
    return {
        "department_id": str(employee.department_id) if employee.department_id else None,
        "designation": employee.designation,
        "employment_type": employee.employment_type,
        "campus_id": str(employee.campus_id) if employee.campus_id else None,
        "employment_status": employee.employment_status.value,
        "reporting_manager_user_id": str(profile.reporting_manager_user_id) if profile and profile.reporting_manager_user_id else None,
        "employee_category": profile.employee_category if profile else None,
    }


async def create_employment_change(scope: AccessScope, payload: EmploymentChangeCreate) -> EmploymentChangeRead:
    authorize_hr_employment_change_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(payload.employee_user_id, "employee_user_id")
    current = await _snapshot_employee(tenant_id, uid)
    code = f"CHG-{uuid4().hex[:10].upper()}"
    status = HrEmploymentChangeStatus.PENDING_MANAGER if payload.requires_manager_approval else HrEmploymentChangeStatus.PENDING_HR
    row = HrEmploymentChangeRequest(
        tenant_id=tenant_id,
        change_code=code,
        employee_user_id=uid,
        change_type=payload.change_type,
        current_details=current,
        proposed_details=payload.proposed_details,
        effective_date=payload.effective_date,
        reason=payload.reason,
        requested_by=scope.user_id,
        document_refs=payload.document_refs,
        status=status,
        actor_id=scope.user_id,
    )
    await row.insert()
    return EmploymentChangeRead.from_document(row)


async def review_employment_change(scope: AccessScope, change_id: str, payload: EmploymentChangeReview) -> EmploymentChangeRead:
    authorize_hr_employment_change_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    cid = to_object_id(change_id, "change_id")
    row = await HrEmploymentChangeRequest.get(cid)
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Change request not found", status_code=404)
    if payload.decision == "manager_approve" and row.status == HrEmploymentChangeStatus.PENDING_MANAGER:
        row.status = HrEmploymentChangeStatus.PENDING_HR
    elif payload.decision == "hr_validate" and row.status == HrEmploymentChangeStatus.PENDING_HR:
        row.status = HrEmploymentChangeStatus.PENDING_MANAGEMENT
    elif payload.decision == "approve" and row.status == HrEmploymentChangeStatus.PENDING_MANAGEMENT:
        row.status = HrEmploymentChangeStatus.APPROVED
        await _apply_change_if_due(row)
    elif payload.decision == "reject":
        row.status = HrEmploymentChangeStatus.REJECTED
    elif payload.decision == "return":
        row.status = HrEmploymentChangeStatus.RETURNED
    else:
        raise AppError(code="CONFLICT", message="Invalid state for decision", status_code=409)
    row.review_note = payload.note
    row.updated_at = utcnow()
    await row.save()
    employee = await HrEmployeeProfile.find_one(Eq(HrEmployeeProfile.tenant_id, tenant_id), Eq(HrEmployeeProfile.user_id, row.employee_user_id))
    if employee:
        await enqueue_hr_notification(
            tenant_id,
            event_type="hr.employment_change.decision",
            aggregate_type="hr_employment_change",
            aggregate_id=str(row.id),
            title="Employment change update",
            body=f"Change {row.change_code} is now {row.status.value}",
            recipient_user_id=row.employee_user_id,
            dedupe_key=f"hr:emp_chg:{row.id}:{row.status.value}",
        )
    return EmploymentChangeRead.from_document(row)


async def _apply_change_if_due(row: HrEmploymentChangeRequest) -> None:
    if row.status != HrEmploymentChangeStatus.APPROVED:
        return
    if row.effective_date > date.today():
        row.status = HrEmploymentChangeStatus.SCHEDULED
        await row.save()
        return
    tenant_id = row.tenant_id
    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, row.employee_user_id))
    profile = await HrEmployeeProfile.find_one(Eq(HrEmployeeProfile.tenant_id, tenant_id), Eq(HrEmployeeProfile.user_id, row.employee_user_id))
    if employee is None:
        return
    proposed = row.proposed_details
    if proposed.get("department_id"):
        employee.department_id = to_object_id(proposed["department_id"], "department_id")
    if proposed.get("designation"):
        employee.designation = str(proposed["designation"])
    if proposed.get("employment_type"):
        employee.employment_type = str(proposed["employment_type"])
    if proposed.get("campus_id"):
        employee.campus_id = to_object_id(proposed["campus_id"], "campus_id")
    if proposed.get("employment_status"):
        employee.employment_status = FacultyEmploymentStatus(str(proposed["employment_status"]))
    employee.updated_at = utcnow()
    await employee.save()
    if profile and proposed.get("reporting_manager_user_id"):
        profile.reporting_manager_user_id = to_object_id(proposed["reporting_manager_user_id"], "reporting_manager_user_id")
        profile.updated_at = utcnow()
        await profile.save()
    await ensure_current_assignment(tenant_id, employee, profile, actor_id=row.actor_id)
    await HrEmployeeAssignmentHistory(
        tenant_id=tenant_id,
        employee_user_id=row.employee_user_id,
        change_type=row.change_type.value,
        assignment_snapshot=proposed,
        effective_from=row.effective_date,
        reason=row.reason,
        approval={"approved_via": "employment_change", "change_id": str(row.id)},
        actor_id=row.actor_id,
    ).insert()
    row.status = HrEmploymentChangeStatus.APPLIED
    row.applied_at = utcnow()
    await row.save()


async def process_due_employment_changes(scope: AccessScope) -> dict:
    authorize_hr_employment_change_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    due = await HrEmploymentChangeRequest.find(
        Eq(HrEmploymentChangeRequest.tenant_id, tenant_id),
        Eq(HrEmploymentChangeRequest.status, HrEmploymentChangeStatus.SCHEDULED),
    ).to_list()
    applied = 0
    for row in due:
        if row.effective_date <= date.today():
            row.status = HrEmploymentChangeStatus.APPROVED
            await _apply_change_if_due(row)
            applied += 1
    return {"processed": applied}


async def get_employment_change(scope: AccessScope, change_id: str) -> EmploymentChangeDetailRead:
    authorize_hr_employment_change_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    cid = to_object_id(change_id, "change_id")
    row = await HrEmploymentChangeRequest.get(cid)
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Change request not found", status_code=404)
    return EmploymentChangeDetailRead.from_document(row)


async def list_probation_approaching(scope: AccessScope, within_days: int = 30) -> list[ProbationApproachingItem]:
    authorize_hr_employment_change_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    today = date.today()
    horizon = today + timedelta(days=within_days)
    profiles = await HrEmployeeProfile.find(Eq(HrEmployeeProfile.tenant_id, tenant_id)).to_list()
    items: list[ProbationApproachingItem] = []
    for profile in profiles:
        if profile.probation_end_date and today <= profile.probation_end_date <= horizon:
            items.append(
                ProbationApproachingItem(
                    employee_user_id=str(profile.user_id),
                    probation_end_date=profile.probation_end_date,
                    days_remaining=(profile.probation_end_date - today).days,
                )
            )
    return items


async def list_contracts(scope: AccessScope, pagination: Pagination, employee_user_id: str | None = None) -> Page[ContractRecordRead]:
    authorize_hr_employment_change_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    filters = [Eq(HrContractRecord.tenant_id, tenant_id)]
    if employee_user_id:
        filters.append(Eq(HrContractRecord.employee_user_id, to_object_id(employee_user_id, "employee_user_id")))
    q = HrContractRecord.find(*filters)
    total = await q.count()
    rows = await q.sort(-HrContractRecord.end_date).skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[ContractRecordRead.from_document(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def dispatch_contract_expiry_reminders(scope: AccessScope, within_days: int = 30) -> dict:
    authorize_hr_employment_change_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    today = date.today()
    horizon = today + timedelta(days=within_days)
    sent = 0
    contracts = await HrContractRecord.find(Eq(HrContractRecord.tenant_id, tenant_id), Eq(HrContractRecord.status, "active")).to_list()
    for contract in contracts:
        if contract.end_date is None or not (today <= contract.end_date <= horizon):
            continue
        created = await enqueue_hr_notification(
            tenant_id,
            event_type="hr.contract.expiry_reminder",
            aggregate_type="hr_contract",
            aggregate_id=str(contract.id),
            title="Contract expiring soon",
            body=f"Contract {contract.contract_code} ends on {contract.end_date.isoformat()}",
            recipient_user_id=contract.employee_user_id,
            dedupe_key=f"hr:contract_expiry:{contract.id}:{contract.end_date.isoformat()}",
        )
        if created:
            sent += 1
    return {"reminders_sent": sent}


async def list_employment_changes(scope: AccessScope, pagination: Pagination, employee_user_id: str | None = None) -> Page[EmploymentChangeRead]:
    authorize_hr_employment_change_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    filters = [Eq(HrEmploymentChangeRequest.tenant_id, tenant_id)]
    if employee_user_id:
        filters.append(Eq(HrEmploymentChangeRequest.employee_user_id, to_object_id(employee_user_id, "employee_user_id")))
    q = HrEmploymentChangeRequest.find(*filters)
    total = await q.count()
    rows = await q.sort(-HrEmploymentChangeRequest.created_at).skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[EmploymentChangeRead.from_document(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def upsert_probation_review(scope: AccessScope, payload: ProbationReviewUpsert) -> ProbationReviewRead:
    authorize_hr_employment_change_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(payload.employee_user_id, "employee_user_id")
    profile = await HrEmployeeProfile.find_one(Eq(HrEmployeeProfile.tenant_id, tenant_id), Eq(HrEmployeeProfile.user_id, uid))
    if profile is None or not profile.probation_end_date:
        raise AppError(code="VALIDATION_ERROR", message="Employee has no probation dates", status_code=422)
    row = HrProbationReview(
        tenant_id=tenant_id,
        employee_user_id=uid,
        probation_start_date=profile.probation_start_date or profile.probation_end_date,
        probation_end_date=profile.probation_end_date,
        manager_feedback=payload.manager_feedback,
        hr_review=payload.hr_review,
        recommendation=payload.recommendation,
        status=HrProbationReviewStatus.PENDING_HR,
        actor_id=scope.user_id,
    )
    if payload.recommendation == "confirm":
        row.status = HrProbationReviewStatus.CONFIRMATION_RECOMMENDED
    elif payload.recommendation == "extend":
        row.status = HrProbationReviewStatus.EXTENSION_RECOMMENDED
    await row.insert()
    return ProbationReviewRead.from_document(row)


async def approve_probation_review(scope: AccessScope, review_id: str, decision: str) -> ProbationReviewRead:
    authorize_hr_employment_change_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rid = to_object_id(review_id, "review_id")
    row = await HrProbationReview.get(rid)
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Probation review not found", status_code=404)
    profile = await HrEmployeeProfile.find_one(Eq(HrEmployeeProfile.tenant_id, tenant_id), Eq(HrEmployeeProfile.user_id, row.employee_user_id))
    if decision == "confirm" and profile:
        profile.confirmation_date = date.today()
        employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, row.employee_user_id))
        if employee:
            employee.employment_status = FacultyEmploymentStatus.ACTIVE
            await employee.save()
        await profile.save()
        row.status = HrProbationReviewStatus.CONFIRMED
    elif decision == "extend" and profile:
        profile.probation_end_date = (profile.probation_end_date or date.today()) + timedelta(days=90)
        await profile.save()
        row.status = HrProbationReviewStatus.EXTENDED
    else:
        row.status = HrProbationReviewStatus.REJECTED
    row.approved_by = scope.user_id
    row.approved_at = utcnow()
    await row.save()
    return ProbationReviewRead.from_document(row)


async def upsert_contract(scope: AccessScope, payload: ContractUpsert) -> dict:
    authorize_hr_employment_change_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(payload.employee_user_id, "employee_user_id")
    doc = await HrContractRecord.find_one(Eq(HrContractRecord.tenant_id, tenant_id), Eq(HrContractRecord.contract_code, payload.contract_code))
    if doc:
        doc.end_date = payload.end_date
        doc.renewal_eligible = payload.renewal_eligible
        doc.document_ref = payload.document_ref
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = HrContractRecord(
            tenant_id=tenant_id,
            employee_user_id=uid,
            contract_code=payload.contract_code,
            contract_type=payload.contract_type,
            start_date=payload.start_date,
            end_date=payload.end_date,
            renewal_eligible=payload.renewal_eligible,
            document_ref=payload.document_ref,
            actor_id=scope.user_id,
        )
        await doc.insert()
    return {"contract_id": str(doc.id)}