"""Mutable state passed between demo seed steps."""

from dataclasses import dataclass, field

from beanie import PydanticObjectId

from app.common.access import AccessScope
from app.modules.auth.models import User
from app.modules.tenants.models import Department, Tenant


@dataclass
class DemoSeedContext:
    tenant: Tenant
    admin: User
    admin_scope: AccessScope
    main_campus_id: PydanticObjectId | None = None
    departments: dict[str, Department] = field(default_factory=dict)
    faculty_users: list[User] = field(default_factory=list)
    student_users: list[User] = field(default_factory=list)
    staff_users: dict[str, User] = field(default_factory=dict)