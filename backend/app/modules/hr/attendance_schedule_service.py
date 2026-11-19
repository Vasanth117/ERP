"""Work schedules, shifts, roster, attendance processing and monthly close."""

from calendar import monthrange
from datetime import date, datetime, timedelta
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, GTE, LTE

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.hr.attendance_calculation import compute_attendance_from_events
from app.modules.hr.attendance_schedule_models import (
    HrEmployeeAttendanceEvent,
    HrEmployeeAttendanceMonthlySummary,
    HrEmployeeAttendanceRecord,
    HrEmployeeRosterAssignment,
    HrShift,
    HrShiftSwapRequest,
    HrWorkSchedule,
)
from app.modules.hr.attendance_schedule_schemas import (
    AttendanceCorrectionCreate,
    AttendanceCorrectionReview,
    AttendanceEventIngest,
    AttendanceManualDay,
    AttendanceOverview,
    AttendanceRecordRead,
    MonthlyAttendanceAction,
    MonthlySummaryRead,
    RosterAssign,
    RosterRead,
    ShiftRead,
    ShiftSwapCreate,
    ShiftUpsert,
    WorkScheduleRead,
    WorkScheduleUpsert,
)
from app.modules.hr.employee_sync import log_hr_activity
from app.modules.hr.enums import (
    EmployeeAttendanceCorrectionStatus,
    EmployeeAttendanceDayStatus,
    HrAttendanceEventSource,
    HrAttendanceEventType,
    HrMonthlyAttendanceStatus,
    HrRosterAssignmentStatus,
    HrStaffActivityType,
)
from app.modules.hr.hr_notification_dispatch import enqueue_hr_notification
from app.modules.hr.operational_models import EmployeeAttendanceCorrection, EmployeeDayAttendance
from app.modules.hr.policy import authorize_hr_attendance_manage, authorize_hr_attendance_read, require_hr_tenant_scope


def _legacy_status_map(status: EmployeeAttendanceDayStatus) -> EmployeeAttendanceDayStatus:
    if status in {EmployeeAttendanceDayStatus.LATE, EmployeeAttendanceDayStatus.HALF_DAY, EmployeeAttendanceDayStatus.WORK_FROM_HOME}:
        return EmployeeAttendanceDayStatus.PRESENT
    if status in {EmployeeAttendanceDayStatus.MISSING_PUNCH, EmployeeAttendanceDayStatus.INCOMPLETE}:
        return EmployeeAttendanceDayStatus.MISSING
    if status == EmployeeAttendanceDayStatus.HOLIDAY:
        return EmployeeAttendanceDayStatus.ABSENT
    if status == EmployeeAttendanceDayStatus.WEEKLY_OFF:
        return EmployeeAttendanceDayStatus.ABSENT
    return status


async def _sync_legacy_day(row: HrEmployeeAttendanceRecord) -> None:
    legacy_status = _legacy_status_map(row.status)
    existing = await EmployeeDayAttendance.find_one(
        Eq(EmployeeDayAttendance.tenant_id, row.tenant_id),
        Eq(EmployeeDayAttendance.employee_user_id, row.employee_user_id),
        Eq(EmployeeDayAttendance.attendance_date, row.attendance_date),
    )
    if existing is None:
        await EmployeeDayAttendance(
            tenant_id=row.tenant_id,
            employee_user_id=row.employee_user_id,
            attendance_date=row.attendance_date,
            status=legacy_status,
            check_in_at=row.first_check_in,
            check_out_at=row.last_check_out,
        ).insert()
    else:
        existing.status = legacy_status
        existing.check_in_at = row.first_check_in
        existing.check_out_at = row.last_check_out
        existing.updated_at = utcnow()
        await existing.save()


async def upsert_work_schedule(scope: AccessScope, payload: WorkScheduleUpsert) -> WorkScheduleRead:
    authorize_hr_attendance_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    doc_rows = await HrWorkSchedule.find(
        Eq(HrWorkSchedule.tenant_id, tenant_id),
        Eq(HrWorkSchedule.schedule_code, payload.schedule_code),
    ).sort(-HrWorkSchedule.version).limit(1).to_list()
    base = doc_rows[0] if doc_rows else None
    version = (base.version + 1) if base else 1
    if base:
        base.is_active = False
        base.effective_to = payload.effective_from - timedelta(days=1)
        base.updated_at = utcnow()
        await base.save()
    row = HrWorkSchedule(
        tenant_id=tenant_id,
        schedule_code=payload.schedule_code,
        title=payload.title,
        employee_categories=payload.employee_categories,
        department_id=to_object_id(payload.department_id, "department_id") if payload.department_id else None,
        campus_id=to_object_id(payload.campus_id, "campus_id") if payload.campus_id else None,
        working_days=payload.working_days,
        weekly_offs=payload.weekly_offs,
        start_time=payload.start_time.strftime("%H:%M"),
        end_time=payload.end_time.strftime("%H:%M"),
        break_minutes=payload.break_minutes,
        expected_hours=payload.expected_hours,
        grace_minutes=payload.grace_minutes,
        wfh_enabled=payload.wfh_enabled,
        effective_from=payload.effective_from,
        version=version,
        actor_id=scope.user_id,
    )
    await row.insert()
    return WorkScheduleRead.from_document(row)


async def list_work_schedules(scope: AccessScope) -> list[WorkScheduleRead]:
    authorize_hr_attendance_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rows = await HrWorkSchedule.find(Eq(HrWorkSchedule.tenant_id, tenant_id), Eq(HrWorkSchedule.is_active, True)).to_list()
    return [WorkScheduleRead.from_document(r) for r in rows]


async def upsert_shift(scope: AccessScope, payload: ShiftUpsert) -> ShiftRead:
    authorize_hr_attendance_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    doc = await HrShift.find_one(Eq(HrShift.tenant_id, tenant_id), Eq(HrShift.shift_code, payload.shift_code))
    if doc:
        doc.title = payload.title
        doc.kind = payload.kind
        doc.start_time = payload.start_time.strftime("%H:%M")
        doc.end_time = payload.end_time.strftime("%H:%M")
        doc.crosses_midnight = payload.crosses_midnight
        doc.break_minutes = payload.break_minutes
        doc.expected_hours = payload.expected_hours
        doc.grace_minutes = payload.grace_minutes
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = HrShift(
            tenant_id=tenant_id,
            shift_code=payload.shift_code,
            title=payload.title,
            kind=payload.kind,
            start_time=payload.start_time.strftime("%H:%M"),
            end_time=payload.end_time.strftime("%H:%M"),
            crosses_midnight=payload.crosses_midnight,
            break_minutes=payload.break_minutes,
            expected_hours=payload.expected_hours,
            grace_minutes=payload.grace_minutes,
            actor_id=scope.user_id,
        )
        await doc.insert()
    return ShiftRead.from_document(doc)


async def list_shifts(scope: AccessScope) -> list[ShiftRead]:
    authorize_hr_attendance_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rows = await HrShift.find(Eq(HrShift.tenant_id, tenant_id), Eq(HrShift.is_active, True)).to_list()
    return [ShiftRead.from_document(r) for r in rows]


async def _detect_roster_conflict(tenant_id: PydanticObjectId, employee_user_id: PydanticObjectId, roster_date: date) -> None:
    existing = await HrEmployeeRosterAssignment.find_one(
        Eq(HrEmployeeRosterAssignment.tenant_id, tenant_id),
        Eq(HrEmployeeRosterAssignment.employee_user_id, employee_user_id),
        Eq(HrEmployeeRosterAssignment.roster_date, roster_date),
    )
    if existing and existing.status != HrRosterAssignmentStatus.CANCELLED:
        raise AppError(code="CONFLICT", message="Roster assignment already exists for date", status_code=409)


async def assign_roster(scope: AccessScope, payload: RosterAssign) -> RosterRead:
    authorize_hr_attendance_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(payload.employee_user_id, "employee_user_id")
    await _detect_roster_conflict(tenant_id, uid, payload.roster_date)
    row = HrEmployeeRosterAssignment(
        tenant_id=tenant_id,
        employee_user_id=uid,
        shift_id=to_object_id(payload.shift_id, "shift_id"),
        schedule_id=to_object_id(payload.schedule_id, "schedule_id") if payload.schedule_id else None,
        department_id=to_object_id(payload.department_id, "department_id") if payload.department_id else None,
        roster_date=payload.roster_date,
        status=HrRosterAssignmentStatus.SCHEDULED,
        actor_id=scope.user_id,
    )
    await row.insert()
    return RosterRead.from_document(row)


async def list_roster(scope: AccessScope, start_date: date, end_date: date, employee_user_id: str | None = None) -> list[RosterRead]:
    authorize_hr_attendance_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    filters = [
        Eq(HrEmployeeRosterAssignment.tenant_id, tenant_id),
        GTE(HrEmployeeRosterAssignment.roster_date, start_date),
        LTE(HrEmployeeRosterAssignment.roster_date, end_date),
    ]
    if employee_user_id:
        filters.append(Eq(HrEmployeeRosterAssignment.employee_user_id, to_object_id(employee_user_id, "employee_user_id")))
    rows = await HrEmployeeRosterAssignment.find(*filters).sort(HrEmployeeRosterAssignment.roster_date).to_list()
    return [RosterRead.from_document(r) for r in rows]


async def request_shift_swap(scope: AccessScope, payload: ShiftSwapCreate) -> dict:
    authorize_hr_attendance_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    assignment = await HrEmployeeRosterAssignment.get(to_object_id(payload.from_assignment_id, "from_assignment_id"))
    if assignment is None or assignment.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Roster assignment not found", status_code=404)
    code = f"SWP-{uuid4().hex[:10].upper()}"
    req = HrShiftSwapRequest(
        tenant_id=tenant_id,
        request_code=code,
        from_assignment_id=assignment.id,
        to_employee_user_id=to_object_id(payload.to_employee_user_id, "to_employee_user_id"),
        reason=payload.reason,
        status="pending",
    )
    await req.insert()
    assignment.status = HrRosterAssignmentStatus.SWAP_PENDING
    assignment.swap_request_id = code
    assignment.updated_at = utcnow()
    await assignment.save()
    return {"swap_request_id": str(req.id), "request_code": code}


async def approve_shift_swap(scope: AccessScope, swap_request_id: str) -> dict:
    authorize_hr_attendance_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    req = await HrShiftSwapRequest.get(to_object_id(swap_request_id, "swap_request_id"))
    if req is None or req.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Swap request not found", status_code=404)
    assignment = await HrEmployeeRosterAssignment.get(req.from_assignment_id)
    if assignment is None:
        raise AppError(code="NOT_FOUND", message="Original assignment missing", status_code=404)
    await _detect_roster_conflict(tenant_id, req.to_employee_user_id, assignment.roster_date)
    replacement = HrEmployeeRosterAssignment(
        tenant_id=tenant_id,
        employee_user_id=req.to_employee_user_id,
        shift_id=assignment.shift_id,
        schedule_id=assignment.schedule_id,
        department_id=assignment.department_id,
        roster_date=assignment.roster_date,
        status=HrRosterAssignmentStatus.ACTIVE,
        actor_id=scope.user_id,
    )
    await replacement.insert()
    assignment.status = HrRosterAssignmentStatus.REPLACED
    assignment.replaced_by_assignment_id = replacement.id
    assignment.updated_at = utcnow()
    await assignment.save()
    req.status = "approved"
    req.approved_by = scope.user_id
    req.updated_at = utcnow()
    await req.save()
    return {"replacement_assignment_id": str(replacement.id)}


async def reprocess_attendance_day(tenant_id: PydanticObjectId, employee_user_id: PydanticObjectId, attendance_date: date) -> HrEmployeeAttendanceRecord:
    start = datetime.combine(attendance_date, datetime.min.time())
    end = datetime.combine(attendance_date + timedelta(days=1), datetime.min.time())
    events = await HrEmployeeAttendanceEvent.find(
        Eq(HrEmployeeAttendanceEvent.tenant_id, tenant_id),
        Eq(HrEmployeeAttendanceEvent.employee_user_id, employee_user_id),
        GTE(HrEmployeeAttendanceEvent.event_at, start),
        LTE(HrEmployeeAttendanceEvent.event_at, end),
    ).to_list()
    metrics = await compute_attendance_from_events(tenant_id, employee_user_id, attendance_date, events)
    record = await HrEmployeeAttendanceRecord.find_one(
        Eq(HrEmployeeAttendanceRecord.tenant_id, tenant_id),
        Eq(HrEmployeeAttendanceRecord.employee_user_id, employee_user_id),
        Eq(HrEmployeeAttendanceRecord.attendance_date, attendance_date),
    )
    if record and record.locked:
        raise AppError(code="CONFLICT", message="Attendance record is locked", status_code=409)
    if record is None:
        record = HrEmployeeAttendanceRecord(
            tenant_id=tenant_id,
            employee_user_id=employee_user_id,
            attendance_date=attendance_date,
            status=metrics["status"],
        )
    else:
        record.previous_snapshot = {
            "status": record.status.value,
            "working_minutes": record.working_minutes,
            "first_check_in": record.first_check_in.isoformat() if record.first_check_in else None,
            "last_check_out": record.last_check_out.isoformat() if record.last_check_out else None,
        }
    record.status = metrics["status"]
    record.first_check_in = metrics["first_check_in"]
    record.last_check_out = metrics["last_check_out"]
    record.working_minutes = metrics["working_minutes"]
    record.break_minutes = metrics["break_minutes"]
    record.late_minutes = metrics["late_minutes"]
    record.early_departure_minutes = metrics["early_departure_minutes"]
    record.overtime_minutes = metrics["overtime_minutes"]
    record.missing_punch = metrics["missing_punch"]
    record.shift_id = metrics["shift_id"]
    record.schedule_id = metrics["schedule_id"]
    record.updated_at = utcnow()
    if record.id:
        await record.save()
    else:
        await record.insert()
    await _sync_legacy_day(record)
    return record


async def ingest_attendance_event(scope: AccessScope, payload: AttendanceEventIngest) -> AttendanceRecordRead:
    authorize_hr_attendance_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    if await HrEmployeeAttendanceEvent.find_one(
        Eq(HrEmployeeAttendanceEvent.tenant_id, tenant_id),
        Eq(HrEmployeeAttendanceEvent.idempotency_key, payload.idempotency_key),
    ):
        existing = await HrEmployeeAttendanceRecord.find_one(
            Eq(HrEmployeeAttendanceRecord.tenant_id, tenant_id),
            Eq(HrEmployeeAttendanceRecord.employee_user_id, to_object_id(payload.employee_user_id, "employee_user_id")),
            Eq(HrEmployeeAttendanceRecord.attendance_date, payload.event_at.date()),
        )
        if existing:
            return AttendanceRecordRead.from_document(existing)
        raise AppError(code="CONFLICT", message="Duplicate event with no aggregate", status_code=409)
    uid = to_object_id(payload.employee_user_id, "employee_user_id")
    await HrEmployeeAttendanceEvent(
        tenant_id=tenant_id,
        employee_user_id=uid,
        event_type=payload.event_type,
        event_at=payload.event_at,
        source=payload.source,
        device_reference=payload.device_reference,
        idempotency_key=payload.idempotency_key,
        raw_payload=payload.raw_payload,
        actor_id=scope.user_id,
    ).insert()
    record = await reprocess_attendance_day(tenant_id, uid, payload.event_at.date())
    return AttendanceRecordRead.from_document(record)


async def manual_attendance_entry(scope: AccessScope, payload: AttendanceManualDay) -> AttendanceRecordRead:
    authorize_hr_attendance_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(payload.employee_user_id, "employee_user_id")
    if payload.check_in_at:
        await ingest_attendance_event(
            scope,
            AttendanceEventIngest(
                employee_user_id=payload.employee_user_id,
                event_type=HrAttendanceEventType.CHECK_IN,
                event_at=payload.check_in_at,
                source=HrAttendanceEventSource.MANUAL_HR,
                idempotency_key=f"manual:in:{uid}:{payload.attendance_date.isoformat()}",
            ),
        )
    if payload.check_out_at:
        await ingest_attendance_event(
            scope,
            AttendanceEventIngest(
                employee_user_id=payload.employee_user_id,
                event_type=HrAttendanceEventType.CHECK_OUT,
                event_at=payload.check_out_at,
                source=HrAttendanceEventSource.MANUAL_HR,
                idempotency_key=f"manual:out:{uid}:{payload.attendance_date.isoformat()}",
            ),
        )
    record = await reprocess_attendance_day(tenant_id, uid, payload.attendance_date)
    if payload.status:
        record.status = payload.status
        record.updated_at = utcnow()
        await record.save()
        await _sync_legacy_day(record)
    return AttendanceRecordRead.from_document(record)


async def submit_attendance_correction(scope: AccessScope, payload: AttendanceCorrectionCreate) -> dict:
    authorize_hr_attendance_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(payload.employee_user_id, "employee_user_id")
    current = await HrEmployeeAttendanceRecord.find_one(
        Eq(HrEmployeeAttendanceRecord.tenant_id, tenant_id),
        Eq(HrEmployeeAttendanceRecord.employee_user_id, uid),
        Eq(HrEmployeeAttendanceRecord.attendance_date, payload.attendance_date),
    )
    previous = {}
    if current:
        previous = {
            "status": current.status.value,
            "first_check_in": current.first_check_in.isoformat() if current.first_check_in else None,
            "last_check_out": current.last_check_out.isoformat() if current.last_check_out else None,
        }
    row = EmployeeAttendanceCorrection(
        tenant_id=tenant_id,
        employee_user_id=uid,
        attendance_date=payload.attendance_date,
        requested_status=payload.requested_status,
        reason=payload.reason,
        status=EmployeeAttendanceCorrectionStatus.PENDING_MANAGER,
        previous_snapshot=previous,
        proposed_snapshot={
            "status": payload.requested_status.value,
            "check_in": payload.proposed_check_in.isoformat() if payload.proposed_check_in else None,
            "check_out": payload.proposed_check_out.isoformat() if payload.proposed_check_out else None,
        },
    )
    await row.insert()
    return {"correction_id": str(row.id)}


async def review_attendance_correction(scope: AccessScope, correction_id: str, payload: AttendanceCorrectionReview) -> dict:
    authorize_hr_attendance_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    cid = to_object_id(correction_id, "correction_id")
    row = await EmployeeAttendanceCorrection.get(cid)
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Correction not found", status_code=404)
    if payload.decision == "manager_approve" and row.status == EmployeeAttendanceCorrectionStatus.PENDING_MANAGER:
        row.status = EmployeeAttendanceCorrectionStatus.PENDING_HR
        row.manager_reviewer_id = scope.user_id
    elif payload.decision in {"hr_approve", "approve"} and row.status in {
        EmployeeAttendanceCorrectionStatus.PENDING_HR,
        EmployeeAttendanceCorrectionStatus.PENDING,
    }:
        record = await HrEmployeeAttendanceRecord.find_one(
            Eq(HrEmployeeAttendanceRecord.tenant_id, tenant_id),
            Eq(HrEmployeeAttendanceRecord.employee_user_id, row.employee_user_id),
            Eq(HrEmployeeAttendanceRecord.attendance_date, row.attendance_date),
        )
        if record is None:
            record = HrEmployeeAttendanceRecord(
                tenant_id=tenant_id,
                employee_user_id=row.employee_user_id,
                attendance_date=row.attendance_date,
                status=row.requested_status,
            )
        else:
            record.previous_snapshot = row.previous_snapshot
            record.status = row.requested_status
        record.updated_at = utcnow()
        if record.id:
            await record.save()
        else:
            await record.insert()
        await _sync_legacy_day(record)
        row.status = EmployeeAttendanceCorrectionStatus.APPROVED
        row.hr_reviewer_id = scope.user_id
        row.reviewer_id = scope.user_id
        row.reviewer_note = payload.note
        row.applied = True
        row.resolved_at = utcnow()
        await enqueue_hr_notification(
            tenant_id,
            event_type="hr.attendance.correction.approved",
            aggregate_type="attendance_correction",
            aggregate_id=str(row.id),
            title="Attendance correction approved",
            body=f"Attendance for {row.attendance_date.isoformat()} updated",
            recipient_user_id=row.employee_user_id,
            dedupe_key=f"hr:att_corr:{row.id}",
        )
    elif payload.decision == "reject":
        row.status = EmployeeAttendanceCorrectionStatus.REJECTED
        row.reviewer_id = scope.user_id
        row.reviewer_note = payload.note
        row.resolved_at = utcnow()
    else:
        raise AppError(code="CONFLICT", message="Invalid correction decision", status_code=409)
    row.updated_at = utcnow()
    await row.save()
    await log_hr_activity(
        tenant_id,
        HrStaffActivityType.ATTENDANCE_CORRECTION,
        f"Attendance correction {row.status.value}",
        actor_id=scope.user_id,
        employee_user_id=row.employee_user_id,
        resource_type="attendance_correction",
        resource_id=str(row.id),
    )
    return {"correction_id": str(row.id), "status": row.status.value}


async def attendance_overview(scope: AccessScope) -> AttendanceOverview:
    authorize_hr_attendance_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    stats = AttendanceOverview()
    stats.pending_corrections = await EmployeeAttendanceCorrection.find(
        Eq(EmployeeAttendanceCorrection.tenant_id, tenant_id),
        Eq(EmployeeAttendanceCorrection.status, EmployeeAttendanceCorrectionStatus.PENDING_HR),
    ).count()
    stats.pending_corrections += await EmployeeAttendanceCorrection.find(
        Eq(EmployeeAttendanceCorrection.tenant_id, tenant_id),
        Eq(EmployeeAttendanceCorrection.status, EmployeeAttendanceCorrectionStatus.PENDING_MANAGER),
    ).count()
    today = date.today()
    stats.missing_punch_today = await HrEmployeeAttendanceRecord.find(
        Eq(HrEmployeeAttendanceRecord.tenant_id, tenant_id),
        Eq(HrEmployeeAttendanceRecord.attendance_date, today),
        Eq(HrEmployeeAttendanceRecord.missing_punch, True),
    ).count()
    stats.locked_months = await HrEmployeeAttendanceMonthlySummary.find(
        Eq(HrEmployeeAttendanceMonthlySummary.tenant_id, tenant_id),
        Eq(HrEmployeeAttendanceMonthlySummary.status, HrMonthlyAttendanceStatus.LOCKED),
    ).count()
    return stats


async def _aggregate_month(tenant_id: PydanticObjectId, employee_user_id: PydanticObjectId, year: int, month: int) -> HrEmployeeAttendanceMonthlySummary:
    start = date(year, month, 1)
    _, last_day = monthrange(year, month)
    end = date(year, month, last_day)
    records = await HrEmployeeAttendanceRecord.find(
        Eq(HrEmployeeAttendanceRecord.tenant_id, tenant_id),
        Eq(HrEmployeeAttendanceRecord.employee_user_id, employee_user_id),
        GTE(HrEmployeeAttendanceRecord.attendance_date, start),
        LTE(HrEmployeeAttendanceRecord.attendance_date, end),
    ).to_list()
    summary = await HrEmployeeAttendanceMonthlySummary.find_one(
        Eq(HrEmployeeAttendanceMonthlySummary.tenant_id, tenant_id),
        Eq(HrEmployeeAttendanceMonthlySummary.employee_user_id, employee_user_id),
        Eq(HrEmployeeAttendanceMonthlySummary.period_year, year),
        Eq(HrEmployeeAttendanceMonthlySummary.period_month, month),
    )
    if summary is None:
        summary = HrEmployeeAttendanceMonthlySummary(
            tenant_id=tenant_id,
            employee_user_id=employee_user_id,
            period_year=year,
            period_month=month,
        )
    present = absent = late = missing = 0
    leave_days = 0.0
    total_work = ot = 0
    for rec in records:
        if rec.status in {EmployeeAttendanceDayStatus.PRESENT, EmployeeAttendanceDayStatus.LATE, EmployeeAttendanceDayStatus.HALF_DAY, EmployeeAttendanceDayStatus.WORK_FROM_HOME}:
            present += 1
        elif rec.status == EmployeeAttendanceDayStatus.ABSENT:
            absent += 1
        elif rec.status == EmployeeAttendanceDayStatus.ON_LEAVE:
            leave_days += 1
        if rec.late_minutes > 0:
            late += 1
        if rec.missing_punch:
            missing += 1
        total_work += rec.working_minutes
        ot += rec.overtime_minutes
    summary.present_days = present
    summary.absent_days = absent
    summary.leave_days = leave_days
    summary.late_days = late
    summary.missing_punch_days = missing
    summary.total_working_minutes = total_work
    summary.overtime_minutes = ot
    summary.updated_at = utcnow()
    if summary.id:
        await summary.save()
    else:
        await summary.insert()
    return summary


async def close_monthly_attendance(scope: AccessScope, payload: MonthlyAttendanceAction) -> MonthlySummaryRead:
    authorize_hr_attendance_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    employees = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    if payload.department_id:
        dept = to_object_id(payload.department_id, "department_id")
        employees = [e for e in employees if e.department_id == dept]
    for emp in employees:
        await _aggregate_month(tenant_id, emp.user_id, payload.period_year, payload.period_month)
    dept_summary = HrEmployeeAttendanceMonthlySummary(
        tenant_id=tenant_id,
        employee_user_id=None,
        department_id=to_object_id(payload.department_id, "department_id") if payload.department_id else None,
        period_year=payload.period_year,
        period_month=payload.period_month,
        status=HrMonthlyAttendanceStatus.CLOSING,
        actor_id=scope.user_id,
    )
    await dept_summary.insert()
    return MonthlySummaryRead.from_dict(
        {"period_year": payload.period_year, "period_month": payload.period_month, "status": HrMonthlyAttendanceStatus.CLOSING, "present_days": 0, "absent_days": 0}
    )


async def lock_monthly_attendance(scope: AccessScope, payload: MonthlyAttendanceAction) -> dict:
    authorize_hr_attendance_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    summaries = await HrEmployeeAttendanceMonthlySummary.find(
        Eq(HrEmployeeAttendanceMonthlySummary.tenant_id, tenant_id),
        Eq(HrEmployeeAttendanceMonthlySummary.period_year, payload.period_year),
        Eq(HrEmployeeAttendanceMonthlySummary.period_month, payload.period_month),
    ).to_list()
    for summary in summaries:
        summary.status = HrMonthlyAttendanceStatus.LOCKED
        summary.locked_at = utcnow()
        summary.locked_by = scope.user_id
        summary.updated_at = utcnow()
        await summary.save()
    start = date(payload.period_year, payload.period_month, 1)
    _, last_day = monthrange(payload.period_year, payload.period_month)
    end = date(payload.period_year, payload.period_month, last_day)
    records = await HrEmployeeAttendanceRecord.find(
        Eq(HrEmployeeAttendanceRecord.tenant_id, tenant_id),
        GTE(HrEmployeeAttendanceRecord.attendance_date, start),
        LTE(HrEmployeeAttendanceRecord.attendance_date, end),
    ).to_list()
    for rec in records:
        rec.locked = True
        rec.updated_at = utcnow()
        await rec.save()
    return {"locked_records": len(records), "summaries": len(summaries)}


async def reopen_monthly_attendance(scope: AccessScope, payload: MonthlyAttendanceAction) -> dict:
    authorize_hr_attendance_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    if not payload.reopen_reason:
        raise AppError(code="VALIDATION_ERROR", message="Reopen reason required", status_code=422)
    summaries = await HrEmployeeAttendanceMonthlySummary.find(
        Eq(HrEmployeeAttendanceMonthlySummary.tenant_id, tenant_id),
        Eq(HrEmployeeAttendanceMonthlySummary.period_year, payload.period_year),
        Eq(HrEmployeeAttendanceMonthlySummary.period_month, payload.period_month),
        Eq(HrEmployeeAttendanceMonthlySummary.status, HrMonthlyAttendanceStatus.LOCKED),
    ).to_list()
    for summary in summaries:
        summary.status = HrMonthlyAttendanceStatus.REOPENED
        summary.reopen_reason = payload.reopen_reason
        summary.updated_at = utcnow()
        await summary.save()
    return {"reopened": len(summaries)}


async def list_attendance_records(
    scope: AccessScope,
    pagination: Pagination,
    employee_user_id: str | None,
    start_date: date | None,
    end_date: date | None,
) -> Page[AttendanceRecordRead]:
    authorize_hr_attendance_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    filters = [Eq(HrEmployeeAttendanceRecord.tenant_id, tenant_id)]
    if employee_user_id:
        filters.append(Eq(HrEmployeeAttendanceRecord.employee_user_id, to_object_id(employee_user_id, "employee_user_id")))
    if start_date:
        filters.append(GTE(HrEmployeeAttendanceRecord.attendance_date, start_date))
    if end_date:
        filters.append(LTE(HrEmployeeAttendanceRecord.attendance_date, end_date))
    q = HrEmployeeAttendanceRecord.find(*filters)
    total = await q.count()
    rows = await q.sort(-HrEmployeeAttendanceRecord.attendance_date).skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[AttendanceRecordRead.from_document(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)