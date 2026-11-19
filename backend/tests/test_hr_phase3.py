"""HR staff portal phase 3 — recruitment and onboarding."""

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import permissions_for_role
from app.common.ids import to_object_id
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.models import InstitutionCampus
from app.modules.hr.enums import (
    HrApplicationPipelineStage,
    HrOnboardingProcessStatus,
    HrOnboardingTaskStatus,
)
from app.modules.hr.onboarding_schemas import OnboardingInitiate, OnboardingTaskUpdate, OnboardingTemplateUpsert
from app.modules.hr.onboarding_service import (
    complete_onboarding,
    compute_onboarding_progress,
    initiate_onboarding,
    update_onboarding_task,
    upsert_onboarding_template,
)
from app.modules.hr.recruitment_schemas import (
    ApplicationCreate,
    ApplicationStageTransition,
    CandidateUpsert,
    InterviewSchedule,
    JobOpeningCreate,
    JobRequisitionCreate,
    OfferCreate,
    OfferDecision,
    RequisitionDecision,
)
from app.modules.hr.recruitment_service import (
    create_application,
    create_job_opening,
    create_job_requisition,
    create_offer,
    decide_offer,
    review_job_requisition,
    schedule_interview,
    set_job_opening_status,
    submit_job_requisition,
    transition_application_stage,
    upsert_candidate,
)
from app.modules.hr.enums import HrJobOpeningStatus
from app.modules.tenants.models import Department, Tenant


@pytest.fixture
async def db_ready():
    try:
        await connect_to_mongo()
    except Exception as exc:
        pytest.skip(f"MongoDB not available: {exc}")
    for model in document_models():
        await model.get_motor_collection().delete_many({})
    yield
    await close_mongo()


def _scope(user: User, role: Role) -> AccessScope:
    return AccessScope(
        role=role,
        user_id=user.id,
        tenant_id=user.tenant_id,
        department_id=None,
        effective_permissions=permissions_for_role(role),
    )


async def _seed(suffix: str):
    tenant = Tenant(name=f"HR3 {suffix}", code=f"hr3_{suffix}")
    await tenant.insert()
    dept = Department(tenant_id=tenant.id, name="Sciences", code=f"SCI-{suffix}")
    await dept.insert()
    campus = InstitutionCampus(tenant_id=tenant.id, campus_code=f"C{suffix}", name="Main", is_main=True)
    await campus.insert()
    hr_user = User(
        email=f"hr3+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="HR Staff",
        role=Role.HR_STAFF,
        tenant_id=tenant.id,
    )
    await hr_user.insert()
    scope = _scope(hr_user, Role.HR_STAFF)
    return tenant, hr_user, scope, dept, campus


@pytest.mark.asyncio
async def test_recruitment_to_onboarding_happy_path(db_ready):
    suffix = uuid4().hex[:8]
    _, _, scope, dept, _ = await _seed(suffix)

    req = await create_job_requisition(
        scope,
        JobRequisitionCreate(
            requisition_code=f"REQ-{suffix}",
            job_title="Lab Assistant",
            department_id=str(dept.id),
            employment_type="full_time",
            job_description="Support laboratory operations",
            reason_for_hiring="Expansion",
            positions_required=1,
        ),
    )
    await submit_job_requisition(scope, req.id)
    await review_job_requisition(scope, req.id, RequisitionDecision(decision="hr_approve", note="OK"))
    approved = await review_job_requisition(scope, req.id, RequisitionDecision(decision="approve", note="Management OK"))
    assert approved.status.value == "approved"

    opening = await create_job_opening(
        scope,
        JobOpeningCreate(
            opening_code=f"OPEN-{suffix}",
            requisition_id=req.id,
            vacancies=1,
            interview_stages=["technical", "hr"],
        ),
    )
    published = await set_job_opening_status(scope, opening.id, HrJobOpeningStatus.PUBLISHED)
    assert published.status == HrJobOpeningStatus.PUBLISHED

    candidate = await upsert_candidate(
        scope,
        CandidateUpsert(full_name="Alex Candidate", email=f"alex+{suffix}@example.com", phone="9000000001"),
    )
    application = await create_application(
        scope,
        ApplicationCreate(job_opening_id=opening.id, candidate_id=candidate.id),
    )
    await transition_application_stage(
        scope,
        application.id,
        ApplicationStageTransition(target_stage=HrApplicationPipelineStage.UNDER_REVIEW),
    )
    await transition_application_stage(
        scope,
        application.id,
        ApplicationStageTransition(target_stage=HrApplicationPipelineStage.SHORTLISTED),
    )
    interview_at = datetime.now(timezone.utc) + timedelta(days=3)
    await schedule_interview(
        scope,
        InterviewSchedule(
            application_id=application.id,
            scheduled_at=interview_at,
            mode="online",
            location_or_meeting="https://meet.example/recruit",
            interviewer_ids=[str(scope.user_id)],
        ),
    )
    await transition_application_stage(
        scope,
        application.id,
        ApplicationStageTransition(target_stage=HrApplicationPipelineStage.INTERVIEW_COMPLETED),
    )
    await transition_application_stage(
        scope,
        application.id,
        ApplicationStageTransition(target_stage=HrApplicationPipelineStage.SELECTED),
    )

    offer = await create_offer(
        scope,
        OfferCreate(
            application_id=application.id,
            designation="Lab Assistant",
            department_id=str(dept.id),
            employment_type="full_time",
            expected_joining_date=date.today() + timedelta(days=14),
        ),
    )
    offer = await decide_offer(scope, offer.id, OfferDecision(decision="approve"))
    offer = await decide_offer(scope, offer.id, OfferDecision(decision="issue"))
    offer = await decide_offer(scope, offer.id, OfferDecision(decision="accept"))
    assert offer.status.value == "accepted"

    template = await upsert_onboarding_template(
        scope,
        OnboardingTemplateUpsert(
            template_code=f"TPL-{suffix}",
            title="Staff onboarding",
            employee_category="staff",
            tasks=[
                {"task_key": "hr_verify_id", "title": "Verify ID", "responsible_role": "hr", "mandatory": True, "due_days": 3},
                {"task_key": "employee_forms", "title": "Joining forms", "responsible_role": "employee", "mandatory": True, "due_days": 5},
            ],
        ),
    )
    process = await initiate_onboarding(
        scope,
        OnboardingInitiate(
            offer_id=offer.id,
            template_id=template.id,
            department_id=str(dept.id),
            designation="Lab Assistant",
            employee_code=f"EMP-{suffix}",
            joining_date=date.today() + timedelta(days=14),
        ),
    )
    assert process.employee_user_id is not None

    from app.modules.hr.onboarding_models import HrOnboardingTask

    tasks = await HrOnboardingTask.find(Eq(HrOnboardingTask.process_id, to_object_id(process.id, "process_id"))).to_list()
    for task in tasks:
        await update_onboarding_task(
            scope,
            str(task.id),
            OnboardingTaskUpdate(status=HrOnboardingTaskStatus.COMPLETED),
        )

    progress = await compute_onboarding_progress(scope, process.id)
    assert progress.overall_percent == 100.0

    done = await complete_onboarding(scope, process.id)
    assert done.status == HrOnboardingProcessStatus.COMPLETED

    with pytest.raises(AppError):
        await create_application(
            scope,
            ApplicationCreate(job_opening_id=opening.id, candidate_id=candidate.id),
        )


@pytest.mark.asyncio
async def test_duplicate_candidate_email_reuses_record(db_ready):
    suffix = uuid4().hex[:8]
    _, _, scope, _, _ = await _seed(suffix)
    email = f"dup+{suffix}@example.com"
    first = await upsert_candidate(scope, CandidateUpsert(full_name="One", email=email))
    second = await upsert_candidate(scope, CandidateUpsert(full_name="One Updated", email=email))
    assert first.id == second.id
    assert second.full_name == "One Updated"