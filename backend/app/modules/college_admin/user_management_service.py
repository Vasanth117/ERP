"""Institution user administration."""

import secrets
from datetime import timedelta, timezone

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.roles import DEPARTMENT_REQUIRED_ROLES, Role
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.security import hash_password, hash_refresh_token
from app.modules.audit.models import AuditLog
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.auth.token_service import revoke_all_for_user
from app.modules.college_admin.identity_models import (
    AccessHistoryEvent,
    InstitutionAccessHistory,
    InstitutionAccountStatus,
    InstitutionRole,
    InstitutionRoleAssignment,
    InstitutionUser,
    InstitutionUserInvitation,
    InvitationStatus,
)
from app.modules.college_admin.identity_schemas import (
    AccessHistoryRead,
    BulkUserCreate,
    InstitutionUserCreate,
    InstitutionUserInvite,
    InstitutionUserRead,
    InstitutionUserUpdate,
    InvitationAccept,
    InvitationCreateResponse,
    UserRoleAssign,
    UserRoleRevoke,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.rbac_policy import actor_may_assign_role
from app.modules.college_admin.rbac_service import seed_tenant_permission_catalog
from app.modules.faculty.models import FacultyProfile
from app.modules.students.models import StudentProfile
from app.modules.tenants.models import Department
from app.repositories.user_repository import UserRepository

_user_repo = UserRepository()


async def _append_access_history(
    *,
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId | None,
    actor_id: PydanticObjectId | None,
    event_type: AccessHistoryEvent,
    summary: str,
    metadata: dict | None = None,
) -> None:
    await InstitutionAccessHistory(
        tenant_id=tenant_id,
        user_id=user_id,
        actor_id=actor_id,
        event_type=event_type,
        summary=summary,
        metadata=metadata or {},
    ).insert()


async def _ensure_institution_user(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    campus_id: PydanticObjectId | None = None,
    department_id: PydanticObjectId | None = None,
) -> InstitutionUser:
    doc = await InstitutionUser.find_one(
        Eq(InstitutionUser.tenant_id, tenant_id),
        Eq(InstitutionUser.user_id, user_id),
    )
    if doc is not None:
        return doc
    faculty = await FacultyProfile.find_one(Eq(FacultyProfile.tenant_id, tenant_id), Eq(FacultyProfile.user_id, user_id))
    student = await StudentProfile.find_one(Eq(StudentProfile.tenant_id, tenant_id), Eq(StudentProfile.user_id, user_id))
    doc = InstitutionUser(
        tenant_id=tenant_id,
        user_id=user_id,
        campus_id=campus_id,
        department_id=department_id,
        faculty_profile_linked=faculty is not None,
        student_profile_linked=student is not None,
    )
    await doc.insert()
    return doc


async def _role_codes_for_user(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> list[str]:
    assignments = await InstitutionRoleAssignment.find(
        {"tenant_id": tenant_id, "user_id": user_id, "revoked_at": None},
    ).to_list()
    codes: list[str] = []
    for row in assignments:
        role = await InstitutionRole.get(row.institution_role_id)
        if role and role.is_active:
            codes.append(role.role_code)
    return codes


async def _validate_department(tenant_id: PydanticObjectId, department_id: PydanticObjectId | None, role: Role) -> None:
    if role in DEPARTMENT_REQUIRED_ROLES and department_id is None:
        raise AppError(code="VALIDATION_ERROR", message="This role requires a department", status_code=422)
    if department_id is None:
        return
    dept = await Department.get(department_id)
    if dept is None or dept.tenant_id != tenant_id:
        raise AppError(code="VALIDATION_ERROR", message="Department does not belong to this college", status_code=422)


async def create_institution_user(scope: AccessScope, payload: InstitutionUserCreate) -> InstitutionUserRead:
    authorize(scope, Permission.INSTITUTION_USER_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    await seed_tenant_permission_catalog(tenant_id)
    privileged = Permission.INSTITUTION_PRIVILEGED_ROLE_ASSIGN in scope.effective_permissions
    actor_may_assign_role(scope.role, payload.role, has_privileged_grant=privileged)

    department_id = to_object_id(payload.department_id, "department_id") if payload.department_id else None
    campus_id = to_object_id(payload.campus_id, "campus_id") if payload.campus_id else None
    await _validate_department(tenant_id, department_id, payload.role)

    email = str(payload.email).lower()
    if await _user_repo.find_by_email_in_tenant(email, tenant_id) is not None:
        raise AppError(code="CONFLICT", message="A user with this email already exists", status_code=409)

    user = User(
        email=email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        role=payload.role,
        tenant_id=tenant_id,
        department_id=department_id,
    )
    await user.insert()
    institution = await _ensure_institution_user(tenant_id, user.id, campus_id=campus_id, department_id=department_id)
    await _append_access_history(
        tenant_id=tenant_id,
        user_id=user.id,
        actor_id=scope.user_id,
        event_type=AccessHistoryEvent.USER_CREATED,
        summary=f"User {email} created",
        metadata={"role": payload.role.value},
    )
    await record_audit(
        actor_id=scope.user_id,
        action="institution.user.created",
        resource_type="user",
        resource_id=str(user.id),
        tenant_id=tenant_id,
        metadata={"email": email, "role": payload.role.value},
    )
    return InstitutionUserRead.from_parts(user, institution, [])


async def invite_institution_user(scope: AccessScope, payload: InstitutionUserInvite) -> InvitationCreateResponse:
    authorize(scope, Permission.INSTITUTION_USER_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    privileged = Permission.INSTITUTION_PRIVILEGED_ROLE_ASSIGN in scope.effective_permissions
    actor_may_assign_role(scope.role, payload.role, has_privileged_grant=privileged)

    department_id = to_object_id(payload.department_id, "department_id") if payload.department_id else None
    campus_id = to_object_id(payload.campus_id, "campus_id") if payload.campus_id else None
    role_id = to_object_id(payload.institution_role_id, "institution_role_id") if payload.institution_role_id else None
    await _validate_department(tenant_id, department_id, payload.role)

    email = str(payload.email).lower()
    pending = await InstitutionUserInvitation.find_one(
        Eq(InstitutionUserInvitation.tenant_id, tenant_id),
        Eq(InstitutionUserInvitation.email, email),
        Eq(InstitutionUserInvitation.status, InvitationStatus.PENDING),
    )
    if pending is not None:
        raise AppError(code="CONFLICT", message="A pending invitation already exists for this email", status_code=409)

    settings = get_settings()
    plain = secrets.token_urlsafe(48)
    invitation = InstitutionUserInvitation(
        tenant_id=tenant_id,
        email=email,
        full_name=payload.full_name.strip(),
        intended_role=payload.role,
        department_id=department_id,
        campus_id=campus_id,
        institution_role_id=role_id,
        token_hash=hash_refresh_token(plain),
        expires_at=utcnow() + timedelta(hours=settings.invitation_expire_hours),
        created_by=scope.user_id,
    )
    await invitation.insert()
    await _append_access_history(
        tenant_id=tenant_id,
        user_id=None,
        actor_id=scope.user_id,
        event_type=AccessHistoryEvent.USER_INVITED,
        summary=f"Invitation sent to {email}",
        metadata={"role": payload.role.value},
    )
    accept_token = plain if settings.app_env != "production" else None
    return InvitationCreateResponse(
        invitation_id=str(invitation.id),
        email=invitation.email,
        expires_at=invitation.expires_at,
        status=invitation.status,
        accept_token=accept_token,
    )


async def accept_institution_invitation(payload: InvitationAccept) -> InstitutionUserRead:
    token_hash = hash_refresh_token(payload.token)
    invitation = await InstitutionUserInvitation.find_one(Eq(InstitutionUserInvitation.token_hash, token_hash))
    if invitation is None or invitation.status != InvitationStatus.PENDING:
        raise AppError(code="NOT_FOUND", message="Invitation is invalid", status_code=404)
    expires_at = invitation.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= utcnow():
        invitation.status = InvitationStatus.EXPIRED
        await invitation.save()
        raise AppError(code="INVITATION_EXPIRED", message="Invitation has expired", status_code=410)

    if await _user_repo.find_by_email_in_tenant(invitation.email, invitation.tenant_id) is not None:
        raise AppError(code="CONFLICT", message="User already exists", status_code=409)

    user = User(
        email=invitation.email,
        hashed_password=hash_password(payload.password),
        full_name=invitation.full_name,
        role=invitation.intended_role,
        tenant_id=invitation.tenant_id,
        department_id=invitation.department_id,
    )
    await user.insert()
    institution = await _ensure_institution_user(
        invitation.tenant_id,
        user.id,
        campus_id=invitation.campus_id,
        department_id=invitation.department_id,
    )
    institution.account_status = InstitutionAccountStatus.ACTIVE
    await institution.save()

    if invitation.institution_role_id is not None:
        await InstitutionRoleAssignment(
            tenant_id=invitation.tenant_id,
            user_id=user.id,
            institution_role_id=invitation.institution_role_id,
            assigned_by=invitation.created_by,
        ).insert()

    invitation.status = InvitationStatus.ACCEPTED
    invitation.accepted_at = utcnow()
    await invitation.save()
    await _append_access_history(
        tenant_id=invitation.tenant_id,
        user_id=user.id,
        actor_id=None,
        event_type=AccessHistoryEvent.USER_ACTIVATED,
        summary="Invitation accepted",
    )
    codes = await _role_codes_for_user(invitation.tenant_id, user.id)
    return InstitutionUserRead.from_parts(user, institution, codes)


async def list_institution_users(scope: AccessScope, pagination: Pagination) -> Page[InstitutionUserRead]:
    authorize(scope, Permission.INSTITUTION_USER_READ)
    tenant_id = require_college_tenant_scope(scope)
    total = await _user_repo.count_in_tenant(tenant_id)
    users = await _user_repo.list_in_tenant(tenant_id, skip=pagination.offset, limit=pagination.limit)
    items: list[InstitutionUserRead] = []
    for user in users:
        institution = await _ensure_institution_user(tenant_id, user.id, department_id=user.department_id)
        codes = await _role_codes_for_user(tenant_id, user.id)
        items.append(InstitutionUserRead.from_parts(user, institution, codes))
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def get_institution_user(scope: AccessScope, user_id: PydanticObjectId) -> InstitutionUserRead:
    authorize(scope, Permission.INSTITUTION_USER_READ)
    tenant_id = require_college_tenant_scope(scope)
    user = await _user_repo.get(user_id)
    if user is None or user.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    institution = await _ensure_institution_user(tenant_id, user.id, department_id=user.department_id)
    codes = await _role_codes_for_user(tenant_id, user.id)
    return InstitutionUserRead.from_parts(user, institution, codes)


async def update_institution_user(
    scope: AccessScope,
    user_id: PydanticObjectId,
    payload: InstitutionUserUpdate,
) -> InstitutionUserRead:
    authorize(scope, Permission.INSTITUTION_USER_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    user = await _user_repo.get(user_id)
    if user is None or user.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)

    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()
    if payload.department_id is not None:
        dept_id = to_object_id(payload.department_id, "department_id")
        await _validate_department(tenant_id, dept_id, user.role)
        user.department_id = dept_id
    user.updated_at = utcnow()
    await user.save()

    institution = await _ensure_institution_user(tenant_id, user.id, department_id=user.department_id)
    if payload.campus_id is not None:
        institution.campus_id = to_object_id(payload.campus_id, "campus_id")
    institution.updated_at = utcnow()
    await institution.save()
    codes = await _role_codes_for_user(tenant_id, user.id)
    return InstitutionUserRead.from_parts(user, institution, codes)


async def activate_user(scope: AccessScope, user_id: PydanticObjectId) -> InstitutionUserRead:
    authorize(scope, Permission.INSTITUTION_USER_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    user = await _user_repo.get(user_id)
    if user is None or user.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    user.is_active = True
    user.updated_at = utcnow()
    await user.save()
    institution = await _ensure_institution_user(tenant_id, user.id)
    institution.account_status = InstitutionAccountStatus.ACTIVE
    institution.suspension_reason = None
    institution.suspended_at = None
    institution.updated_at = utcnow()
    await institution.save()
    await _append_access_history(
        tenant_id=tenant_id,
        user_id=user.id,
        actor_id=scope.user_id,
        event_type=AccessHistoryEvent.USER_ACTIVATED,
        summary="Account activated",
    )
    return await get_institution_user(scope, user_id)


async def suspend_user(scope: AccessScope, user_id: PydanticObjectId, *, reason: str | None) -> InstitutionUserRead:
    authorize(scope, Permission.INSTITUTION_USER_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    user = await _user_repo.get(user_id)
    if user is None or user.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    if user.id == scope.user_id:
        raise AppError(code="FORBIDDEN", message="You cannot suspend your own account", status_code=403)
    user.is_active = False
    user.updated_at = utcnow()
    await user.save()
    await revoke_all_for_user(user.id)
    institution = await _ensure_institution_user(tenant_id, user.id)
    institution.account_status = InstitutionAccountStatus.SUSPENDED
    institution.suspension_reason = reason
    institution.suspended_at = utcnow()
    await institution.save()
    await _append_access_history(
        tenant_id=tenant_id,
        user_id=user.id,
        actor_id=scope.user_id,
        event_type=AccessHistoryEvent.USER_SUSPENDED,
        summary="Account suspended",
        metadata={"reason": reason},
    )
    return await get_institution_user(scope, user_id)


async def deactivate_user(scope: AccessScope, user_id: PydanticObjectId) -> InstitutionUserRead:
    authorize(scope, Permission.INSTITUTION_USER_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    user = await _user_repo.get(user_id)
    if user is None or user.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    user.is_active = False
    await user.save()
    await revoke_all_for_user(user.id)
    institution = await _ensure_institution_user(tenant_id, user.id)
    institution.account_status = InstitutionAccountStatus.DEACTIVATED
    await institution.save()
    await _append_access_history(
        tenant_id=tenant_id,
        user_id=user.id,
        actor_id=scope.user_id,
        event_type=AccessHistoryEvent.USER_DEACTIVATED,
        summary="Account deactivated",
    )
    return await get_institution_user(scope, user_id)


async def assign_user_roles(scope: AccessScope, user_id: PydanticObjectId, payload: UserRoleAssign) -> InstitutionUserRead:
    authorize(scope, Permission.INSTITUTION_ROLE_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    user = await _user_repo.get(user_id)
    if user is None or user.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)

    privileged = Permission.INSTITUTION_PRIVILEGED_ROLE_ASSIGN in scope.effective_permissions
    if payload.role is not None:
        actor_may_assign_role(scope.role, payload.role, has_privileged_grant=privileged)
        user.role = payload.role
        user.updated_at = utcnow()
        await user.save()
        await _append_access_history(
            tenant_id=tenant_id,
            user_id=user.id,
            actor_id=scope.user_id,
            event_type=AccessHistoryEvent.ROLE_CHANGED,
            summary=f"Primary role set to {payload.role.value}",
        )

    if payload.institution_role_id is not None:
        role_id = to_object_id(payload.institution_role_id, "institution_role_id")
        role_doc = await InstitutionRole.get(role_id)
        if role_doc is None or role_doc.tenant_id != tenant_id:
            raise AppError(code="NOT_FOUND", message="Institution role not found", status_code=404)
        existing = await InstitutionRoleAssignment.find_one(
            {"tenant_id": tenant_id, "user_id": user.id, "institution_role_id": role_id, "revoked_at": None},
        )
        if existing is None:
            await InstitutionRoleAssignment(
                tenant_id=tenant_id,
                user_id=user.id,
                institution_role_id=role_id,
                assigned_by=scope.user_id,
            ).insert()
            await _append_access_history(
                tenant_id=tenant_id,
                user_id=user.id,
                actor_id=scope.user_id,
                event_type=AccessHistoryEvent.ROLE_ASSIGNED,
                summary=f"Custom role {role_doc.role_code} assigned",
            )
    return await get_institution_user(scope, user_id)


async def revoke_user_role(scope: AccessScope, user_id: PydanticObjectId, payload: UserRoleRevoke) -> InstitutionUserRead:
    authorize(scope, Permission.INSTITUTION_ROLE_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    role_id = to_object_id(payload.institution_role_id, "institution_role_id")
    row = await InstitutionRoleAssignment.find_one(
        {"tenant_id": tenant_id, "user_id": user_id, "institution_role_id": role_id, "revoked_at": None},
    )
    if row is None:
        raise AppError(code="NOT_FOUND", message="Role assignment not found", status_code=404)
    row.revoked_at = utcnow()
    await row.save()
    await _append_access_history(
        tenant_id=tenant_id,
        user_id=user_id,
        actor_id=scope.user_id,
        event_type=AccessHistoryEvent.ROLE_REVOKED,
        summary="Institution role revoked",
        metadata={"institution_role_id": str(role_id)},
    )
    return await get_institution_user(scope, user_id)


async def revoke_user_sessions(scope: AccessScope, user_id: PydanticObjectId) -> dict:
    authorize(scope, Permission.AUTH_SESSION_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    user = await _user_repo.get(user_id)
    if user is None or user.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    count = await revoke_all_for_user(user.id)
    await _append_access_history(
        tenant_id=tenant_id,
        user_id=user.id,
        actor_id=scope.user_id,
        event_type=AccessHistoryEvent.SESSION_REVOKED,
        summary="User sessions revoked",
        metadata={"count": count},
    )
    return {"revoked_sessions": count}


async def reset_user_access(scope: AccessScope, user_id: PydanticObjectId) -> dict:
    authorize(scope, Permission.INSTITUTION_USER_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    user = await _user_repo.get(user_id)
    if user is None or user.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    revoked = await revoke_all_for_user(user.id)
    plain = secrets.token_urlsafe(48)
    token_hash = hash_refresh_token(plain)
    settings = get_settings()
    try:
        from app.core.redis import get_redis

        redis = get_redis()
        await redis.setex(f"institution:pwd_reset:{token_hash}", 3600, str(user.id))
    except RuntimeError:
        if settings.app_env != "test":
            raise
    await _append_access_history(
        tenant_id=tenant_id,
        user_id=user.id,
        actor_id=scope.user_id,
        event_type=AccessHistoryEvent.PASSWORD_RESET,
        summary="Password reset token issued",
    )
    payload: dict = {"revoked_sessions": revoked}
    if settings.app_env != "production":
        payload["reset_token"] = plain
    return payload


async def accept_password_reset(payload: InvitationAccept) -> dict:
    token_hash = hash_refresh_token(payload.token)
    try:
        from app.core.redis import get_redis

        redis = get_redis()
        user_id_raw = await redis.get(f"institution:pwd_reset:{token_hash}")
    except RuntimeError:
        raise AppError(code="SERVICE_UNAVAILABLE", message="Reset service unavailable", status_code=503)
    if not user_id_raw:
        raise AppError(code="NOT_FOUND", message="Reset token is invalid or expired", status_code=404)
    user_id = to_object_id(user_id_raw.decode() if isinstance(user_id_raw, bytes) else user_id_raw, "user id")
    user = await _user_repo.get(user_id)
    if user is None:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    user.hashed_password = hash_password(payload.password)
    user.updated_at = utcnow()
    await user.save()
    await redis.delete(f"institution:pwd_reset:{token_hash}")
    await _append_access_history(
        tenant_id=user.tenant_id,
        user_id=user.id,
        actor_id=None,
        event_type=AccessHistoryEvent.PASSWORD_RESET,
        summary="Password reset completed",
    )
    return {"status": "ok"}


async def bulk_create_users(scope: AccessScope, payload: BulkUserCreate) -> list[InstitutionUserRead]:
    authorize(scope, Permission.INSTITUTION_USER_MANAGE)
    created: list[InstitutionUserRead] = []
    for item in payload.users:
        try:
            created.append(await create_institution_user(scope, item))
        except AppError as exc:
            if exc.code == "CONFLICT":
                continue
            raise
    return created


async def get_user_access_history(
    scope: AccessScope,
    user_id: PydanticObjectId,
    *,
    limit: int = 50,
) -> list[AccessHistoryRead]:
    authorize(scope, Permission.INSTITUTION_USER_READ)
    tenant_id = require_college_tenant_scope(scope)
    rows = await (
        InstitutionAccessHistory.find(Eq(InstitutionAccessHistory.tenant_id, tenant_id), Eq(InstitutionAccessHistory.user_id, user_id))
        .sort("-created_at")
        .limit(limit)
        .to_list()
    )
    audit_rows = await (
        AuditLog.find({"tenant_id": tenant_id, "actor_id": user_id, "action": {"$regex": "^auth\\.login"}})
        .sort("-created_at")
        .limit(limit)
        .to_list()
    )
    result = [
        AccessHistoryRead(
            event_type=row.event_type.value,
            summary=row.summary,
            user_id=str(row.user_id) if row.user_id else None,
            actor_id=str(row.actor_id) if row.actor_id else None,
            created_at=row.created_at,
            metadata=row.metadata,
        )
        for row in rows
    ]
    for audit in audit_rows:
        result.append(
            AccessHistoryRead(
                event_type=AccessHistoryEvent.LOGIN_SUCCESS.value
                if audit.action.endswith("success")
                else AccessHistoryEvent.LOGIN_FAILURE.value,
                summary=audit.action,
                user_id=str(user_id),
                actor_id=str(audit.actor_id) if audit.actor_id else None,
                created_at=audit.created_at,
                metadata=audit.metadata,
            )
        )
    result.sort(key=lambda r: r.created_at, reverse=True)
    return result[:limit]


async def record_user_login(user: User) -> None:
    if user.tenant_id is None:
        return
    institution = await InstitutionUser.find_one(
        Eq(InstitutionUser.tenant_id, user.tenant_id),
        Eq(InstitutionUser.user_id, user.id),
    )
    if institution is None:
        institution = await _ensure_institution_user(user.tenant_id, user.id, department_id=user.department_id)
    institution.last_login_at = utcnow()
    await institution.save()
