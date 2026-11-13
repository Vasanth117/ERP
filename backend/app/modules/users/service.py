"""Create and list users inside a college."""

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.ids import to_object_id
from app.common.roles import DEPARTMENT_REQUIRED_ROLES, TENANT_REQUIRED_ROLES, Role
from app.common.schemas import Page, Pagination
from app.core.exceptions import AppError
from app.core.security import hash_password
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.auth.schemas import UserRead
from app.modules.tenants.models import Department
from app.modules.users.schemas import UserCreate
from app.repositories.tenant_repository import TenantRepository
from app.repositories.user_repository import UserRepository

_tenant_repo = TenantRepository()
_user_repo = UserRepository()


def _resolve_assignment(
    scope: AccessScope,
    payload: UserCreate,
) -> tuple[PydanticObjectId | None, PydanticObjectId | None]:
    tenant_id = to_object_id(payload.tenant_id, "tenant id") if payload.tenant_id else None
    department_id = to_object_id(payload.department_id, "department id") if payload.department_id else None

    if payload.role == Role.SUPER_ADMIN:
        authorize(scope, Permission.TENANT_USER_MANAGE)
        if scope.role != Role.SUPER_ADMIN:
            raise AppError(
                code="FORBIDDEN",
                message="You do not have permission for this action",
                status_code=403,
            )
        if tenant_id is not None or department_id is not None:
            raise AppError(
                code="VALIDATION_ERROR",
                message="Super admin accounts are not assigned to a college",
                status_code=422,
            )
        return None, None

    if payload.role not in TENANT_REQUIRED_ROLES:
        raise AppError(
            code="VALIDATION_ERROR",
            message="This role must belong to a college",
            status_code=422,
        )

    if scope.role == Role.COLLEGE_ADMIN:
        if tenant_id is not None and str(tenant_id) != str(scope.tenant_id):
            raise AppError(
                code="FORBIDDEN",
                message="You cannot access another college",
                status_code=403,
            )
        tenant_id = scope.tenant_id
    elif scope.role == Role.SUPER_ADMIN:
        if tenant_id is None:
            raise AppError(
                code="VALIDATION_ERROR",
                message="This role must belong to a college",
                status_code=422,
            )
        if scope.tenant_id is not None and str(scope.tenant_id) != str(tenant_id):
            raise AppError(
                code="VALIDATION_ERROR",
                message="Tenant does not match the selected college",
                status_code=422,
            )
    else:
        raise AppError(
            code="FORBIDDEN",
            message="You do not have permission for this action",
            status_code=403,
        )

    if payload.role in DEPARTMENT_REQUIRED_ROLES and department_id is None:
        raise AppError(
            code="VALIDATION_ERROR",
            message="This role must belong to a department",
            status_code=422,
        )
    return tenant_id, department_id


async def create_user(scope: AccessScope, payload: UserCreate) -> UserRead:
    authorize(scope, Permission.TENANT_USER_MANAGE)
    tenant_id, department_id = _resolve_assignment(scope, payload)
    email = str(payload.email).lower()

    if tenant_id is not None:
        tenant = await _tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
        if not tenant.is_active:
            raise AppError(code="TENANT_INACTIVE", message="This college is inactive", status_code=409)

    if department_id is not None:
        department = await Department.get(department_id)
        if department is None or str(department.tenant_id) != str(tenant_id):
            raise AppError(
                code="VALIDATION_ERROR",
                message="Department does not belong to this college",
                status_code=422,
            )

    existing = await _user_repo.find_by_email_in_tenant(email, tenant_id)
    if existing is not None:
        raise AppError(
            code="CONFLICT",
            message="A user with this email already exists in this college",
            status_code=409,
        )

    user = User(
        email=email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        tenant_id=tenant_id,
        department_id=department_id,
    )
    await user.insert()
    await record_audit(
        actor_id=scope.user_id,
        action="user.created",
        resource_type="user",
        resource_id=str(user.id),
        tenant_id=tenant_id,
        metadata={"email": email, "role": payload.role.value},
    )
    return UserRead.from_document(user)


async def list_users(scope: AccessScope, pagination: Pagination) -> Page[UserRead]:
    authorize(scope, Permission.TENANT_USER_READ)
    if scope.tenant_id is None and not scope.is_super_admin:
        raise AppError(
            code="TENANT_REQUIRED",
            message="College context is required",
            status_code=403,
        )

    total = await _user_repo.count_in_tenant(scope.tenant_id)
    documents = await _user_repo.list_in_tenant(
        scope.tenant_id,
        skip=pagination.offset,
        limit=pagination.limit,
    )
    return Page(
        items=[UserRead.from_document(document) for document in documents],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_user(scope: AccessScope, user_id: PydanticObjectId) -> UserRead:
    authorize(scope, Permission.TENANT_USER_READ)
    user = await _user_repo.get(user_id)
    if user is None:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    if scope.tenant_id is not None and str(user.tenant_id) != str(scope.tenant_id):
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    if scope.tenant_id is None and not scope.is_super_admin:
        raise AppError(
            code="TENANT_REQUIRED",
            message="College context is required",
            status_code=403,
        )
    return UserRead.from_document(user)
