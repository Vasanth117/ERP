"""Create and list users inside a college."""

from beanie import PydanticObjectId
from fastapi import HTTPException, status

from app.api.deps import AccessScope
from app.common.ids import to_object_id
from app.common.roles import DEPARTMENT_REQUIRED_ROLES, TENANT_REQUIRED_ROLES, Role
from app.common.schemas import Page, Pagination
from app.core.security import hash_password
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.auth.schemas import UserRead
from app.modules.tenants.models import Department, Tenant
from app.modules.users.schemas import UserCreate


def _resolve_assignment(
    scope: AccessScope,
    payload: UserCreate,
) -> tuple[PydanticObjectId | None, PydanticObjectId | None]:
    tenant_id = to_object_id(payload.tenant_id, "tenant id") if payload.tenant_id else None
    department_id = to_object_id(payload.department_id, "department id") if payload.department_id else None

    if payload.role == Role.SUPER_ADMIN:
        if scope.role != Role.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission for this action",
            )
        if tenant_id is not None or department_id is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Super admin accounts are not assigned to a college",
            )
        return None, None

    if payload.role not in TENANT_REQUIRED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="This role must belong to a college",
        )

    if scope.role == Role.COLLEGE_ADMIN:
        if tenant_id is not None and str(tenant_id) != str(scope.tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot access another college",
            )
        tenant_id = scope.tenant_id
    elif scope.role == Role.SUPER_ADMIN:
        if tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="This role must belong to a college",
            )
        if scope.tenant_id is not None and str(scope.tenant_id) != str(tenant_id):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Tenant does not match the selected college",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission for this action",
        )

    if payload.role in DEPARTMENT_REQUIRED_ROLES and department_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="This role must belong to a department",
        )
    return tenant_id, department_id


async def create_user(scope: AccessScope, payload: UserCreate) -> UserRead:
    tenant_id, department_id = _resolve_assignment(scope, payload)
    email = str(payload.email).lower()

    if tenant_id is not None:
        tenant = await Tenant.get(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="College not found")
        if not tenant.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This college is inactive")

    if department_id is not None:
        department = await Department.get(department_id)
        if department is None or str(department.tenant_id) != str(tenant_id):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Department does not belong to this college",
            )

    existing = await User.find_one(User.email == email)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists")

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
    if scope.tenant_id is None and not scope.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="College context is required")

    filters: dict = {}
    if scope.tenant_id is not None:
        filters["tenant_id"] = scope.tenant_id

    total = await User.find(filters).count()
    documents = await User.find(filters).sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[UserRead.from_document(document) for document in documents],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_user(scope: AccessScope, user_id: PydanticObjectId) -> UserRead:
    user = await User.get(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if scope.tenant_id is not None and str(user.tenant_id) != str(scope.tenant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if scope.tenant_id is None and not scope.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="College context is required")
    return UserRead.from_document(user)
