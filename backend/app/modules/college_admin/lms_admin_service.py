"""LMS administration — institutional config and operational monitors."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.lms_admin_models import (
    InstitutionLmsSettings,
    LmsConfigurationHistory,
    LmsContentCategory,
    LmsCourseMapping,
    LmsPublishingPolicy,
)
from app.modules.college_admin.lms_admin_schemas import (
    LmsConfigurationHistoryItem,
    LmsContentCategoryRead,
    LmsContentCategoryUpsert,
    LmsCourseMappingRead,
    LmsCourseMappingUpsert,
    LmsMonitorSummary,
    LmsOperationalStats,
    LmsPublishingPolicyRead,
    LmsPublishingPolicyUpsert,
    LmsSettingsRead,
    LmsSettingsUpdate,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.lms.enums import LmsAssignmentStatus, MaterialPublishState, SubmissionStatus
from app.modules.lms.models import AssignmentRule, AssignmentSubmission, CourseAssignment, LearningMaterial
from app.modules.students.student_lms_models import StudentLearningProgress

_reader = OperationalDataReader()


async def _get_settings_doc(tenant_id: PydanticObjectId) -> InstitutionLmsSettings:
    doc = await InstitutionLmsSettings.find_one(
        Eq(InstitutionLmsSettings.tenant_id, tenant_id),
        Eq(InstitutionLmsSettings.settings_id, "default"),
    )
    if doc is None:
        doc = InstitutionLmsSettings(tenant_id=tenant_id)
        await doc.insert()
    return doc


async def _append_history(
    tenant_id: PydanticObjectId,
    *,
    scope: str,
    resource_id: str,
    version_number: int,
    snapshot: dict,
    actor_id: PydanticObjectId | None,
) -> None:
    await LmsConfigurationHistory(
        tenant_id=tenant_id,
        scope=scope,
        resource_id=resource_id,
        version_number=version_number,
        snapshot=snapshot,
        actor_id=actor_id,
    ).insert()


def _settings_read(doc: InstitutionLmsSettings) -> LmsSettingsRead:
    return LmsSettingsRead(
        default_access=doc.default_access,
        allowed_material_types=list(doc.allowed_material_types),
        assignment_late_penalty_cap=doc.assignment_late_penalty_cap,
        quiz_enabled=doc.quiz_enabled,
        moderation_required=doc.moderation_required,
        integration_provider_code=doc.integration_provider_code,
        version=doc.version,
        updated_at=doc.updated_at,
    )


async def get_lms_settings(scope: AccessScope) -> LmsSettingsRead:
    authorize(scope, Permission.LMS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    return _settings_read(await _get_settings_doc(tenant_id))


async def update_lms_settings(scope: AccessScope, user: User, payload: LmsSettingsUpdate) -> LmsSettingsRead:
    authorize(scope, Permission.LMS_ADMIN_CONFIG)
    tenant_id = require_college_tenant_scope(scope)
    doc = await _get_settings_doc(tenant_id)
    prev = doc.model_dump(mode="json")
    changed = payload.model_dump(exclude_unset=True)
    if not changed:
        return _settings_read(doc)
    for key, value in changed.items():
        setattr(doc, key, value)
    doc.version += 1
    doc.updated_by = user.id
    doc.updated_at = utcnow()
    await doc.save()
    await _append_history(
        tenant_id,
        scope="lms_settings",
        resource_id="default",
        version_number=doc.version,
        snapshot=prev,
        actor_id=user.id,
    )
    return _settings_read(doc)


async def upsert_course_mapping(scope: AccessScope, user: User, payload: LmsCourseMappingUpsert) -> LmsCourseMappingRead:
    authorize(scope, Permission.LMS_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    dept = to_object_id(payload.department_id, "department_id") if payload.department_id else None
    doc = await LmsCourseMapping.find_one(
        Eq(LmsCourseMapping.tenant_id, tenant_id),
        Eq(LmsCourseMapping.course_code, payload.course_code.strip().upper()),
    )
    if doc is None:
        doc = LmsCourseMapping(
            tenant_id=tenant_id,
            course_id=payload.course_id,
            course_code=payload.course_code.strip().upper(),
            lms_course_key=payload.lms_course_key,
            department_id=dept,
            published=payload.published,
            actor_id=user.id,
        )
        await doc.insert()
    else:
        prev = doc.model_dump(mode="json")
        doc.course_id = payload.course_id
        doc.lms_course_key = payload.lms_course_key
        doc.department_id = dept
        doc.published = payload.published
        doc.actor_id = user.id
        doc.updated_at = utcnow()
        await doc.save()
        await _append_history(
            tenant_id,
            scope="course_mapping",
            resource_id=doc.course_code,
            version_number=1,
            snapshot=prev,
            actor_id=user.id,
        )
    return LmsCourseMappingRead(
        course_code=doc.course_code,
        course_id=doc.course_id,
        lms_course_key=doc.lms_course_key,
        department_id=str(doc.department_id) if doc.department_id else None,
        published=doc.published,
        updated_at=doc.updated_at,
    )


async def list_course_mappings(scope: AccessScope) -> list[LmsCourseMappingRead]:
    authorize(scope, Permission.LMS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    docs = await LmsCourseMapping.find(Eq(LmsCourseMapping.tenant_id, tenant_id)).to_list()
    return [
        LmsCourseMappingRead(
            course_code=d.course_code,
            course_id=d.course_id,
            lms_course_key=d.lms_course_key,
            department_id=str(d.department_id) if d.department_id else None,
            published=d.published,
            updated_at=d.updated_at,
        )
        for d in docs
    ]


async def upsert_content_category(scope: AccessScope, payload: LmsContentCategoryUpsert) -> LmsContentCategoryRead:
    authorize(scope, Permission.LMS_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    code = payload.category_code.strip().lower()
    doc = await LmsContentCategory.find_one(
        Eq(LmsContentCategory.tenant_id, tenant_id),
        Eq(LmsContentCategory.category_code, code),
    )
    if doc is None:
        doc = LmsContentCategory(
            tenant_id=tenant_id,
            category_code=code,
            title=payload.title,
            parent_code=payload.parent_code,
            sort_order=payload.sort_order,
        )
        await doc.insert()
    else:
        doc.title = payload.title
        doc.parent_code = payload.parent_code
        doc.sort_order = payload.sort_order
        doc.updated_at = utcnow()
        await doc.save()
    return LmsContentCategoryRead(
        category_code=doc.category_code,
        title=doc.title,
        parent_code=doc.parent_code,
        sort_order=doc.sort_order,
    )


async def list_content_categories(scope: AccessScope) -> list[LmsContentCategoryRead]:
    authorize(scope, Permission.LMS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    docs = await LmsContentCategory.find(Eq(LmsContentCategory.tenant_id, tenant_id)).sort("+sort_order").to_list()
    return [
        LmsContentCategoryRead(
            category_code=d.category_code,
            title=d.title,
            parent_code=d.parent_code,
            sort_order=d.sort_order,
        )
        for d in docs
    ]


async def upsert_publishing_policy(
    scope: AccessScope,
    user: User,
    payload: LmsPublishingPolicyUpsert,
) -> LmsPublishingPolicyRead:
    authorize(scope, Permission.LMS_ADMIN_CONFIG)
    tenant_id = require_college_tenant_scope(scope)
    code = payload.policy_code.strip().lower()
    doc = await LmsPublishingPolicy.find_one(
        Eq(LmsPublishingPolicy.tenant_id, tenant_id),
        Eq(LmsPublishingPolicy.policy_code, code),
    )
    rules_extra = {}
    if doc is None:
        doc = LmsPublishingPolicy(
            tenant_id=tenant_id,
            policy_code=code,
            material_requires_approval=payload.material_requires_approval,
            assignment_publish_window_hours=payload.assignment_publish_window_hours,
            updated_by=user.id,
        )
        await doc.insert()
    else:
        prev = doc.model_dump(mode="json")
        doc.material_requires_approval = payload.material_requires_approval
        doc.assignment_publish_window_hours = payload.assignment_publish_window_hours
        doc.version += 1
        doc.updated_by = user.id
        doc.updated_at = utcnow()
        await doc.save()
        await _append_history(
            tenant_id,
            scope="publishing_policy",
            resource_id=code,
            version_number=doc.version,
            snapshot=prev,
            actor_id=user.id,
        )
    rule = await AssignmentRule.find_one(Eq(AssignmentRule.tenant_id, tenant_id))
    if rule is None:
        rule = AssignmentRule(tenant_id=tenant_id)
    if payload.allowed_extensions is not None:
        rule.allowed_extensions = payload.allowed_extensions
    if payload.max_file_size_bytes is not None:
        rule.max_file_size_bytes = payload.max_file_size_bytes
    if payload.late_submission_allowed is not None:
        rule.late_submission_allowed = payload.late_submission_allowed
    if payload.late_penalty_percent is not None:
        cap = (await _get_settings_doc(tenant_id)).assignment_late_penalty_cap
        rule.late_penalty_percent = min(payload.late_penalty_percent, cap)
    if rule.id:
        await rule.save()
    else:
        await rule.insert()
    doc.rules = {
        "assignment_rule_id": str(rule.id),
        **rules_extra,
    }
    await doc.save()
    return LmsPublishingPolicyRead(
        policy_code=doc.policy_code,
        material_requires_approval=doc.material_requires_approval,
        assignment_publish_window_hours=doc.assignment_publish_window_hours,
        version=doc.version,
        updated_at=doc.updated_at,
    )


async def get_lms_operational_stats(scope: AccessScope) -> LmsOperationalStats:
    authorize(scope, Permission.LMS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    mats = await LearningMaterial.find(Eq(LearningMaterial.tenant_id, tenant_id)).to_list()
    published = sum(1 for m in mats if m.publish_state == MaterialPublishState.PUBLISHED)
    draft = sum(1 for m in mats if m.publish_state == MaterialPublishState.DRAFT)
    assigns = await CourseAssignment.find(Eq(CourseAssignment.tenant_id, tenant_id)).to_list()
    pub_assign = sum(1 for a in assigns if a.status == LmsAssignmentStatus.PUBLISHED)
    subs = await AssignmentSubmission.find(Eq(AssignmentSubmission.tenant_id, tenant_id)).count()
    learners = await StudentLearningProgress.find(Eq(StudentLearningProgress.tenant_id, tenant_id)).count()
    mappings = await LmsCourseMapping.find(Eq(LmsCourseMapping.tenant_id, tenant_id)).count()
    return LmsOperationalStats(
        materials_total=len(mats),
        materials_published=published,
        materials_draft=draft,
        assignments_total=len(assigns),
        assignments_published=pub_assign,
        submissions_total=subs,
        active_learners=learners,
        course_mappings=mappings,
    )


async def get_lms_monitor_summary(scope: AccessScope) -> LmsMonitorSummary:
    authorize(scope, Permission.LMS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    mats = await LearningMaterial.find(Eq(LearningMaterial.tenant_id, tenant_id)).to_list()
    content = {
        MaterialPublishState.PUBLISHED.value: sum(1 for m in mats if m.publish_state == MaterialPublishState.PUBLISHED),
        MaterialPublishState.DRAFT.value: sum(1 for m in mats if m.publish_state == MaterialPublishState.DRAFT),
    }
    assigns = await CourseAssignment.find(Eq(CourseAssignment.tenant_id, tenant_id)).to_list()
    publication = {s.value: sum(1 for a in assigns if a.status == s) for s in LmsAssignmentStatus}
    subs = await AssignmentSubmission.find(Eq(AssignmentSubmission.tenant_id, tenant_id)).to_list()
    submission = {
        SubmissionStatus.SUBMITTED.value: sum(1 for s in subs if s.status == SubmissionStatus.SUBMITTED),
        SubmissionStatus.LATE.value: sum(1 for s in subs if s.status == SubmissionStatus.LATE),
        SubmissionStatus.EVALUATED.value: sum(1 for s in subs if s.status == SubmissionStatus.EVALUATED),
        SubmissionStatus.MISSING.value: sum(1 for s in subs if s.status == SubmissionStatus.MISSING),
    }
    progress = await StudentLearningProgress.find(Eq(StudentLearningProgress.tenant_id, tenant_id)).to_list()
    learning = {
        "tracked_courses": len(progress),
        "materials_viewed": sum(p.materials_viewed for p in progress),
        "assignments_submitted": sum(p.assignments_submitted for p in progress),
        "quizzes_completed": sum(p.quizzes_completed for p in progress),
    }
    return LmsMonitorSummary(
        content_availability=content,
        assignment_publication=publication,
        submission_activity=submission,
        learning_progress=learning,
    )


async def list_lms_configuration_history(scope: AccessScope, *, limit: int = 50) -> list[LmsConfigurationHistoryItem]:
    authorize(scope, Permission.LMS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    docs = (
        await LmsConfigurationHistory.find(Eq(LmsConfigurationHistory.tenant_id, tenant_id))
        .sort("-created_at")
        .limit(limit)
        .to_list()
    )
    return [
        LmsConfigurationHistoryItem(
            scope=d.scope,
            resource_id=d.resource_id,
            version_number=d.version_number,
            created_at=d.created_at,
            actor_id=str(d.actor_id) if d.actor_id else None,
        )
        for d in docs
    ]


async def get_lms_integration_status(scope: AccessScope) -> dict:
    authorize(scope, Permission.LMS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    settings = await _get_settings_doc(tenant_id)
    health = await _reader.integration_health(tenant_id)
    return {
        "integration_provider_code": settings.integration_provider_code,
        "integration_health": health,
    }