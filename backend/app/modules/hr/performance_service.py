"""Performance cycles, goals, reviews, PIPs and development plans."""

from decimal import Decimal

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.hr.employee_profile_models import HrEmployeeProfile
from app.modules.hr.enums import (
    HrDevelopmentPlanStatus,
    HrPerformanceCycleStatus,
    HrPerformanceGoalStatus,
    HrPerformancePipStatus,
    HrPerformanceReviewStatus,
)
from app.modules.hr.performance_models import (
    EmployeeDevelopmentPlan,
    EmployeePerformanceFeedback,
    EmployeePerformanceGoal,
    EmployeePerformanceImprovementPlan,
    EmployeePerformanceReview,
    HrPerformanceCriteria,
    HrPerformanceCycle,
)
from app.modules.hr.performance_schemas import (
    DevelopmentPlanUpsert,
    PerformanceCycleRead,
    PerformanceCycleUpsert,
    PerformanceGoalCreate,
    PerformanceGoalProgress,
    PerformanceGoalRead,
    PerformanceHrAction,
    PerformanceManagerAssessment,
    PerformanceReviewRead,
    PerformanceSelfAssessment,
    PipCreate,
)
from app.modules.hr.policy import (
    authorize_hr_performance_manage,
    authorize_hr_performance_read,
    authorize_hr_performance_review,
    require_employee_tenant_scope,
    require_hr_tenant_scope,
)


async def upsert_performance_cycle(scope: AccessScope, payload: PerformanceCycleUpsert) -> PerformanceCycleRead:
    authorize_hr_performance_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    doc = await HrPerformanceCycle.find_one(
        Eq(HrPerformanceCycle.tenant_id, tenant_id),
        Eq(HrPerformanceCycle.cycle_code, payload.cycle_code),
    )
    data = payload.model_dump()
    if doc:
        for k, v in data.items():
            setattr(doc, k, v)
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = HrPerformanceCycle(tenant_id=tenant_id, actor_id=scope.user_id, **data)
        await doc.insert()
    for item in payload.criteria:
        code = str(item.get("criteria_code"))
        if not code:
            continue
        existing = await HrPerformanceCriteria.find_one(
            Eq(HrPerformanceCriteria.tenant_id, tenant_id),
            Eq(HrPerformanceCriteria.cycle_id, doc.id),
            Eq(HrPerformanceCriteria.criteria_code, code),
        )
        if existing:
            existing.title = str(item.get("title", existing.title))
            existing.weight = str(item.get("weight", existing.weight))
            existing.description = item.get("description")
            await existing.save()
        else:
            await HrPerformanceCriteria(
                tenant_id=tenant_id,
                cycle_id=doc.id,
                criteria_code=code,
                title=str(item.get("title", code)),
                weight=str(item.get("weight", "0")),
                description=item.get("description"),
            ).insert()
    return PerformanceCycleRead.from_doc(doc)


async def activate_performance_cycle(scope: AccessScope, cycle_id: str) -> dict:
    authorize_hr_performance_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    cid = to_object_id(cycle_id, "cycle_id")
    cycle = await HrPerformanceCycle.get(cid)
    if cycle is None or cycle.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Cycle not found", status_code=404)
    cycle.status = HrPerformanceCycleStatus.ACTIVE
    cycle.updated_at = utcnow()
    await cycle.save()
    employees = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    created = 0
    for emp in employees:
        profile = await HrEmployeeProfile.find_one(
            Eq(HrEmployeeProfile.tenant_id, tenant_id),
            Eq(HrEmployeeProfile.user_id, emp.user_id),
        )
        if cycle.eligible_categories and profile and profile.employee_category not in cycle.eligible_categories:
            continue
        exists = await EmployeePerformanceReview.find_one(
            Eq(EmployeePerformanceReview.tenant_id, tenant_id),
            Eq(EmployeePerformanceReview.cycle_id, cycle.id),
            Eq(EmployeePerformanceReview.employee_user_id, emp.user_id),
        )
        if exists:
            continue
        manager_id = profile.reporting_manager_user_id if profile else None
        await EmployeePerformanceReview(
            tenant_id=tenant_id,
            cycle_id=cycle.id,
            employee_user_id=emp.user_id,
            manager_user_id=manager_id,
            status=HrPerformanceReviewStatus.SELF_ASSESSMENT,
            actor_id=scope.user_id,
        ).insert()
        created += 1
    return {"activated": True, "reviews_created": created}


async def create_goal(scope: AccessScope, payload: PerformanceGoalCreate) -> PerformanceGoalRead:
    authorize_hr_performance_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(payload.employee_user_id, "employee_user_id")
    row = EmployeePerformanceGoal(
        tenant_id=tenant_id,
        cycle_id=to_object_id(payload.cycle_id, "cycle_id") if payload.cycle_id else None,
        employee_user_id=uid,
        goal_code=payload.goal_code,
        title=payload.title,
        description=payload.description,
        goal_kind=payload.goal_kind,
        due_date=payload.due_date,
        target_value=payload.target_value,
        reviewer_user_id=to_object_id(payload.reviewer_user_id, "reviewer_user_id") if payload.reviewer_user_id else None,
        status=HrPerformanceGoalStatus.PENDING_APPROVAL,
        actor_id=scope.user_id,
    )
    await row.insert()
    return PerformanceGoalRead.from_doc(row)


async def approve_goal(scope: AccessScope, goal_id: str) -> PerformanceGoalRead:
    authorize_hr_performance_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    gid = to_object_id(goal_id, "goal_id")
    row = await EmployeePerformanceGoal.get(gid)
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Goal not found", status_code=404)
    row.status = HrPerformanceGoalStatus.ACTIVE
    row.updated_at = utcnow()
    await row.save()
    return PerformanceGoalRead.from_doc(row)


async def update_goal_progress(scope: AccessScope, goal_id: str, payload: PerformanceGoalProgress, *, self_service: bool) -> PerformanceGoalRead:
    gid = to_object_id(goal_id, "goal_id")
    row = await EmployeePerformanceGoal.get(gid)
    if row is None:
        raise AppError(code="NOT_FOUND", message="Goal not found", status_code=404)
    if self_service:
        if scope.user_id != row.employee_user_id:
            raise AppError(code="FORBIDDEN", message="Goal access denied", status_code=403)
        require_employee_tenant_scope(scope)
    else:
        authorize_hr_performance_manage(scope)
        require_hr_tenant_scope(scope)
    if row.tenant_id != scope.tenant_id:
        raise AppError(code="FORBIDDEN", message="Tenant mismatch", status_code=403)
    row.progress_percent = payload.progress_percent
    row.evidence_refs = payload.evidence_refs
    row.status = HrPerformanceGoalStatus.COMPLETED if payload.progress_percent >= 100 else HrPerformanceGoalStatus.IN_PROGRESS
    row.updated_at = utcnow()
    await row.save()
    return PerformanceGoalRead.from_doc(row)


async def submit_self_assessment(scope: AccessScope, review_id: str, payload: PerformanceSelfAssessment) -> PerformanceReviewRead:
    require_employee_tenant_scope(scope)
    rid = to_object_id(review_id, "review_id")
    row = await EmployeePerformanceReview.get(rid)
    if row is None or row.employee_user_id != scope.user_id:
        raise AppError(code="FORBIDDEN", message="Review access denied", status_code=403)
    if row.status != HrPerformanceReviewStatus.SELF_ASSESSMENT:
        raise AppError(code="CONFLICT", message="Self assessment not open", status_code=409)
    row.self_assessment = payload.model_dump()
    row.evidence_refs = payload.evidence_refs
    row.status = HrPerformanceReviewStatus.MANAGER_REVIEW
    row.updated_at = utcnow()
    await row.save()
    return PerformanceReviewRead.from_doc(row)


async def submit_manager_assessment(scope: AccessScope, review_id: str, payload: PerformanceManagerAssessment) -> PerformanceReviewRead:
    authorize_hr_performance_review(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rid = to_object_id(review_id, "review_id")
    row = await EmployeePerformanceReview.get(rid)
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Review not found", status_code=404)
    from app.authorization.permissions import Permission

    if (
        row.manager_user_id
        and row.manager_user_id != scope.user_id
        and Permission.HR_PERFORMANCE_MANAGE not in scope.effective_permissions
        and Permission.HR_PERFORMANCE_REVIEW not in scope.effective_permissions
    ):
        raise AppError(code="FORBIDDEN", message="Not assigned manager", status_code=403)
    if row.status != HrPerformanceReviewStatus.MANAGER_REVIEW:
        raise AppError(code="CONFLICT", message="Manager review not open", status_code=409)
    row.manager_assessment = payload.model_dump()
    row.weighted_scores = payload.weighted_scores
    row.status = HrPerformanceReviewStatus.HR_REVIEW
    row.updated_at = utcnow()
    await row.save()
    if payload.feedback:
        await EmployeePerformanceFeedback(
            tenant_id=tenant_id,
            review_id=row.id,
            author_user_id=scope.user_id,
            recipient_user_id=row.employee_user_id,
            feedback_text=payload.feedback,
            strengths=payload.strengths,
            improvement_areas=payload.improvement_areas,
            training_recommendations=payload.training_recommendations,
        ).insert()
    return PerformanceReviewRead.from_doc(row)


async def hr_review_action(scope: AccessScope, review_id: str, payload: PerformanceHrAction) -> PerformanceReviewRead:
    authorize_hr_performance_review(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rid = to_object_id(review_id, "review_id")
    row = await EmployeePerformanceReview.get(rid)
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Review not found", status_code=404)
    if row.status != HrPerformanceReviewStatus.HR_REVIEW:
        raise AppError(code="CONFLICT", message="HR review not open", status_code=409)
    if payload.action == "return":
        row.status = HrPerformanceReviewStatus.RETURNED
        row.hr_assessment = {"note": payload.note}
    else:
        row.status = HrPerformanceReviewStatus.FINALIZED
        row.overall_rating = payload.overall_rating or _compute_rating(row.weighted_scores)
        row.finalized_at = utcnow()
        row.hr_assessment = {"note": payload.note, "overall_rating": row.overall_rating}
    row.updated_at = utcnow()
    await row.save()
    return PerformanceReviewRead.from_doc(row)


def _compute_rating(scores: dict[str, str]) -> str:
    if not scores:
        return "0"
    total_w = Decimal("0")
    weighted = Decimal("0")
    for k, v in scores.items():
        weighted += Decimal(v)
        total_w += Decimal("1")
    if total_w == 0:
        return "0"
    return str((weighted / total_w).quantize(Decimal("0.01")))


async def list_reviews(scope: AccessScope, cycle_id: str | None = None, employee_user_id: str | None = None) -> list[PerformanceReviewRead]:
    authorize_hr_performance_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    filters = [Eq(EmployeePerformanceReview.tenant_id, tenant_id)]
    if cycle_id:
        filters.append(Eq(EmployeePerformanceReview.cycle_id, to_object_id(cycle_id, "cycle_id")))
    if employee_user_id:
        filters.append(Eq(EmployeePerformanceReview.employee_user_id, to_object_id(employee_user_id, "employee_user_id")))
    rows = await EmployeePerformanceReview.find(*filters).to_list()
    return [PerformanceReviewRead.from_doc(r) for r in rows]


async def create_pip(scope: AccessScope, payload: PipCreate) -> dict:
    authorize_hr_performance_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    row = EmployeePerformanceImprovementPlan(
        tenant_id=tenant_id,
        employee_user_id=to_object_id(payload.employee_user_id, "employee_user_id"),
        title=payload.title,
        improvement_areas=payload.improvement_areas,
        expectations=payload.expectations,
        action_steps=payload.action_steps,
        manager_user_id=to_object_id(payload.manager_user_id, "manager_user_id") if payload.manager_user_id else None,
        review_dates=payload.review_dates,
        status=HrPerformancePipStatus.ACTIVE,
        actor_id=scope.user_id,
    )
    await row.insert()
    return {"pip_id": str(row.id)}


async def upsert_development_plan(scope: AccessScope, payload: DevelopmentPlanUpsert) -> dict:
    authorize_hr_performance_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(payload.employee_user_id, "employee_user_id")
    doc = await EmployeeDevelopmentPlan.find_one(
        Eq(EmployeeDevelopmentPlan.tenant_id, tenant_id),
        Eq(EmployeeDevelopmentPlan.employee_user_id, uid),
        Eq(EmployeeDevelopmentPlan.status, HrDevelopmentPlanStatus.ACTIVE),
    )
    if doc:
        doc.skill_gaps = payload.skill_gaps
        doc.training_requirements = payload.training_requirements
        doc.activities = payload.activities
        doc.mentor_user_id = to_object_id(payload.mentor_user_id, "mentor_user_id") if payload.mentor_user_id else None
        doc.deadlines = payload.deadlines
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = EmployeeDevelopmentPlan(
            tenant_id=tenant_id,
            employee_user_id=uid,
            review_id=to_object_id(payload.review_id, "review_id") if payload.review_id else None,
            skill_gaps=payload.skill_gaps,
            training_requirements=payload.training_requirements,
            activities=payload.activities,
            mentor_user_id=to_object_id(payload.mentor_user_id, "mentor_user_id") if payload.mentor_user_id else None,
            deadlines=payload.deadlines,
            status=HrDevelopmentPlanStatus.ACTIVE,
            actor_id=scope.user_id,
        )
        await doc.insert()
    return {"development_plan_id": str(doc.id)}