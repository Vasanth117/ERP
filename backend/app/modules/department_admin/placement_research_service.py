"""Department Admin — placement and research coordination (not institution-wide placement cell)."""

from __future__ import annotations

from collections import Counter

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.department_admin.audit_helpers import record_department_audit
from app.modules.auth.models import User
from app.modules.college_admin.student_admin_models import StudentRecord
from app.modules.department_admin.department_scope import (
    assert_faculty_visible_to_department,
    department_course_codes,
)
from app.modules.department_admin.helpdesk_constants import PLACEMENT_ACTIVITY_TYPES
from app.modules.department_admin.models import (
    DepartmentCalendarEvent,
    DepartmentInternshipCoordination,
    DepartmentInternshipStatus,
    DepartmentPlacementActivity,
    DepartmentPlacementActivityStatus,
    DepartmentProjectCoordination,
    DepartmentProjectCoordinationStatus,
    DepartmentProjectReview,
    DepartmentProjectReviewStatus,
    DepartmentResearchProject,
    DepartmentResearchProjectStatus,
    DepartmentStudentFollowUp,
)
from app.modules.department_admin.phase10_schemas import (
    InternshipCreate,
    InternshipRead,
    PlacementActivityCreate,
    PlacementActivityRead,
    PlacementOverviewRead,
    PlacementResearchReportRead,
    PlacementStudentRead,
    ProjectCoordinationRead,
    ProjectReviewCreate,
    ProjectReviewRead,
    ResearchEventRead,
    ResearchOverviewRead,
    ResearchProjectCreate,
    ResearchProjectRead,
)
from app.modules.department_admin.policy import resolve_authorized_department
from app.modules.department_admin.student_administration_service import list_students
from app.modules.department_admin.phase3_schemas import StudentDirectoryFilters
from app.modules.lms.enums import LmsAssignmentStatus
from app.modules.lms.models import CourseAssignment

PLACEMENT_ADVISORY = (
    "Institution-wide Placement Cell and official eligibility rules are not implemented. "
    "This module provides departmental coordination records only."
)

RESEARCH_ADVISORY = (
    "Publication references are not independently verified. "
    "Research approval/ethics remain with the institution's research authority."
)


def _audit_meta(central_id: PydanticObjectId) -> dict:
    return {"central_department_id": str(central_id)}


async def _assert_student(tenant_id: PydanticObjectId, central_id: PydanticObjectId, student_user_id: PydanticObjectId) -> None:
    record = await StudentRecord.find_one(
        Eq(StudentRecord.tenant_id, tenant_id),
        Eq(StudentRecord.user_id, student_user_id),
    )
    if record is None or record.department_id != central_id:
        raise AppError(code="FORBIDDEN", message="Student outside department", status_code=403)


async def placement_overview(scope: AccessScope, user: User) -> PlacementOverviewRead:
    authorize(scope, Permission.DEPARTMENT_PLACEMENT_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    students = await list_students(scope, user, Pagination(offset=0, limit=1), StudentDirectoryFilters())
    activities = await DepartmentPlacementActivity.find(
        Eq(DepartmentPlacementActivity.tenant_id, tenant_id),
        Eq(DepartmentPlacementActivity.central_department_id, central_id),
    ).count()
    scheduled = await DepartmentPlacementActivity.find(
        Eq(DepartmentPlacementActivity.tenant_id, tenant_id),
        Eq(DepartmentPlacementActivity.central_department_id, central_id),
        Eq(DepartmentPlacementActivity.status, DepartmentPlacementActivityStatus.SCHEDULED),
    ).count()
    internships = await DepartmentInternshipCoordination.find(
        Eq(DepartmentInternshipCoordination.tenant_id, tenant_id),
        Eq(DepartmentInternshipCoordination.central_department_id, central_id),
        Eq(DepartmentInternshipCoordination.status, DepartmentInternshipStatus.ACTIVE),
    ).count()
    projects = await DepartmentProjectCoordination.find(
        Eq(DepartmentProjectCoordination.tenant_id, tenant_id),
        Eq(DepartmentProjectCoordination.central_department_id, central_id),
    ).count()
    research = await DepartmentResearchProject.find(
        Eq(DepartmentResearchProject.tenant_id, tenant_id),
        Eq(DepartmentResearchProject.central_department_id, central_id),
    ).count()
    reviews = await DepartmentProjectReview.find(
        Eq(DepartmentProjectReview.tenant_id, tenant_id),
        Eq(DepartmentProjectReview.central_department_id, central_id),
        Eq(DepartmentProjectReview.status, DepartmentProjectReviewStatus.SCHEDULED),
    ).count()

    return PlacementOverviewRead(
        student_count=students.total,
        placement_activities=activities,
        scheduled_activities=scheduled,
        active_internships=internships,
        project_records=projects,
        research_projects=research,
        pending_reviews=reviews,
        advisory=PLACEMENT_ADVISORY,
        generated_at=utcnow(),
    )


async def list_placement_students(
    scope: AccessScope,
    user: User,
    pagination: Pagination,
) -> Page[PlacementStudentRead]:
    authorize(scope, Permission.DEPARTMENT_PLACEMENT_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    directory = await list_students(scope, user, pagination, StudentDirectoryFilters())
    out: list[PlacementStudentRead] = []
    for row in directory.items:
        sid = to_object_id(row.student_user_id, "student_user_id")
        follow_ups = await DepartmentStudentFollowUp.find(
            Eq(DepartmentStudentFollowUp.tenant_id, tenant_id),
            Eq(DepartmentStudentFollowUp.student_user_id, sid),
        ).count()
        internships = await DepartmentInternshipCoordination.find(
            Eq(DepartmentInternshipCoordination.tenant_id, tenant_id),
            Eq(DepartmentInternshipCoordination.student_user_id, sid),
        ).count()
        out.append(
            PlacementStudentRead(
                student_user_id=row.student_user_id,
                programme_code=row.programme_code,
                batch_label=row.batch_label,
                section_code=row.section_code,
                placement_follow_ups=follow_ups,
                internship_count=internships,
                preparation_note="Official placement readiness/eligibility not configured.",
            )
        )
    return Page(items=out, total=directory.total, limit=directory.limit, offset=directory.offset)


async def list_placement_activities(
    scope: AccessScope,
    user: User,
    pagination: Pagination,
) -> Page[PlacementActivityRead]:
    authorize(scope, Permission.DEPARTMENT_PLACEMENT_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    query = DepartmentPlacementActivity.find(
        Eq(DepartmentPlacementActivity.tenant_id, tenant_id),
        Eq(DepartmentPlacementActivity.central_department_id, central_id),
    )
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            PlacementActivityRead(
                activity_id=str(r.id),
                title=r.title,
                activity_type=r.activity_type,
                description=r.description,
                academic_year_label=r.academic_year_label,
                programme_code=r.programme_code,
                batch_label=r.batch_label,
                scheduled_at=r.scheduled_at,
                status=r.status,
                calendar_event_id=str(r.calendar_event_id) if r.calendar_event_id else None,
                coordinator_user_id=str(r.coordinator_user_id),
                participant_count=r.participant_count,
                created_at=r.created_at,
            )
            for r in rows
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def create_placement_activity(scope: AccessScope, user: User, payload: PlacementActivityCreate) -> PlacementActivityRead:
    authorize(scope, Permission.DEPARTMENT_PLACEMENT_MANAGE)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    if payload.activity_type not in PLACEMENT_ACTIVITY_TYPES:
        raise AppError(code="VALIDATION_ERROR", message="Invalid activity type", status_code=422)

    if payload.idempotency_key:
        existing = await DepartmentPlacementActivity.find_one(
            Eq(DepartmentPlacementActivity.tenant_id, tenant_id),
            Eq(DepartmentPlacementActivity.idempotency_key, payload.idempotency_key),
        )
        if existing:
            return PlacementActivityRead(
                activity_id=str(existing.id),
                title=existing.title,
                activity_type=existing.activity_type,
                description=existing.description,
                academic_year_label=existing.academic_year_label,
                programme_code=existing.programme_code,
                batch_label=existing.batch_label,
                scheduled_at=existing.scheduled_at,
                status=existing.status,
                calendar_event_id=str(existing.calendar_event_id) if existing.calendar_event_id else None,
                coordinator_user_id=str(existing.coordinator_user_id),
                participant_count=existing.participant_count,
                created_at=existing.created_at,
            )

    status = DepartmentPlacementActivityStatus.PLANNED
    if payload.scheduled_at:
        status = DepartmentPlacementActivityStatus.SCHEDULED

    doc = DepartmentPlacementActivity(
        tenant_id=tenant_id,
        central_department_id=central_id,
        title=payload.title.strip(),
        activity_type=payload.activity_type,
        description=payload.description,
        academic_year_label=payload.academic_year_label,
        programme_code=payload.programme_code.upper() if payload.programme_code else None,
        batch_label=payload.batch_label,
        scheduled_at=payload.scheduled_at,
        status=status,
        coordinator_user_id=user.id,
        participant_count=payload.participant_count,
        idempotency_key=payload.idempotency_key,
    )
    await doc.insert()
    await record_department_audit(
        actor_id=user.id,
        action="department.placement.activity_created",
        resource_type="department_placement_activity",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
        metadata=_audit_meta(central_id),
    )
    return PlacementActivityRead(
        activity_id=str(doc.id),
        title=doc.title,
        activity_type=doc.activity_type,
        description=doc.description,
        academic_year_label=doc.academic_year_label,
        programme_code=doc.programme_code,
        batch_label=doc.batch_label,
        scheduled_at=doc.scheduled_at,
        status=doc.status,
        calendar_event_id=None,
        coordinator_user_id=str(doc.coordinator_user_id),
        participant_count=doc.participant_count,
        created_at=doc.created_at,
    )


async def list_internships(scope: AccessScope, user: User, pagination: Pagination) -> Page[InternshipRead]:
    authorize(scope, Permission.DEPARTMENT_PLACEMENT_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    query = DepartmentInternshipCoordination.find(
        Eq(DepartmentInternshipCoordination.tenant_id, tenant_id),
        Eq(DepartmentInternshipCoordination.central_department_id, central_id),
    )
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            InternshipRead(
                internship_id=str(r.id),
                title=r.title,
                organization_name=r.organization_name,
                organization_website=r.organization_website,
                organization_verified=r.organization_verified,
                student_user_id=str(r.student_user_id),
                faculty_coordinator_id=str(r.faculty_coordinator_id),
                duration_label=r.duration_label,
                academic_year_label=r.academic_year_label,
                status=r.status,
                document_ids=[str(d) for d in r.document_ids],
                notes=r.notes,
                created_at=r.created_at,
            )
            for r in rows
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def create_internship(scope: AccessScope, user: User, payload: InternshipCreate) -> InternshipRead:
    authorize(scope, Permission.DEPARTMENT_PLACEMENT_MANAGE)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    if payload.idempotency_key:
        existing = await DepartmentInternshipCoordination.find_one(
            Eq(DepartmentInternshipCoordination.tenant_id, tenant_id),
            Eq(DepartmentInternshipCoordination.idempotency_key, payload.idempotency_key),
        )
        if existing:
            return InternshipRead(
                internship_id=str(existing.id),
                title=existing.title,
                organization_name=existing.organization_name,
                organization_website=existing.organization_website,
                organization_verified=existing.organization_verified,
                student_user_id=str(existing.student_user_id),
                faculty_coordinator_id=str(existing.faculty_coordinator_id),
                duration_label=existing.duration_label,
                academic_year_label=existing.academic_year_label,
                status=existing.status,
                document_ids=[str(d) for d in existing.document_ids],
                notes=existing.notes,
                created_at=existing.created_at,
            )

    student_id = to_object_id(payload.student_user_id, "student_user_id")
    faculty_id = to_object_id(payload.faculty_coordinator_id, "faculty_coordinator_id")
    await _assert_student(tenant_id, central_id, student_id)
    await assert_faculty_visible_to_department(tenant_id, central_id, faculty_id)

    doc = DepartmentInternshipCoordination(
        tenant_id=tenant_id,
        central_department_id=central_id,
        title=payload.title.strip(),
        organization_name=payload.organization_name.strip(),
        organization_website=payload.organization_website,
        organization_verified=False,
        student_user_id=student_id,
        faculty_coordinator_id=faculty_id,
        duration_label=payload.duration_label,
        academic_year_label=payload.academic_year_label,
        status=DepartmentInternshipStatus.DRAFT,
        notes=payload.notes,
        created_by=user.id,
        idempotency_key=payload.idempotency_key,
    )
    await doc.insert()
    await record_department_audit(
        actor_id=user.id,
        action="department.internship.created",
        resource_type="department_internship_coordination",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
        metadata=_audit_meta(central_id),
    )
    return InternshipRead(
        internship_id=str(doc.id),
        title=doc.title,
        organization_name=doc.organization_name,
        organization_website=doc.organization_website,
        organization_verified=False,
        student_user_id=str(doc.student_user_id),
        faculty_coordinator_id=str(doc.faculty_coordinator_id),
        duration_label=doc.duration_label,
        academic_year_label=doc.academic_year_label,
        status=doc.status,
        document_ids=[],
        notes=doc.notes,
        created_at=doc.created_at,
    )


async def _lms_capstone_rows(tenant_id: PydanticObjectId, central_id: PydanticObjectId) -> list[ProjectCoordinationRead]:
    course_codes = list(await department_course_codes(tenant_id, central_id))
    if not course_codes:
        return []
    assignments = await CourseAssignment.find(
        Eq(CourseAssignment.tenant_id, tenant_id),
        In(CourseAssignment.course_code, course_codes),
        In(CourseAssignment.status, [LmsAssignmentStatus.PUBLISHED]),
    ).to_list()
    reads: list[ProjectCoordinationRead] = []
    for a in assignments:
        reads.append(
            ProjectCoordinationRead(
                project_id=f"lms:{a.id}",
                title=a.title,
                project_type="lms_assignment",
                student_user_ids=[],
                faculty_guide_id=str(a.faculty_user_id),
                lms_assignment_id=str(a.id),
                academic_year_label=None,
                programme_code=None,
                milestones=[],
                status=DepartmentProjectCoordinationStatus.IN_PROGRESS,
                submission_status=a.status.value,
                source="lms_course_assignment",
            )
        )
    return reads


async def list_projects(scope: AccessScope, user: User, pagination: Pagination) -> Page[ProjectCoordinationRead]:
    authorize(scope, Permission.DEPARTMENT_RESEARCH_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    local = await DepartmentProjectCoordination.find(
        Eq(DepartmentProjectCoordination.tenant_id, tenant_id),
        Eq(DepartmentProjectCoordination.central_department_id, central_id),
    ).sort("-created_at").to_list()
    items = [
        ProjectCoordinationRead(
            project_id=str(r.id),
            title=r.title,
            project_type=r.project_type,
            student_user_ids=[str(s) for s in r.student_user_ids],
            faculty_guide_id=str(r.faculty_guide_id),
            lms_assignment_id=str(r.lms_assignment_id) if r.lms_assignment_id else None,
            academic_year_label=r.academic_year_label,
            programme_code=r.programme_code,
            milestones=r.milestones,
            status=r.status,
            submission_status=r.submission_status,
            source="department_project_coordination",
        )
        for r in local
    ]
    items.extend(await _lms_capstone_rows(tenant_id, central_id))
    total = len(items)
    page = items[pagination.offset : pagination.offset + pagination.limit]
    return Page(items=page, total=total, limit=pagination.limit, offset=pagination.offset)


async def get_project(scope: AccessScope, user: User, project_id: str) -> ProjectCoordinationRead:
    authorize(scope, Permission.DEPARTMENT_RESEARCH_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    if project_id.startswith("lms:"):
        lms_id = to_object_id(project_id.removeprefix("lms:"), "project_id")
        assignment = await CourseAssignment.get(lms_id)
        if assignment is None or assignment.tenant_id != tenant_id:
            raise AppError(code="NOT_FOUND", message="Project not found", status_code=404)
        return ProjectCoordinationRead(
            project_id=project_id,
            title=assignment.title,
            project_type="lms_assignment",
            student_user_ids=[],
            faculty_guide_id=str(assignment.faculty_user_id),
            lms_assignment_id=str(assignment.id),
            academic_year_label=None,
            programme_code=None,
            milestones=[],
            status=DepartmentProjectCoordinationStatus.IN_PROGRESS,
            submission_status=assignment.status.value,
            source="lms_course_assignment",
        )

    doc = await DepartmentProjectCoordination.get(to_object_id(project_id, "project_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Project not found", status_code=404)
    return ProjectCoordinationRead(
        project_id=str(doc.id),
        title=doc.title,
        project_type=doc.project_type,
        student_user_ids=[str(s) for s in doc.student_user_ids],
        faculty_guide_id=str(doc.faculty_guide_id),
        lms_assignment_id=str(doc.lms_assignment_id) if doc.lms_assignment_id else None,
        academic_year_label=doc.academic_year_label,
        programme_code=doc.programme_code,
        milestones=doc.milestones,
        status=doc.status,
        submission_status=doc.submission_status,
        source="department_project_coordination",
    )


async def schedule_project_review(
    scope: AccessScope,
    user: User,
    project_id: str,
    payload: ProjectReviewCreate,
) -> ProjectReviewRead:
    authorize(scope, Permission.DEPARTMENT_RESEARCH_MANAGE)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    if project_id.startswith("lms:"):
        raise AppError(
            code="VALIDATION_ERROR",
            message="Create a department project coordination record before scheduling reviews for LMS assignments",
            status_code=422,
        )

    project = await DepartmentProjectCoordination.get(to_object_id(project_id, "project_id"))
    if project is None or project.tenant_id != tenant_id or project.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Project not found", status_code=404)

    reviewer_ids: list[PydanticObjectId] = []
    for raw in payload.reviewer_faculty_ids:
        rid = to_object_id(raw, "reviewer_faculty_id")
        await assert_faculty_visible_to_department(tenant_id, central_id, rid)
        reviewer_ids.append(rid)

    review = DepartmentProjectReview(
        tenant_id=tenant_id,
        central_department_id=central_id,
        project_id=project.id,
        review_type=payload.review_type,
        milestone_label=payload.milestone_label,
        scheduled_at=payload.scheduled_at,
        reviewer_faculty_ids=reviewer_ids,
        feedback_ref=payload.feedback_ref,
        created_by=user.id,
    )
    await review.insert()
    project.status = DepartmentProjectCoordinationStatus.UNDER_REVIEW
    project.updated_at = utcnow()
    await project.save()
    await record_department_audit(
        actor_id=user.id,
        action="department.project.review_scheduled",
        resource_type="department_project_review",
        resource_id=str(review.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
        metadata=_audit_meta(central_id),
    )
    return ProjectReviewRead(
        review_id=str(review.id),
        project_id=str(project.id),
        review_type=review.review_type,
        milestone_label=review.milestone_label,
        scheduled_at=review.scheduled_at,
        reviewer_faculty_ids=[str(r) for r in review.reviewer_faculty_ids],
        status=review.status,
        feedback_ref=review.feedback_ref,
        calendar_event_id=str(review.calendar_event_id) if review.calendar_event_id else None,
    )


async def research_overview(scope: AccessScope, user: User) -> ResearchOverviewRead:
    authorize(scope, Permission.DEPARTMENT_RESEARCH_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    rows = await DepartmentResearchProject.find(
        Eq(DepartmentResearchProject.tenant_id, tenant_id),
        Eq(DepartmentResearchProject.central_department_id, central_id),
    ).to_list()
    active = sum(1 for r in rows if r.status == DepartmentResearchProjectStatus.ACTIVE)
    completed = sum(1 for r in rows if r.status == DepartmentResearchProjectStatus.COMPLETED)
    faculty_leads = len({r.faculty_lead_id for r in rows})
    students = len({sid for r in rows for sid in r.student_participant_ids})
    upcoming = sum(1 for r in rows if r.seminar_scheduled_at and r.seminar_scheduled_at >= utcnow())
    return ResearchOverviewRead(
        active_projects=active,
        completed_projects=completed,
        faculty_leads=faculty_leads,
        student_participants=students,
        upcoming_seminars=upcoming,
        advisory=RESEARCH_ADVISORY,
        generated_at=utcnow(),
    )


async def list_research_projects(
    scope: AccessScope,
    user: User,
    pagination: Pagination,
) -> Page[ResearchProjectRead]:
    authorize(scope, Permission.DEPARTMENT_RESEARCH_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    query = DepartmentResearchProject.find(
        Eq(DepartmentResearchProject.tenant_id, tenant_id),
        Eq(DepartmentResearchProject.central_department_id, central_id),
    )
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            ResearchProjectRead(
                project_id=str(r.id),
                title=r.title,
                faculty_lead_id=str(r.faculty_lead_id),
                student_participant_ids=[str(s) for s in r.student_participant_ids],
                status=r.status,
                publication_refs=r.publication_refs,
                seminar_scheduled_at=r.seminar_scheduled_at,
                academic_year_label=r.academic_year_label,
                notes=r.notes,
                created_at=r.created_at,
            )
            for r in rows
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def create_research_project(scope: AccessScope, user: User, payload: ResearchProjectCreate) -> ResearchProjectRead:
    authorize(scope, Permission.DEPARTMENT_RESEARCH_MANAGE)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    faculty_id = to_object_id(payload.faculty_lead_id, "faculty_lead_id")
    await assert_faculty_visible_to_department(tenant_id, central_id, faculty_id)
    student_ids: list[PydanticObjectId] = []
    for raw in payload.student_participant_ids:
        sid = to_object_id(raw, "student_participant_id")
        await _assert_student(tenant_id, central_id, sid)
        student_ids.append(sid)

    doc = DepartmentResearchProject(
        tenant_id=tenant_id,
        central_department_id=central_id,
        title=payload.title.strip(),
        faculty_lead_id=faculty_id,
        student_participant_ids=student_ids,
        academic_year_label=payload.academic_year_label,
        publication_refs=payload.publication_refs,
        seminar_scheduled_at=payload.seminar_scheduled_at,
        notes=payload.notes,
        created_by=user.id,
    )
    await doc.insert()
    await record_department_audit(
        actor_id=user.id,
        action="department.research.project_created",
        resource_type="department_research_project",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
        metadata=_audit_meta(central_id),
    )
    return ResearchProjectRead(
        project_id=str(doc.id),
        title=doc.title,
        faculty_lead_id=str(doc.faculty_lead_id),
        student_participant_ids=[str(s) for s in doc.student_participant_ids],
        status=doc.status,
        publication_refs=doc.publication_refs,
        seminar_scheduled_at=doc.seminar_scheduled_at,
        academic_year_label=doc.academic_year_label,
        notes=doc.notes,
        created_at=doc.created_at,
    )


async def list_research_events(
    scope: AccessScope,
    user: User,
    pagination: Pagination,
) -> Page[ResearchEventRead]:
    authorize(scope, Permission.DEPARTMENT_RESEARCH_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    query = DepartmentCalendarEvent.find(
        Eq(DepartmentCalendarEvent.tenant_id, tenant_id),
        Eq(DepartmentCalendarEvent.central_department_id, central_id),
    )
    rows = await query.sort("+starts_at").to_list()
    filtered = [r for r in rows if r.category in {"seminar", "workshop", "project_review"}]
    total = len(filtered)
    page = filtered[pagination.offset : pagination.offset + pagination.limit]
    return Page(
        items=[
            ResearchEventRead(
                event_id=str(r.id),
                title=r.title,
                category=r.category,
                starts_at=r.starts_at,
                ends_at=r.ends_at,
                status=r.status.value,
            )
            for r in page
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def placement_research_report(scope: AccessScope, user: User) -> PlacementResearchReportRead:
    authorize(scope, Permission.DEPARTMENT_PLACEMENT_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    activities = await DepartmentPlacementActivity.find(
        Eq(DepartmentPlacementActivity.tenant_id, tenant_id),
        Eq(DepartmentPlacementActivity.central_department_id, central_id),
    ).count()
    internships = await DepartmentInternshipCoordination.find(
        Eq(DepartmentInternshipCoordination.tenant_id, tenant_id),
        Eq(DepartmentInternshipCoordination.central_department_id, central_id),
    ).to_list()
    projects = await DepartmentProjectCoordination.find(
        Eq(DepartmentProjectCoordination.tenant_id, tenant_id),
        Eq(DepartmentProjectCoordination.central_department_id, central_id),
    ).to_list()
    research = await DepartmentResearchProject.find(
        Eq(DepartmentResearchProject.tenant_id, tenant_id),
        Eq(DepartmentResearchProject.central_department_id, central_id),
    ).to_list()
    reviews = await DepartmentProjectReview.find(
        Eq(DepartmentProjectReview.tenant_id, tenant_id),
        Eq(DepartmentProjectReview.central_department_id, central_id),
        Eq(DepartmentProjectReview.status, DepartmentProjectReviewStatus.SCHEDULED),
    ).count()
    lms_count = len(await _lms_capstone_rows(tenant_id, central_id))

    return PlacementResearchReportRead(
        placement_activities=activities,
        internships_by_status=dict(Counter(i.status.value for i in internships)),
        projects_by_status=dict(Counter(p.status.value for p in projects)),
        research_by_status=dict(Counter(r.status.value for r in research)),
        reviews_pending=reviews,
        lms_capstone_assignments=lms_count,
        generated_at=utcnow(),
        advisory=f"{PLACEMENT_ADVISORY} {RESEARCH_ADVISORY}",
    )