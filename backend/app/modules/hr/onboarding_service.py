"""HR employee onboarding services."""

from datetime import date, timedelta
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.roles import Role
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.college_admin.hr_admin_models import EmployeeOnboardingRecord
from app.modules.hr.document_models import HrEmployeeDocument
from app.modules.hr.employee_profile_schemas import EmployeeRegister
from app.modules.hr.employee_profile_service import register_employee
from app.modules.hr.employee_sync import log_hr_activity
from app.modules.hr.enums import (
    HrEmployeeDocumentStatus,
    HrEmploymentOfferStatus,
    HrOnboardingProcessStatus,
    HrOnboardingTaskStatus,
    HrStaffActivityType,
)
from app.modules.hr.hr_notification_dispatch import enqueue_hr_notification
from app.modules.hr.onboarding_models import (
    HrOnboardingChecklistTemplate,
    HrOnboardingProcess,
    HrOnboardingTask,
    HrOnboardingWaiver,
)
from app.modules.hr.onboarding_schemas import (
    OnboardingInitiate,
    OnboardingOverviewStats,
    OnboardingProcessRead,
    OnboardingProgressRead,
    OnboardingTaskRead,
    OnboardingTaskUpdate,
    OnboardingTemplateRead,
    OnboardingTemplateUpsert,
    OnboardingWaiverCreate,
)
from app.modules.hr.policy import authorize_hr_onboarding_complete, authorize_hr_onboarding_manage, authorize_hr_onboarding_read, require_hr_tenant_scope
from app.modules.hr.recruitment_models import HrCandidate, HrEmploymentOffer


async def _refresh_overdue_tasks(tenant_id: PydanticObjectId, process_id: PydanticObjectId) -> None:
    today = date.today()
    tasks = await HrOnboardingTask.find(
        Eq(HrOnboardingTask.tenant_id, tenant_id),
        Eq(HrOnboardingTask.process_id, process_id),
    ).to_list()
    for task in tasks:
        if task.status == HrOnboardingTaskStatus.COMPLETED:
            continue
        if task.due_date and task.due_date < today and task.status != HrOnboardingTaskStatus.OVERDUE:
            task.status = HrOnboardingTaskStatus.OVERDUE
            task.updated_at = utcnow()
            await task.save()


async def _sync_legacy_checklist(tenant_id: PydanticObjectId, employee_user_id: PydanticObjectId, process_id: PydanticObjectId) -> None:
    legacy = await EmployeeOnboardingRecord.find_one(
        Eq(EmployeeOnboardingRecord.tenant_id, tenant_id),
        Eq(EmployeeOnboardingRecord.user_id, employee_user_id),
    )
    if legacy is None:
        return
    tasks = await HrOnboardingTask.find(Eq(HrOnboardingTask.process_id, process_id)).to_list()
    legacy.checklist = [
        {
            "task_key": t.task_key,
            "title": t.title,
            "completed": t.status == HrOnboardingTaskStatus.COMPLETED,
            "due_date": t.due_date.isoformat() if t.due_date else None,
        }
        for t in tasks
    ]
    await legacy.save()


def _task_role_bucket(role: str) -> str:
    r = role.lower()
    if r in {"employee", "new_hire"}:
        return "employee"
    if r in {"hr", "hr_staff"}:
        return "hr"
    return "department"


async def upsert_onboarding_template(scope: AccessScope, payload: OnboardingTemplateUpsert) -> OnboardingTemplateRead:
    authorize_hr_onboarding_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    code = payload.template_code.strip()
    doc = await HrOnboardingChecklistTemplate.find_one(
        Eq(HrOnboardingChecklistTemplate.tenant_id, tenant_id),
        Eq(HrOnboardingChecklistTemplate.template_code, code),
    )
    if doc:
        doc.title = payload.title
        doc.employee_category = payload.employee_category
        doc.tasks = payload.tasks
        doc.version += 1
        doc.updated_at = utcnow()
        doc.actor_id = scope.user_id
        await doc.save()
    else:
        doc = HrOnboardingChecklistTemplate(
            tenant_id=tenant_id,
            template_code=code,
            title=payload.title,
            employee_category=payload.employee_category,
            tasks=payload.tasks,
            actor_id=scope.user_id,
        )
        await doc.insert()
    return OnboardingTemplateRead.from_document(doc)


async def initiate_onboarding(scope: AccessScope, payload: OnboardingInitiate) -> OnboardingProcessRead:
    authorize_hr_onboarding_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    offer_id = to_object_id(payload.offer_id, "offer_id")
    offer = await HrEmploymentOffer.get(offer_id)
    if offer is None or offer.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Offer not found", status_code=404)
    if offer.status != HrEmploymentOfferStatus.ACCEPTED:
        raise AppError(code="CONFLICT", message="Offer must be accepted before onboarding", status_code=409)
    if await HrOnboardingProcess.find_one(Eq(HrOnboardingProcess.tenant_id, tenant_id), Eq(HrOnboardingProcess.offer_id, offer.id)):
        raise AppError(code="CONFLICT", message="Onboarding already initiated for this offer", status_code=409)

    template_id = to_object_id(payload.template_id, "template_id")
    template = await HrOnboardingChecklistTemplate.get(template_id)
    if template is None or template.tenant_id != tenant_id or not template.is_active:
        raise AppError(code="NOT_FOUND", message="Onboarding template not found", status_code=404)

    candidate = await HrCandidate.get(offer.candidate_id)
    if candidate is None:
        raise AppError(code="NOT_FOUND", message="Candidate not found", status_code=404)

    employee_user_id: PydanticObjectId | None = candidate.converted_employee_user_id
    employee_record_id: PydanticObjectId | None = None

    if payload.create_employee and employee_user_id is None:
        if not payload.employee_code:
            raise AppError(code="VALIDATION_ERROR", message="employee_code is required to create employee", status_code=422)
        names = candidate.full_name.split()
        first = names[0]
        last = names[-1] if len(names) > 1 else names[0]
        role = Role(payload.institution_role) if payload.institution_role else Role.ACCOUNTS_STAFF
        reg = EmployeeRegister(
            employee_code=payload.employee_code,
            first_name=first,
            last_name=last,
            official_email=candidate.email,
            password="OnboardingTempPass123!",
            mobile_number=candidate.phone or "0000000000",
            joining_date=payload.joining_date or offer.expected_joining_date or date.today(),
            employee_category=template.employee_category,
            employment_type=offer.employment_type,
            employment_status=FacultyEmploymentStatus.PROBATION,
            department_id=payload.department_id,
            designation=payload.designation,
            institution_role=role,
        )
        profile = await register_employee(scope, reg)
        employee_user_id = to_object_id(profile.user_id, "user_id")
        employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, employee_user_id))
        if employee:
            employee_record_id = employee.id
        candidate.converted_employee_user_id = employee_user_id
        candidate.updated_at = utcnow()
        await candidate.save()
    elif employee_user_id:
        employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, employee_user_id))
        if employee:
            employee_record_id = employee.id

    dept_id = to_object_id(payload.department_id, "department_id")
    manager_id = to_object_id(payload.reporting_manager_id, "reporting_manager_id") if payload.reporting_manager_id else None
    process_code = f"ONB-{uuid4().hex[:10].upper()}"
    process = HrOnboardingProcess(
        tenant_id=tenant_id,
        process_code=process_code,
        offer_id=offer.id,
        application_id=offer.application_id,
        candidate_id=offer.candidate_id,
        employee_user_id=employee_user_id,
        employee_record_id=employee_record_id,
        template_id=template.id,
        department_id=dept_id,
        designation=payload.designation,
        reporting_manager_id=manager_id,
        joining_date=payload.joining_date or offer.expected_joining_date,
        mandatory_document_requirements=payload.mandatory_document_requirements,
        status=HrOnboardingProcessStatus.IN_PROGRESS,
        actor_id=scope.user_id,
    )
    await process.insert()

    today = date.today()
    for idx, task_def in enumerate(template.tasks):
        task_key = str(task_def.get("task_key") or f"task_{idx + 1}")
        due_days = int(task_def.get("due_days") or 7)
        task = HrOnboardingTask(
            tenant_id=tenant_id,
            process_id=process.id,
            task_key=task_key,
            title=str(task_def.get("title") or task_key),
            description=str(task_def.get("description") or ""),
            responsible_role=str(task_def.get("responsible_role") or "hr"),
            due_date=today + timedelta(days=due_days),
            priority=str(task_def.get("priority") or "normal"),
            status=HrOnboardingTaskStatus.ASSIGNED,
            mandatory=bool(task_def.get("mandatory", True)),
            assigned_date=today,
        )
        await task.insert()

    if employee_user_id and not await EmployeeOnboardingRecord.find_one(
        Eq(EmployeeOnboardingRecord.tenant_id, tenant_id),
        Eq(EmployeeOnboardingRecord.user_id, employee_user_id),
    ):
        await EmployeeOnboardingRecord(
            tenant_id=tenant_id,
            user_id=employee_user_id,
            employee_record_id=employee_record_id,
            checklist=[{"task_key": t.task_key, "title": t.title, "completed": False} for t in await HrOnboardingTask.find(Eq(HrOnboardingTask.process_id, process.id)).to_list()],
            actor_id=scope.user_id,
        ).insert()

    await enqueue_hr_notification(
        tenant_id,
        event_type="hr.onboarding.started",
        aggregate_type="hr_onboarding_process",
        aggregate_id=str(process.id),
        title="Onboarding started",
        body=f"Onboarding process {process_code} has been initiated.",
        recipient_user_id=employee_user_id,
        recipient_email=candidate.email if not employee_user_id else None,
        dedupe_key=f"hr:onboarding_start:{process.id}",
    )
    return OnboardingProcessRead.from_document(process)


async def update_onboarding_task(scope: AccessScope, task_id: str, payload: OnboardingTaskUpdate) -> OnboardingTaskRead:
    tenant_id = require_hr_tenant_scope(scope)
    tid = to_object_id(task_id, "task_id")
    task = await HrOnboardingTask.get(tid)
    if task is None or task.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Task not found", status_code=404)
    process = await HrOnboardingProcess.get(task.process_id)
    if process is None:
        raise AppError(code="NOT_FOUND", message="Onboarding process not found", status_code=404)

    is_employee_task = _task_role_bucket(task.responsible_role) == "employee"
    if is_employee_task and process.employee_user_id == scope.user_id:
        pass
    else:
        authorize_hr_onboarding_manage(scope)

    task.status = payload.status
    task.remarks = payload.remarks
    if payload.document_ref:
        task.document_ref = payload.document_ref
    if payload.status == HrOnboardingTaskStatus.COMPLETED:
        task.completion_date = date.today()
    task.updated_at = utcnow()
    await task.save()
    if process.employee_user_id:
        await _sync_legacy_checklist(tenant_id, process.employee_user_id, process.id)
    mandatory_open = await HrOnboardingTask.find(
        Eq(HrOnboardingTask.process_id, process.id),
        Eq(HrOnboardingTask.mandatory, True),
    ).to_list()
    if all(t.status == HrOnboardingTaskStatus.COMPLETED for t in mandatory_open):
        process.status = HrOnboardingProcessStatus.PENDING_COMPLETION
        process.updated_at = utcnow()
        await process.save()
    return OnboardingTaskRead.from_document(task)


async def submit_onboarding_for_completion(scope: AccessScope, process_id: str) -> OnboardingProcessRead:
    authorize_hr_onboarding_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    pid = to_object_id(process_id, "process_id")
    process = await HrOnboardingProcess.get(pid)
    if process is None or process.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Onboarding process not found", status_code=404)
    await _refresh_overdue_tasks(tenant_id, process.id)
    process.status = HrOnboardingProcessStatus.PENDING_COMPLETION
    process.updated_at = utcnow()
    await process.save()
    return OnboardingProcessRead.from_document(process)


async def record_onboarding_waiver(scope: AccessScope, process_id: str, payload: OnboardingWaiverCreate) -> dict:
    authorize_hr_onboarding_complete(scope)
    tenant_id = require_hr_tenant_scope(scope)
    pid = to_object_id(process_id, "process_id")
    process = await HrOnboardingProcess.get(pid)
    if process is None or process.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Onboarding process not found", status_code=404)
    waiver = HrOnboardingWaiver(
        tenant_id=tenant_id,
        process_id=process.id,
        requirement_key=payload.requirement_key.strip(),
        reason=payload.reason,
        approved_by=scope.user_id,
    )
    await waiver.insert()
    return {"waiver_id": str(waiver.id)}


async def compute_onboarding_progress(scope: AccessScope, process_id: str) -> OnboardingProgressRead:
    authorize_hr_onboarding_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    pid = to_object_id(process_id, "process_id")
    process = await HrOnboardingProcess.get(pid)
    if process is None or process.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Onboarding process not found", status_code=404)
    await _refresh_overdue_tasks(tenant_id, process.id)
    tasks = await HrOnboardingTask.find(Eq(HrOnboardingTask.tenant_id, tenant_id), Eq(HrOnboardingTask.process_id, process.id)).to_list()
    today = date.today()
    completed = pending = overdue = blocked = 0
    buckets: dict[str, list[HrOnboardingTask]] = {"employee": [], "hr": [], "department": []}
    for task in tasks:
        bucket = _task_role_bucket(task.responsible_role)
        buckets[bucket].append(task)
        if task.status == HrOnboardingTaskStatus.COMPLETED:
            completed += 1
        elif task.status == HrOnboardingTaskStatus.BLOCKED:
            blocked += 1
            pending += 1
        else:
            pending += 1
            if task.due_date and task.due_date < today and task.status != HrOnboardingTaskStatus.COMPLETED:
                overdue += 1

    def _percent(group: list[HrOnboardingTask]) -> float:
        if not group:
            return 100.0
        done = sum(1 for t in group if t.status == HrOnboardingTaskStatus.COMPLETED)
        return round(100.0 * done / len(group), 2)

    total = len(tasks) or 1
    overall = round(100.0 * completed / total, 2)
    return OnboardingProgressRead(
        process_id=str(process.id),
        overall_percent=overall,
        completed_tasks=completed,
        pending_tasks=pending,
        overdue_tasks=overdue,
        blocked_tasks=blocked,
        employee_side_percent=_percent(buckets["employee"]),
        hr_side_percent=_percent(buckets["hr"]),
        department_side_percent=_percent(buckets["department"]),
    )


async def _mandatory_documents_satisfied(tenant_id: PydanticObjectId, process: HrOnboardingProcess) -> tuple[bool, list[str]]:
    if not process.mandatory_document_requirements:
        return True, []
    if process.employee_user_id is None:
        return False, list(process.mandatory_document_requirements)
    missing: list[str] = []
    waived = {
        w.requirement_key
        for w in await HrOnboardingWaiver.find(Eq(HrOnboardingWaiver.tenant_id, tenant_id), Eq(HrOnboardingWaiver.process_id, process.id)).to_list()
    }
    for code in process.mandatory_document_requirements:
        if code in waived:
            continue
        doc = await HrEmployeeDocument.find_one(
            Eq(HrEmployeeDocument.tenant_id, tenant_id),
            Eq(HrEmployeeDocument.employee_user_id, process.employee_user_id),
            Eq(HrEmployeeDocument.category_code, code),
        )
        if doc is None or doc.status.value != "verified":
            missing.append(code)
    return len(missing) == 0, missing


async def complete_onboarding(scope: AccessScope, process_id: str) -> OnboardingProcessRead:
    authorize_hr_onboarding_complete(scope)
    tenant_id = require_hr_tenant_scope(scope)
    pid = to_object_id(process_id, "process_id")
    process = await HrOnboardingProcess.get(pid)
    if process is None or process.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Onboarding process not found", status_code=404)
    if process.status == HrOnboardingProcessStatus.COMPLETED:
        return OnboardingProcessRead.from_document(process)

    tasks = await HrOnboardingTask.find(Eq(HrOnboardingTask.process_id, process.id), Eq(HrOnboardingTask.mandatory, True)).to_list()
    waived_task_keys = {
        w.requirement_key
        for w in await HrOnboardingWaiver.find(Eq(HrOnboardingWaiver.tenant_id, tenant_id), Eq(HrOnboardingWaiver.process_id, process.id)).to_list()
    }
    incomplete = [t for t in tasks if t.status != HrOnboardingTaskStatus.COMPLETED and t.task_key not in waived_task_keys]
    if incomplete:
        raise AppError(
            code="CONFLICT",
            message=f"Mandatory onboarding tasks remain: {', '.join(t.task_key for t in incomplete[:5])}",
            status_code=409,
        )
    docs_ok, missing_docs = await _mandatory_documents_satisfied(tenant_id, process)
    if not docs_ok:
        raise AppError(code="CONFLICT", message=f"Mandatory documents not verified: {', '.join(missing_docs)}", status_code=409)
    if process.employee_user_id is None:
        raise AppError(code="CONFLICT", message="Employee record required before completion", status_code=409)

    process.status = HrOnboardingProcessStatus.COMPLETED
    process.completed_at = utcnow()
    process.updated_at = utcnow()
    await process.save()

    from app.modules.hr.employee_profile_models import HrEmployeeProfile

    profile = await HrEmployeeProfile.find_one(
        Eq(HrEmployeeProfile.tenant_id, tenant_id),
        Eq(HrEmployeeProfile.user_id, process.employee_user_id),
    )
    if profile and process.joining_date:
        profile.probation_start_date = process.joining_date
        profile.probation_end_date = process.joining_date + timedelta(days=180)
        profile.updated_at = utcnow()
        await profile.save()

    legacy = await EmployeeOnboardingRecord.find_one(
        Eq(EmployeeOnboardingRecord.tenant_id, tenant_id),
        Eq(EmployeeOnboardingRecord.user_id, process.employee_user_id),
    )
    if legacy and not legacy.completed:
        legacy.completed = True
        legacy.completed_at = utcnow()
        await legacy.save()

    await log_hr_activity(
        tenant_id,
        HrStaffActivityType.ONBOARDING_COMPLETED,
        f"Onboarding {process.process_code} completed",
        actor_id=scope.user_id,
        employee_user_id=process.employee_user_id,
        department_id=process.department_id,
        resource_type="hr_onboarding_process",
        resource_id=str(process.id),
    )
    await enqueue_hr_notification(
        tenant_id,
        event_type="hr.onboarding.completed",
        aggregate_type="hr_onboarding_process",
        aggregate_id=str(process.id),
        title="Welcome aboard",
        body="Your onboarding has been completed.",
        recipient_user_id=process.employee_user_id,
        dedupe_key=f"hr:onboarding_complete:{process.id}",
    )
    return OnboardingProcessRead.from_document(process)


async def list_onboarding_templates(scope: AccessScope) -> list[OnboardingTemplateRead]:
    authorize_hr_onboarding_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rows = await HrOnboardingChecklistTemplate.find(
        Eq(HrOnboardingChecklistTemplate.tenant_id, tenant_id),
        Eq(HrOnboardingChecklistTemplate.is_active, True),
    ).to_list()
    return [OnboardingTemplateRead.from_document(r) for r in rows]


async def list_onboarding_processes(scope: AccessScope, pagination: Pagination) -> Page[OnboardingProcessRead]:
    authorize_hr_onboarding_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    query = HrOnboardingProcess.find(Eq(HrOnboardingProcess.tenant_id, tenant_id))
    total = await query.count()
    rows = await query.sort(-HrOnboardingProcess.created_at).skip(pagination.skip).limit(pagination.limit).to_list()
    return Page(items=[OnboardingProcessRead.from_document(r) for r in rows], total=total, page=pagination.page, size=pagination.size)


async def get_onboarding_process(scope: AccessScope, process_id: str) -> OnboardingProcessRead:
    authorize_hr_onboarding_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    pid = to_object_id(process_id, "process_id")
    process = await HrOnboardingProcess.get(pid)
    if process is None or process.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Onboarding process not found", status_code=404)
    return OnboardingProcessRead.from_document(process)


async def list_process_tasks(scope: AccessScope, process_id: str) -> list[OnboardingTaskRead]:
    authorize_hr_onboarding_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    pid = to_object_id(process_id, "process_id")
    process = await HrOnboardingProcess.get(pid)
    if process is None or process.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Onboarding process not found", status_code=404)
    rows = await HrOnboardingTask.find(Eq(HrOnboardingTask.tenant_id, tenant_id), Eq(HrOnboardingTask.process_id, process.id)).to_list()
    return [OnboardingTaskRead.from_document(t) for t in rows]


async def list_my_onboarding_tasks(scope: AccessScope) -> list[OnboardingTaskRead]:
    """Employee-visible onboarding tasks for the current user."""
    tenant_id = require_hr_tenant_scope(scope)
    process = await HrOnboardingProcess.find_one(
        Eq(HrOnboardingProcess.tenant_id, tenant_id),
        Eq(HrOnboardingProcess.employee_user_id, scope.user_id),
    )
    if process is None:
        return []
    rows = await HrOnboardingTask.find(Eq(HrOnboardingTask.process_id, process.id)).to_list()
    visible = [t for t in rows if _task_role_bucket(t.responsible_role) == "employee" or t.assigned_to_user_id == scope.user_id]
    return [OnboardingTaskRead.from_document(t) for t in visible]


async def onboarding_overview(scope: AccessScope) -> OnboardingOverviewStats:
    authorize_hr_onboarding_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    stats = OnboardingOverviewStats()
    today = date.today()

    accepted_offers = await HrEmploymentOffer.find(
        Eq(HrEmploymentOffer.tenant_id, tenant_id),
        Eq(HrEmploymentOffer.status, HrEmploymentOfferStatus.ACCEPTED),
    ).to_list()
    processes = await HrOnboardingProcess.find(Eq(HrOnboardingProcess.tenant_id, tenant_id)).to_list()
    process_by_offer = {str(p.offer_id): p for p in processes}
    for offer in accepted_offers:
        if str(offer.id) not in process_by_offer:
            stats.awaiting_onboarding += 1

    for process in processes:
        if process.status == HrOnboardingProcessStatus.COMPLETED:
            stats.completed += 1
            continue
        if process.status == HrOnboardingProcessStatus.PENDING_COMPLETION:
            stats.pending_approvals += 1
        stats.currently_onboarding += 1
        tasks = await HrOnboardingTask.find(Eq(HrOnboardingTask.process_id, process.id)).to_list()
        for task in tasks:
            if task.status != HrOnboardingTaskStatus.COMPLETED:
                stats.pending_tasks += 1
                if task.due_date and task.due_date < today:
                    stats.overdue_tasks += 1
        docs_ok, _ = await _mandatory_documents_satisfied(tenant_id, process)
        if not docs_ok:
            stats.pending_documents += 1

    pending_docs = await HrEmployeeDocument.find(
        Eq(HrEmployeeDocument.tenant_id, tenant_id),
        Eq(HrEmployeeDocument.status, HrEmployeeDocumentStatus.PENDING_VERIFICATION),
    ).count()
    stats.pending_verifications = pending_docs
    return stats