"""Resignation, notice period, offboarding, and final separation."""

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
from app.modules.college_admin.hr_admin_models import EmployeeOffboardingRecord
from app.modules.hr.employee_sync import log_hr_activity
from app.modules.hr.enums import (
    HrOffboardingProcessStatus,
    HrOffboardingTaskStatus,
    HrResignationStatus,
    HrStaffActivityType,
)
from app.modules.hr.hr_notification_dispatch import enqueue_hr_notification
from app.modules.hr.offboarding_models import (
    HrExitInterview,
    HrNoticePeriodRecord,
    HrOffboardingChecklistTemplate,
    HrOffboardingProcess,
    HrOffboardingTask,
    HrResignationRequest,
)
from app.modules.hr.offboarding_schemas import (
    ExitInterviewUpsert,
    NoticePeriodUpdate,
    OffboardingInitiate,
    OffboardingProcessRead,
    OffboardingTaskUpdate,
    OffboardingTemplateUpsert,
    ResignationCreate,
    ResignationRead,
    ResignationReview,
)
from app.modules.hr.structure_models import HrEmployeeAssignmentHistory, HrEmployeeCurrentAssignment
from app.modules.hr.policy import authorize_hr_offboarding_manage, authorize_hr_offboarding_read, require_hr_tenant_scope
from app.modules.messaging.outbox_models import DomainOutboxEvent, OutboxEventStatus


async def create_resignation(scope: AccessScope, payload: ResignationCreate) -> ResignationRead:
    authorize_hr_offboarding_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(payload.employee_user_id, "employee_user_id")
    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, uid))
    if employee is None:
        raise AppError(code="NOT_FOUND", message="Employee not found", status_code=404)
    active_statuses = {
        HrResignationStatus.SUBMITTED,
        HrResignationStatus.UNDER_REVIEW,
        HrResignationStatus.AWAITING_MANAGER_APPROVAL,
        HrResignationStatus.AWAITING_HR_APPROVAL,
        HrResignationStatus.ACCEPTED,
        HrResignationStatus.NOTICE_PERIOD,
        HrResignationStatus.EXIT_IN_PROGRESS,
    }
    existing_rows = await HrResignationRequest.find(
        Eq(HrResignationRequest.tenant_id, tenant_id),
        Eq(HrResignationRequest.employee_user_id, uid),
    ).to_list()
    if any(r.status in active_statuses for r in existing_rows):
        raise AppError(code="CONFLICT", message="Active resignation already exists", status_code=409)
    code = f"RES-{uuid4().hex[:10].upper()}"
    row = HrResignationRequest(
        tenant_id=tenant_id,
        resignation_code=code,
        employee_user_id=uid,
        proposed_last_working_date=payload.proposed_last_working_date,
        reason=payload.reason,
        employee_remarks=payload.employee_remarks,
        document_refs=payload.document_refs,
        status=HrResignationStatus.AWAITING_MANAGER_APPROVAL,
        requested_by=scope.user_id,
        actor_id=scope.user_id,
    )
    await row.insert()
    await log_hr_activity(
        tenant_id,
        HrStaffActivityType.EMPLOYEE_EXIT,
        f"Resignation {code} submitted",
        actor_id=scope.user_id,
        employee_user_id=uid,
        resource_type="hr_resignation",
        resource_id=str(row.id),
        status_label=row.status.value,
    )
    return ResignationRead.from_document(row)


async def review_resignation(scope: AccessScope, resignation_id: str, payload: ResignationReview) -> ResignationRead:
    authorize_hr_offboarding_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rid = to_object_id(resignation_id, "resignation_id")
    row = await HrResignationRequest.get(rid)
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Resignation not found", status_code=404)

    if payload.decision == "withdraw":
        row.status = HrResignationStatus.WITHDRAWN
    elif payload.decision == "manager_approve" and row.status == HrResignationStatus.AWAITING_MANAGER_APPROVAL:
        row.status = HrResignationStatus.AWAITING_HR_APPROVAL
        row.manager_review = payload.note
    elif payload.decision == "hr_approve" and row.status == HrResignationStatus.AWAITING_HR_APPROVAL:
        row.status = HrResignationStatus.UNDER_REVIEW
        row.hr_review = payload.note
    elif payload.decision == "accept" and row.status in {
        HrResignationStatus.UNDER_REVIEW,
        HrResignationStatus.AWAITING_HR_APPROVAL,
        HrResignationStatus.SUBMITTED,
    }:
        row.status = HrResignationStatus.NOTICE_PERIOD
        row.management_decision = payload.note
        notice_start = date.today()
        notice_days = 30
        expected_lwd = row.proposed_last_working_date
        if expected_lwd < notice_start:
            expected_lwd = notice_start + timedelta(days=notice_days)
        await HrNoticePeriodRecord(
            tenant_id=tenant_id,
            resignation_id=row.id,
            employee_user_id=row.employee_user_id,
            notice_start_date=notice_start,
            required_notice_days=notice_days,
            expected_last_working_date=expected_lwd,
        ).insert()
        employee = await EmployeeRecord.find_one(
            Eq(EmployeeRecord.tenant_id, tenant_id),
            Eq(EmployeeRecord.user_id, row.employee_user_id),
        )
        if employee:
            employee.employment_status = FacultyEmploymentStatus.NOTICE_PERIOD
            employee.updated_at = utcnow()
            await employee.save()
        row.status = HrResignationStatus.NOTICE_PERIOD
    elif payload.decision == "reject":
        row.status = HrResignationStatus.REJECTED
        row.management_decision = payload.note
    else:
        raise AppError(code="CONFLICT", message="Invalid resignation decision for current status", status_code=409)

    row.updated_at = utcnow()
    await row.save()
    await enqueue_hr_notification(
        tenant_id,
        event_type="hr.resignation.decision",
        aggregate_type="hr_resignation",
        aggregate_id=str(row.id),
        title="Resignation update",
        body=f"Resignation {row.resignation_code} is {row.status.value}",
        recipient_user_id=row.employee_user_id,
        dedupe_key=f"hr:resignation:{row.id}:{row.status.value}",
    )
    return ResignationRead.from_document(row)


async def upsert_offboarding_template(scope: AccessScope, payload: OffboardingTemplateUpsert) -> dict:
    authorize_hr_offboarding_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    doc = await HrOffboardingChecklistTemplate.find_one(
        Eq(HrOffboardingChecklistTemplate.tenant_id, tenant_id),
        Eq(HrOffboardingChecklistTemplate.template_code, payload.template_code),
    )
    if doc:
        doc.title = payload.title
        doc.tasks = payload.tasks
        doc.version += 1
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = HrOffboardingChecklistTemplate(
            tenant_id=tenant_id,
            template_code=payload.template_code,
            title=payload.title,
            tasks=payload.tasks,
        )
        await doc.insert()
    return {"template_id": str(doc.id), "version": doc.version}


async def initiate_offboarding(scope: AccessScope, payload: OffboardingInitiate) -> OffboardingProcessRead:
    authorize_hr_offboarding_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    resignation_id = to_object_id(payload.resignation_id, "resignation_id")
    template_id = to_object_id(payload.template_id, "template_id")
    resignation = await HrResignationRequest.get(resignation_id)
    template = await HrOffboardingChecklistTemplate.get(template_id)
    if resignation is None or resignation.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Resignation not found", status_code=404)
    if template is None or template.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Offboarding template not found", status_code=404)
    if resignation.status not in {HrResignationStatus.NOTICE_PERIOD, HrResignationStatus.ACCEPTED}:
        raise AppError(code="CONFLICT", message="Resignation must be in notice period to start offboarding", status_code=409)

    notice = await HrNoticePeriodRecord.find_one(
        Eq(HrNoticePeriodRecord.tenant_id, tenant_id),
        Eq(HrNoticePeriodRecord.resignation_id, resignation.id),
    )
    lwd = notice.expected_last_working_date if notice else resignation.proposed_last_working_date
    code = f"OFF-{uuid4().hex[:10].upper()}"
    process = HrOffboardingProcess(
        tenant_id=tenant_id,
        process_code=code,
        resignation_id=resignation.id,
        employee_user_id=resignation.employee_user_id,
        template_id=template.id,
        last_working_date=lwd,
        separation_reason=resignation.reason,
        actor_id=scope.user_id,
    )
    await process.insert()

    for idx, task_def in enumerate(template.tasks):
        task_key = str(task_def.get("task_key") or f"task_{idx}")
        await HrOffboardingTask(
            tenant_id=tenant_id,
            process_id=process.id,
            task_key=task_key,
            title=str(task_def.get("title") or task_key),
            clearance_department=str(task_def.get("clearance_department") or "hr"),
        ).insert()

    resignation.status = HrResignationStatus.EXIT_IN_PROGRESS
    resignation.updated_at = utcnow()
    await resignation.save()
    return OffboardingProcessRead.from_document(process)


async def update_offboarding_task(scope: AccessScope, task_id: str, payload: OffboardingTaskUpdate) -> dict:
    authorize_hr_offboarding_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    tid = to_object_id(task_id, "task_id")
    task = await HrOffboardingTask.get(tid)
    if task is None or task.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Offboarding task not found", status_code=404)
    task.status = payload.status
    task.remarks = payload.remarks
    if payload.status == HrOffboardingTaskStatus.COMPLETED:
        task.completed_at = utcnow()
    task.updated_at = utcnow()
    await task.save()
    return {"task_id": str(task.id), "status": task.status.value}


async def upsert_exit_interview(scope: AccessScope, process_id: str, payload: ExitInterviewUpsert) -> dict:
    authorize_hr_offboarding_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    pid = to_object_id(process_id, "process_id")
    process = await HrOffboardingProcess.get(pid)
    if process is None or process.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Offboarding process not found", status_code=404)
    row = await HrExitInterview.find_one(
        Eq(HrExitInterview.tenant_id, tenant_id),
        Eq(HrExitInterview.process_id, process.id),
    )
    if row:
        row.scheduled_at = payload.scheduled_at
        row.interviewer_id = to_object_id(payload.interviewer_id, "interviewer_id") if payload.interviewer_id else None
        row.reason_for_leaving = payload.reason_for_leaving
        row.employee_feedback = payload.employee_feedback
        row.department_feedback = payload.department_feedback
        row.improvement_suggestions = payload.improvement_suggestions
        row.confidential_hr_remarks = payload.confidential_hr_remarks
        row.updated_at = utcnow()
        await row.save()
    else:
        row = HrExitInterview(
            tenant_id=tenant_id,
            process_id=process.id,
            employee_user_id=process.employee_user_id,
            scheduled_at=payload.scheduled_at,
            interviewer_id=to_object_id(payload.interviewer_id, "interviewer_id") if payload.interviewer_id else None,
            reason_for_leaving=payload.reason_for_leaving,
            employee_feedback=payload.employee_feedback,
            department_feedback=payload.department_feedback,
            improvement_suggestions=payload.improvement_suggestions,
            confidential_hr_remarks=payload.confidential_hr_remarks,
        )
        await row.insert()
    return {"exit_interview_id": str(row.id)}


async def update_notice_period(scope: AccessScope, resignation_id: str, payload: NoticePeriodUpdate) -> dict:
    authorize_hr_offboarding_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rid = to_object_id(resignation_id, "resignation_id")
    notice = await HrNoticePeriodRecord.find_one(
        Eq(HrNoticePeriodRecord.tenant_id, tenant_id),
        Eq(HrNoticePeriodRecord.resignation_id, rid),
    )
    if notice is None:
        raise AppError(code="NOT_FOUND", message="Notice period record not found", status_code=404)
    if payload.waiver_reason:
        notice.waiver_reason = payload.waiver_reason
        notice.waiver_approved_by = scope.user_id
    if payload.actual_last_working_date:
        notice.actual_last_working_date = payload.actual_last_working_date
        notice.expected_last_working_date = payload.actual_last_working_date
    if payload.early_release:
        notice.early_release = True
    if payload.extension_days:
        notice.extension_days = payload.extension_days
        notice.expected_last_working_date = notice.expected_last_working_date + timedelta(days=payload.extension_days)
        notice.required_notice_days += payload.extension_days
    notice.updated_at = utcnow()
    await notice.save()
    process = await HrOffboardingProcess.find_one(Eq(HrOffboardingProcess.tenant_id, tenant_id), Eq(HrOffboardingProcess.resignation_id, rid))
    if process and payload.actual_last_working_date:
        process.last_working_date = payload.actual_last_working_date
        process.updated_at = utcnow()
        await process.save()
    return {"resignation_id": resignation_id, "expected_last_working_date": notice.expected_last_working_date.isoformat()}


async def complete_offboarding(scope: AccessScope, process_id: str) -> OffboardingProcessRead:
    authorize_hr_offboarding_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    pid = to_object_id(process_id, "process_id")
    process = await HrOffboardingProcess.get(pid)
    if process is None or process.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Offboarding process not found", status_code=404)
    if process.status == HrOffboardingProcessStatus.COMPLETED:
        return OffboardingProcessRead.from_document(process)

    tasks = await HrOffboardingTask.find(Eq(HrOffboardingTask.process_id, process.id)).to_list()
    incomplete = [t for t in tasks if t.status != HrOffboardingTaskStatus.COMPLETED]
    if incomplete:
        raise AppError(
            code="CONFLICT",
            message=f"Clearance tasks pending: {', '.join(t.task_key for t in incomplete[:5])}",
            status_code=409,
        )

    resignation = await HrResignationRequest.get(process.resignation_id)
    notice = await HrNoticePeriodRecord.find_one(
        Eq(HrNoticePeriodRecord.tenant_id, tenant_id),
        Eq(HrNoticePeriodRecord.resignation_id, process.resignation_id),
    )
    lwd = process.last_working_date or (notice.expected_last_working_date if notice else date.today())
    if notice:
        notice.actual_last_working_date = lwd
        notice.updated_at = utcnow()
        await notice.save()

    await EmployeeOffboardingRecord(
        tenant_id=tenant_id,
        user_id=process.employee_user_id,
        reason=process.separation_reason or "Resignation",
        last_working_date=lwd,
        clearance_checklist=[{"task_key": t.task_key, "status": t.status.value} for t in tasks],
        actor_id=scope.user_id,
    ).insert()

    employee = await EmployeeRecord.find_one(
        Eq(EmployeeRecord.tenant_id, tenant_id),
        Eq(EmployeeRecord.user_id, process.employee_user_id),
    )
    if employee:
        employee.employment_status = FacultyEmploymentStatus.RESIGNED
        employee.updated_at = utcnow()
        await employee.save()

    assignment = await HrEmployeeCurrentAssignment.find_one(
        Eq(HrEmployeeCurrentAssignment.tenant_id, tenant_id),
        Eq(HrEmployeeCurrentAssignment.employee_user_id, process.employee_user_id),
    )
    if assignment:
        await HrEmployeeAssignmentHistory(
            tenant_id=tenant_id,
            employee_user_id=process.employee_user_id,
            change_type="separation_close",
            assignment_snapshot={
                "designation_code": assignment.designation_code,
                "institution_department_id": str(assignment.institution_department_id) if assignment.institution_department_id else None,
            },
            effective_from=assignment.effective_from,
            effective_to=lwd,
            reason=process.separation_reason or "Separation",
            approval={"offboarding_process_id": str(process.id)},
            actor_id=scope.user_id,
        ).insert()

    if resignation:
        resignation.status = HrResignationStatus.COMPLETED
        resignation.updated_at = utcnow()
        await resignation.save()

    process.status = HrOffboardingProcessStatus.COMPLETED
    process.completed_at = utcnow()
    process.updated_at = utcnow()
    if not process.payroll_handoff_sent:
        await DomainOutboxEvent(
            tenant_id=tenant_id,
            event_type="hr.payroll.final_settlement_requested",
            aggregate_type="hr_offboarding_process",
            aggregate_id=str(process.id),
            payload={
                "employee_user_id": str(process.employee_user_id),
                "last_working_date": lwd.isoformat(),
                "separation_reason": process.separation_reason,
            },
            idempotency_key=f"hr:payroll_handoff:{process.id}",
            status=OutboxEventStatus.PENDING,
        ).insert()
        process.payroll_handoff_sent = True
    await process.save()

    await DomainOutboxEvent(
        tenant_id=tenant_id,
        event_type="hr.identity.deactivate_requested",
        aggregate_type="hr_offboarding_process",
        aggregate_id=str(process.id),
        payload={"employee_user_id": str(process.employee_user_id)},
        idempotency_key=f"hr:identity_deactivate:{process.id}",
        status=OutboxEventStatus.PENDING,
    ).insert()

    await log_hr_activity(
        tenant_id,
        HrStaffActivityType.EMPLOYEE_EXIT,
        f"Offboarding {process.process_code} completed",
        actor_id=scope.user_id,
        employee_user_id=process.employee_user_id,
        resource_type="hr_offboarding_process",
        resource_id=str(process.id),
        status_label="completed",
    )
    return OffboardingProcessRead.from_document(process)


async def list_resignations(scope: AccessScope, pagination: Pagination) -> Page[ResignationRead]:
    authorize_hr_offboarding_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    q = HrResignationRequest.find(Eq(HrResignationRequest.tenant_id, tenant_id))
    total = await q.count()
    rows = await q.sort(-HrResignationRequest.created_at).skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[ResignationRead.from_document(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)