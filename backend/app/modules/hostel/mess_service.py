"""Hostel mess management, enrollment and billing services."""

from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.finance.finance_enums import FeeDemandStatus
from app.modules.finance.finance_models import StudentFeeDemand
from app.modules.hostel.hostel_notify import notify_hostel_student
from app.modules.hostel.mess_models import (
    HostelMealAttendance,
    HostelMealCategory,
    HostelMenu,
    HostelMess,
    HostelMessBillingAdjustment,
    HostelMessBillingPeriod,
    HostelMessBillingRecord,
    HostelMessEnrollment,
    HostelMessFinanceReference,
    HostelMessPlan,
    MessBillingMethod,
    MessBillingPeriodStatus,
    MessBillingRecordStatus,
    MessEnrollmentStatus,
    MessPlanStatus,
)
from app.modules.hostel.mess_schemas import (
    BillingAdjustmentCreate,
    BillingCalculateInput,
    BillingPeriodCreate,
    BillingRecordRead,
    BillingSendFinanceInput,
    HostelMessCreate,
    HostelMessRead,
    MealAttendanceRecord,
    MealCategoryUpsert,
    MenuRead,
    MenuUpsert,
    MessEnrollmentCreate,
    MessEnrollmentDecision,
    MessEnrollmentRead,
    MessEnrollmentReport,
    MessPlanRead,
    MessPlanUpsertPortal,
)
from app.modules.hostel.policy import authorize_hostel_mess_manage, authorize_hostel_mess_read, require_hostel_tenant_scope
from app.modules.hostel.resident_models import HostelResident, HostelResidentStatus


def _plan_rate(plan: HostelMessPlan) -> float:
    if plan.rate is not None:
        return plan.rate
    return plan.monthly_amount


def _prorate_monthly(rate: float, period_start: date, period_end: date, enroll_start: date, enroll_end: date | None) -> tuple[float, int]:
    start = max(period_start, enroll_start)
    end = min(period_end, enroll_end or period_end)
    if end < start:
        return 0.0, 0
    days_active = (end - start).days + 1
    total_days = (period_end - period_start).days + 1
    return round(rate * days_active / total_days, 2), days_active


async def _require_checked_in_resident(tenant_id: PydanticObjectId, resident_id: str) -> HostelResident:
    doc = await HostelResident.find_one(Eq(HostelResident.tenant_id, tenant_id), Eq(HostelResident.resident_id, resident_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Resident not found", status_code=404)
    if doc.status not in (HostelResidentStatus.CHECKED_IN, HostelResidentStatus.TEMPORARILY_OUTSIDE):
        raise AppError(code="VALIDATION_ERROR", message="Resident must be checked in for mess enrollment", status_code=422)
    return doc


async def upsert_mess(scope: AccessScope, payload: HostelMessCreate) -> HostelMessRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_mess_manage(scope)
    code = payload.mess_code.strip().upper()
    doc = await HostelMess.find_one(Eq(HostelMess.tenant_id, tenant_id), Eq(HostelMess.mess_code, code))
    if doc:
        doc.name = payload.name.strip()
        doc.hostel_codes = [h.upper() for h in payload.hostel_codes]
        doc.building_codes = [b.upper() for b in payload.building_codes]
        doc.capacity = payload.capacity
        doc.operating_hours = payload.operating_hours
        doc.supervisor_user_ids = payload.supervisor_user_ids
        doc.status = payload.status
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = await HostelMess(
            tenant_id=tenant_id,
            mess_code=code,
            name=payload.name.strip(),
            hostel_codes=[h.upper() for h in payload.hostel_codes],
            building_codes=[b.upper() for b in payload.building_codes],
            capacity=payload.capacity,
            operating_hours=payload.operating_hours,
            supervisor_user_ids=payload.supervisor_user_ids,
            status=payload.status,
        ).insert()
    await append_institution_audit(
        tenant_id, actor_id=scope.user_id, action="hostel.mess.upsert", module="hostel_mess", resource_type="mess", resource_id=code
    )
    return HostelMessRead(
        mess_code=doc.mess_code,
        name=doc.name,
        hostel_codes=doc.hostel_codes,
        building_codes=doc.building_codes,
        capacity=doc.capacity,
        operating_hours=doc.operating_hours,
        supervisor_user_ids=doc.supervisor_user_ids,
        status=doc.status,
        updated_at=doc.updated_at,
    )


async def list_messes(scope: AccessScope) -> list[HostelMessRead]:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_mess_read(scope)
    rows = await HostelMess.find(Eq(HostelMess.tenant_id, tenant_id)).to_list()
    return [
        HostelMessRead(
            mess_code=r.mess_code,
            name=r.name,
            hostel_codes=r.hostel_codes,
            building_codes=r.building_codes,
            capacity=r.capacity,
            operating_hours=r.operating_hours,
            supervisor_user_ids=r.supervisor_user_ids,
            status=r.status,
            updated_at=r.updated_at,
        )
        for r in rows
    ]


async def upsert_plan(scope: AccessScope, payload: MessPlanUpsertPortal) -> MessPlanRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_mess_manage(scope)
    code = payload.plan_code.strip().upper()
    doc = await HostelMessPlan.find_one(Eq(HostelMessPlan.tenant_id, tenant_id), Eq(HostelMessPlan.plan_code, code))
    if doc:
        doc.title = payload.title.strip()
        doc.description = payload.description
        doc.mess_code = payload.mess_code.upper() if payload.mess_code else doc.mess_code
        doc.included_meals = payload.included_meals
        doc.billing_method = payload.billing_method
        doc.monthly_amount = payload.monthly_amount
        doc.rate = payload.monthly_amount
        doc.billing_frequency = payload.billing_frequency
        doc.effective_from = payload.effective_from
        doc.effective_to = payload.effective_to
        doc.requires_approval = payload.requires_approval
        doc.published = payload.published
        doc.status = payload.status
        doc.finance_reference = payload.finance_reference
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = await HostelMessPlan(
            tenant_id=tenant_id,
            plan_code=code,
            title=payload.title.strip(),
            description=payload.description,
            mess_code=payload.mess_code.upper() if payload.mess_code else None,
            included_meals=payload.included_meals,
            billing_method=payload.billing_method,
            monthly_amount=payload.monthly_amount,
            rate=payload.monthly_amount,
            billing_frequency=payload.billing_frequency,
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            requires_approval=payload.requires_approval,
            published=payload.published,
            status=payload.status,
            finance_reference=payload.finance_reference,
        ).insert()
    return _plan_read(doc)


def _plan_read(doc: HostelMessPlan) -> MessPlanRead:
    return MessPlanRead(
        plan_code=doc.plan_code,
        title=doc.title,
        mess_code=doc.mess_code,
        monthly_amount=doc.monthly_amount,
        billing_method=doc.billing_method,
        published=doc.published,
        status=doc.status,
        included_meals=doc.included_meals,
        finance_reference=doc.finance_reference,
        updated_at=doc.updated_at,
    )


async def list_plans(scope: AccessScope, *, mess_code: str | None = None) -> list[MessPlanRead]:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_mess_read(scope)
    q: dict = {"tenant_id": tenant_id}
    if mess_code:
        q["mess_code"] = mess_code.upper()
    rows = await HostelMessPlan.find(q).to_list()
    return [_plan_read(r) for r in rows]


async def upsert_meal_category(scope: AccessScope, payload: MealCategoryUpsert) -> dict:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_mess_manage(scope)
    code = payload.category_code.strip().upper()
    doc = await HostelMealCategory.find_one(Eq(HostelMealCategory.tenant_id, tenant_id), Eq(HostelMealCategory.category_code, code))
    if doc:
        doc.label = payload.label
        doc.mess_code = payload.mess_code.upper() if payload.mess_code else doc.mess_code
        doc.default_start_time = payload.default_start_time
        doc.default_end_time = payload.default_end_time
        doc.serving_days = payload.serving_days
        doc.active = payload.active
        doc.updated_at = utcnow()
        await doc.save()
    else:
        await HostelMealCategory(
            tenant_id=tenant_id,
            category_code=code,
            label=payload.label,
            mess_code=payload.mess_code.upper() if payload.mess_code else None,
            default_start_time=payload.default_start_time,
            default_end_time=payload.default_end_time,
            serving_days=payload.serving_days,
            active=payload.active,
        ).insert()
    return {"category_code": code}


async def upsert_menu(scope: AccessScope, payload: MenuUpsert) -> MenuRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_mess_manage(scope)
    menu_id = payload.menu_id or f"menu_{uuid4().hex[:10]}"
    doc = await HostelMenu.find_one(Eq(HostelMenu.tenant_id, tenant_id), Eq(HostelMenu.menu_id, menu_id))
    if doc:
        doc.items = payload.items
        doc.dietary_labels = payload.dietary_labels
        doc.revision += 1
        if payload.publish:
            doc.published = True
            doc.published_at = utcnow()
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = await HostelMenu(
            tenant_id=tenant_id,
            menu_id=menu_id,
            mess_code=payload.mess_code.upper(),
            menu_scope=payload.menu_scope,
            meal_category_code=payload.meal_category_code.upper() if payload.meal_category_code else None,
            service_date=payload.service_date,
            items=payload.items,
            dietary_labels=payload.dietary_labels,
            published=payload.publish,
            published_at=utcnow() if payload.publish else None,
        ).insert()
    return MenuRead(
        menu_id=doc.menu_id,
        mess_code=doc.mess_code,
        menu_scope=doc.menu_scope,
        service_date=doc.service_date,
        items=doc.items,
        published=doc.published,
        revision=doc.revision,
        updated_at=doc.updated_at,
    )


def _enrollment_read(doc: HostelMessEnrollment) -> MessEnrollmentRead:
    return MessEnrollmentRead(
        enrollment_id=doc.enrollment_id,
        resident_id=doc.resident_id,
        student_user_id=str(doc.student_user_id),
        mess_code=doc.mess_code,
        plan_code=doc.plan_code,
        start_date=doc.start_date,
        end_date=doc.end_date,
        status=doc.status,
        rate_snapshot=doc.rate_snapshot,
    )


async def create_enrollment(scope: AccessScope, payload: MessEnrollmentCreate) -> MessEnrollmentRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_mess_manage(scope)
    resident = await _require_checked_in_resident(tenant_id, payload.resident_id)
    plan = await HostelMessPlan.find_one(Eq(HostelMessPlan.tenant_id, tenant_id), Eq(HostelMessPlan.plan_code, payload.plan_code.upper()))
    if plan is None or plan.status != MessPlanStatus.ACTIVE:
        raise AppError(code="NOT_FOUND", message="Mess plan not found or inactive", status_code=404)
    dup = await HostelMessEnrollment.find_one(
        {
            "tenant_id": tenant_id,
            "resident_id": payload.resident_id,
            "status": {"$in": [MessEnrollmentStatus.PENDING_APPROVAL.value, MessEnrollmentStatus.ACTIVE.value, MessEnrollmentStatus.PAUSED.value]},
        }
    )
    if dup:
        raise AppError(code="CONFLICT", message="Resident already has an active mess enrollment", status_code=409)
    status = MessEnrollmentStatus.PENDING_APPROVAL if plan.requires_approval else MessEnrollmentStatus.ACTIVE
    enrollment_id = f"men_{uuid4().hex[:10]}"
    doc = await HostelMessEnrollment(
        tenant_id=tenant_id,
        enrollment_id=enrollment_id,
        resident_id=resident.resident_id,
        student_user_id=resident.student_user_id,
        mess_code=payload.mess_code.upper(),
        plan_code=plan.plan_code,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status=status,
        rate_snapshot=_plan_rate(plan),
        billing_method=plan.billing_method,
        approved_by=scope.user_id if status == MessEnrollmentStatus.ACTIVE else None,
        approved_at=utcnow() if status == MessEnrollmentStatus.ACTIVE else None,
    ).insert()
    await notify_hostel_student(
        tenant_id,
        student_user_id=resident.student_user_id,
        event_type="mess.enrollment",
        title="Mess enrollment",
        body=f"Mess plan {plan.title} enrollment submitted.",
        aggregate_id=enrollment_id,
    )
    return _enrollment_read(doc)


async def decide_enrollment(scope: AccessScope, payload: MessEnrollmentDecision) -> MessEnrollmentRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_mess_manage(scope)
    doc = await HostelMessEnrollment.find_one(
        Eq(HostelMessEnrollment.tenant_id, tenant_id), Eq(HostelMessEnrollment.enrollment_id, payload.enrollment_id)
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Enrollment not found", status_code=404)
    if doc.status != MessEnrollmentStatus.PENDING_APPROVAL:
        raise AppError(code="CONFLICT", message="Enrollment not pending approval", status_code=409)
    doc.status = MessEnrollmentStatus.ACTIVE if payload.approve else MessEnrollmentStatus.CANCELLED
    doc.approved_by = scope.user_id if payload.approve else None
    doc.approved_at = utcnow() if payload.approve else None
    if not payload.approve:
        doc.cancelled_at = utcnow()
    doc.updated_at = utcnow()
    await doc.save()
    return _enrollment_read(doc)


async def list_enrollments(
    scope: AccessScope,
    pagination: Pagination,
    *,
    mess_code: str | None = None,
    plan_code: str | None = None,
    status: MessEnrollmentStatus | None = None,
) -> Page[MessEnrollmentRead]:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_mess_read(scope)
    q: dict = {"tenant_id": tenant_id}
    if mess_code:
        q["mess_code"] = mess_code.upper()
    if plan_code:
        q["plan_code"] = plan_code.upper()
    if status:
        q["status"] = status.value
    total = await HostelMessEnrollment.find(q).count()
    skip = (pagination.page - 1) * pagination.page_size
    rows = await HostelMessEnrollment.find(q).sort("-created_at").skip(skip).limit(pagination.page_size).to_list()
    return Page(items=[_enrollment_read(r) for r in rows], total=total, page=pagination.page, page_size=pagination.page_size)


async def record_meal_attendance(scope: AccessScope, payload: MealAttendanceRecord) -> dict:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_mess_manage(scope)
    enr = await HostelMessEnrollment.find_one(
        Eq(HostelMessEnrollment.tenant_id, tenant_id), Eq(HostelMessEnrollment.enrollment_id, payload.enrollment_id)
    )
    if enr is None:
        raise AppError(code="NOT_FOUND", message="Enrollment not found", status_code=404)
    attendance_id = f"mat_{uuid4().hex[:10]}"
    existing = await HostelMealAttendance.find_one(
        {
            "tenant_id": tenant_id,
            "enrollment_id": payload.enrollment_id,
            "service_date": payload.service_date,
            "meal_category_code": payload.meal_category_code.upper(),
        }
    )
    if existing:
        existing.attended = payload.attended
        existing.exemption_reason = payload.exemption_reason
        existing.capture_method = payload.capture_method
        existing.recorded_by = scope.user_id
        await existing.save()
        return {"attendance_id": existing.attendance_id, "updated": True}
    await HostelMealAttendance(
        tenant_id=tenant_id,
        attendance_id=attendance_id,
        enrollment_id=payload.enrollment_id,
        student_user_id=enr.student_user_id,
        mess_code=enr.mess_code,
        meal_category_code=payload.meal_category_code.upper(),
        service_date=payload.service_date,
        attended=payload.attended,
        capture_method=payload.capture_method,
        exemption_reason=payload.exemption_reason,
        recorded_by=scope.user_id,
    ).insert()
    return {"attendance_id": attendance_id, "updated": False}


async def create_billing_period(scope: AccessScope, payload: BillingPeriodCreate) -> dict:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_mess_manage(scope)
    if payload.period_end < payload.period_start:
        raise AppError(code="VALIDATION_ERROR", message="Invalid period range", status_code=422)
    period_id = payload.period_id or f"mbp_{uuid4().hex[:10]}"
    if await HostelMessBillingPeriod.find_one(Eq(HostelMessBillingPeriod.tenant_id, tenant_id), Eq(HostelMessBillingPeriod.period_id, period_id)):
        raise AppError(code="CONFLICT", message="Billing period already exists", status_code=409)
    await HostelMessBillingPeriod(
        tenant_id=tenant_id,
        period_id=period_id,
        mess_code=payload.mess_code.upper() if payload.mess_code else None,
        label=payload.label,
        period_start=payload.period_start,
        period_end=payload.period_end,
        status=MessBillingPeriodStatus.DRAFT,
        created_by=scope.user_id,
    ).insert()
    return {"period_id": period_id}


async def calculate_billing_period(scope: AccessScope, payload: BillingCalculateInput) -> dict:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_mess_manage(scope)
    period = await HostelMessBillingPeriod.find_one(
        Eq(HostelMessBillingPeriod.tenant_id, tenant_id), Eq(HostelMessBillingPeriod.period_id, payload.period_id)
    )
    if period is None:
        raise AppError(code="NOT_FOUND", message="Billing period not found", status_code=404)
    period.status = MessBillingPeriodStatus.CALCULATING
    await period.save()
    enroll_q: dict = {
        "tenant_id": tenant_id,
        "status": MessEnrollmentStatus.ACTIVE.value,
        "start_date": {"$lte": period.period_end},
        "$or": [{"end_date": None}, {"end_date": {"$gte": period.period_start}}],
    }
    if period.mess_code:
        enroll_q["mess_code"] = period.mess_code
    enrollments = await HostelMessEnrollment.find(enroll_q).to_list()
    created = 0
    for enr in enrollments:
        exists = await HostelMessBillingRecord.find_one(
            {"tenant_id": tenant_id, "period_id": period.period_id, "enrollment_id": enr.enrollment_id}
        )
        if exists:
            continue
        amount, days = _prorate_monthly(enr.rate_snapshot, period.period_start, period.period_end, enr.start_date, enr.end_date)
        if enr.billing_method == MessBillingMethod.PER_MEAL and period.mess_code:
            count = await HostelMealAttendance.find(
                {
                    "tenant_id": tenant_id,
                    "enrollment_id": enr.enrollment_id,
                    "service_date": {"$gte": period.period_start, "$lte": period.period_end},
                    "attended": True,
                }
            ).count()
            amount = round(count * enr.rate_snapshot, 2)
        adj_sum = 0.0
        adjs = await HostelMessBillingAdjustment.find(
            {"tenant_id": tenant_id, "enrollment_id": enr.enrollment_id}
        ).to_list()
        for a in adjs:
            adj_sum += a.amount_delta
        amount = max(0.0, round(amount + adj_sum, 2))
        record_id = f"mbr_{uuid4().hex[:10]}"
        await HostelMessBillingRecord(
            tenant_id=tenant_id,
            record_id=record_id,
            period_id=period.period_id,
            enrollment_id=enr.enrollment_id,
            student_user_id=enr.student_user_id,
            resident_id=enr.resident_id,
            plan_code=enr.plan_code,
            mess_code=enr.mess_code,
            amount=amount,
            proration_days=days,
            status=MessBillingRecordStatus.DRAFT if amount > 0 else MessBillingRecordStatus.APPROVED,
        ).insert()
        created += 1
    period.status = MessBillingPeriodStatus.PENDING_REVIEW
    period.updated_at = utcnow()
    await period.save()
    return {"period_id": period.period_id, "records_created": created}


async def approve_billing_record(scope: AccessScope, record_id: str) -> BillingRecordRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_mess_manage(scope)
    doc = await HostelMessBillingRecord.find_one(
        Eq(HostelMessBillingRecord.tenant_id, tenant_id), Eq(HostelMessBillingRecord.record_id, record_id)
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Billing record not found", status_code=404)
    doc.status = MessBillingRecordStatus.APPROVED
    doc.updated_at = utcnow()
    await doc.save()
    return BillingRecordRead(
        record_id=doc.record_id,
        period_id=doc.period_id,
        enrollment_id=doc.enrollment_id,
        student_user_id=str(doc.student_user_id),
        amount=doc.amount,
        status=doc.status,
        finance_demand_id=doc.finance_demand_id,
    )


async def send_billing_to_finance(scope: AccessScope, payload: BillingSendFinanceInput) -> dict:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_mess_manage(scope)
    period = await HostelMessBillingPeriod.find_one(
        Eq(HostelMessBillingPeriod.tenant_id, tenant_id), Eq(HostelMessBillingPeriod.period_id, payload.period_id)
    )
    if period is None:
        raise AppError(code="NOT_FOUND", message="Billing period not found", status_code=404)
    rows = await HostelMessBillingRecord.find(
        {
            "tenant_id": tenant_id,
            "period_id": payload.period_id,
            "status": MessBillingRecordStatus.APPROVED.value,
            "finance_demand_id": None,
            "amount": {"$gt": 0},
        }
    ).to_list()
    sent = 0
    for row in rows:
        demand_id = f"hmd_{uuid4().hex[:10]}"
        due = period.period_end + timedelta(days=14)
        await StudentFeeDemand(
            tenant_id=tenant_id,
            student_user_id=row.student_user_id,
            demand_id=demand_id,
            academic_year_label="hostel",
            semester_label="mess",
            description=f"Hostel mess {row.plan_code} period {period.label}",
            amount=row.amount,
            due_date=due,
            status=FeeDemandStatus.OPEN,
        ).insert()
        ref_id = f"mfr_{uuid4().hex[:10]}"
        await HostelMessFinanceReference(
            tenant_id=tenant_id,
            reference_id=ref_id,
            record_id=row.record_id,
            demand_id=demand_id,
            student_user_id=row.student_user_id,
            amount=row.amount,
            synced_status=FeeDemandStatus.OPEN.value,
            last_synced_at=utcnow(),
        ).insert()
        row.finance_demand_id = demand_id
        row.status = MessBillingRecordStatus.SENT_TO_FINANCE
        row.updated_at = utcnow()
        await row.save()
        sent += 1
    period.status = MessBillingPeriodStatus.SENT_TO_FINANCE
    period.updated_at = utcnow()
    await period.save()
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="hostel.mess.billing_sent_finance",
        module="hostel_mess",
        resource_type="billing_period",
        resource_id=payload.period_id,
    )
    return {"period_id": payload.period_id, "demands_created": sent}


async def sync_billing_payments(scope: AccessScope, period_id: str) -> dict:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_mess_read(scope)
    rows = await HostelMessBillingRecord.find(
        {"tenant_id": tenant_id, "period_id": period_id, "finance_demand_id": {"$ne": None}}
    ).to_list()
    updated = 0
    for row in rows:
        demand = await StudentFeeDemand.find_one(
            Eq(StudentFeeDemand.tenant_id, tenant_id), Eq(StudentFeeDemand.demand_id, row.finance_demand_id)
        )
        if demand is None:
            continue
        ref = await HostelMessFinanceReference.find_one(
            Eq(HostelMessFinanceReference.tenant_id, tenant_id), Eq(HostelMessFinanceReference.record_id, row.record_id)
        )
        if ref:
            ref.synced_status = demand.status.value
            ref.last_synced_at = utcnow()
            await ref.save()
        if demand.status == FeeDemandStatus.PAID:
            row.status = MessBillingRecordStatus.PAID
            updated += 1
        elif demand.status == FeeDemandStatus.PARTIALLY_PAID:
            row.status = MessBillingRecordStatus.PARTIALLY_PAID
            updated += 1
        elif demand.status == FeeDemandStatus.WAIVED:
            row.status = MessBillingRecordStatus.CANCELLED
            updated += 1
        row.updated_at = utcnow()
        await row.save()
    return {"period_id": period_id, "records_updated": updated}


async def add_billing_adjustment(scope: AccessScope, payload: BillingAdjustmentCreate) -> dict:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_mess_manage(scope)
    enr = await HostelMessEnrollment.find_one(
        Eq(HostelMessEnrollment.tenant_id, tenant_id), Eq(HostelMessEnrollment.enrollment_id, payload.enrollment_id)
    )
    if enr is None:
        raise AppError(code="NOT_FOUND", message="Enrollment not found", status_code=404)
    adj_id = f"mba_{uuid4().hex[:10]}"
    await HostelMessBillingAdjustment(
        tenant_id=tenant_id,
        adjustment_id=adj_id,
        enrollment_id=payload.enrollment_id,
        student_user_id=enr.student_user_id,
        amount_delta=payload.amount_delta,
        reason=payload.reason,
        source_type=payload.source_type,
        source_ref=payload.source_ref,
        approved_by=scope.user_id,
    ).insert()
    return {"adjustment_id": adj_id}


async def mess_enrollment_report(scope: AccessScope, *, mess_code: str | None = None) -> MessEnrollmentReport:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_mess_read(scope)
    q: dict = {"tenant_id": tenant_id, "status": MessEnrollmentStatus.ACTIVE.value}
    if mess_code:
        q["mess_code"] = mess_code.upper()
    rows = await HostelMessEnrollment.find(q).to_list()
    breakdown: dict[str, int] = {}
    for r in rows:
        breakdown[r.plan_code] = breakdown.get(r.plan_code, 0) + 1
    return MessEnrollmentReport(active_enrollments=len(rows), plan_breakdown=breakdown)


async def end_enrollment_on_checkout(tenant_id: PydanticObjectId, resident_id: str) -> None:
    """Called from resident checkout — end active mess enrollments."""
    rows = await HostelMessEnrollment.find(
        {
            "tenant_id": tenant_id,
            "resident_id": resident_id,
            "status": {"$in": [MessEnrollmentStatus.ACTIVE.value, MessEnrollmentStatus.PAUSED.value]},
        }
    ).to_list()
    today = utcnow().date()
    for doc in rows:
        doc.status = MessEnrollmentStatus.ENDED
        doc.end_date = today
        doc.updated_at = utcnow()
        await doc.save()