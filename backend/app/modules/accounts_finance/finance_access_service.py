"""Finance access scope and temporary grants (complements central RBAC)."""

import uuid
from datetime import datetime, timezone

from beanie.odm.operators.find.comparison import Eq, LTE, GTE

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.accounts_finance.phase12_models import FinanceAccessAssignment, FinanceAccessReviewHistory, FinanceTemporaryAccessGrant
from app.modules.accounts_finance.policy import (
    authorize_finance_settings_approve,
    authorize_finance_settings_manage,
    authorize_finance_settings_read,
    require_finance_tenant_scope,
)
from app.modules.college_admin.security_admin_service import append_institution_audit


async def assign_finance_scope(scope: AccessScope, payload: dict) -> dict:
    authorize_finance_settings_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    user_id = to_object_id(payload["user_id"], "user_id")
    assignment_id = f"fas_{uuid.uuid4().hex[:10]}"
    doc = FinanceAccessAssignment(
        tenant_id=tenant_id,
        assignment_id=assignment_id,
        user_id=user_id,
        scope_type=payload["scope_type"],
        scope_ref=payload.get("scope_ref"),
        assigned_by=scope.user_id,
    )
    await doc.insert()
    await FinanceAccessReviewHistory(
        tenant_id=tenant_id,
        review_id=f"far_{uuid.uuid4().hex[:10]}",
        user_id=user_id,
        action="scope_assigned",
        detail={"scope_type": doc.scope_type, "scope_ref": doc.scope_ref},
        actor_id=scope.user_id,
    ).insert()
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="finance.access.scope_assigned",
        module="accounts_finance",
        resource_type="finance_access_assignment",
        resource_id=assignment_id,
    )
    return {"assignment_id": assignment_id}


async def grant_temporary_access(scope: AccessScope, payload: dict) -> dict:
    authorize_finance_settings_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    user_id = to_object_id(payload["user_id"], "user_id")
    grant_id = f"ftg_{uuid.uuid4().hex[:10]}"
    valid_from = payload.get("valid_from") or datetime.now(timezone.utc)
    valid_to = payload["valid_to"]
    if valid_to <= valid_from:
        raise AppError(code="VALIDATION_ERROR", message="valid_to must be after valid_from", status_code=400)
    await FinanceTemporaryAccessGrant(
        tenant_id=tenant_id,
        grant_id=grant_id,
        user_id=user_id,
        permissions=payload.get("permissions") or [],
        valid_from=valid_from,
        valid_to=valid_to,
        granted_by=scope.user_id,
    ).insert()
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="finance.access.temporary_grant",
        module="accounts_finance",
        resource_type="finance_temporary_access",
        resource_id=grant_id,
    )
    return {"grant_id": grant_id}


async def list_active_access(scope: AccessScope, user_id: str | None = None) -> dict:
    authorize_finance_settings_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    clauses = [Eq(FinanceAccessAssignment.tenant_id, tenant_id), Eq(FinanceAccessAssignment.active, True)]
    if user_id:
        clauses.append(Eq(FinanceAccessAssignment.user_id, to_object_id(user_id, "user_id")))
    assignments = await FinanceAccessAssignment.find(*clauses).to_list()
    now = datetime.now(timezone.utc)
    raw_grants = await FinanceTemporaryAccessGrant.find(
        Eq(FinanceTemporaryAccessGrant.tenant_id, tenant_id),
        Eq(FinanceTemporaryAccessGrant.revoked, False),
        LTE(FinanceTemporaryAccessGrant.valid_from, now),
        GTE(FinanceTemporaryAccessGrant.valid_to, now),
    ).to_list()
    grants = [g for g in raw_grants if g.valid_from <= now <= g.valid_to]
    return {
        "assignments": [
            {"assignment_id": a.assignment_id, "user_id": str(a.user_id), "scope_type": a.scope_type, "scope_ref": a.scope_ref}
            for a in assignments
        ],
        "temporary_grants": [
            {"grant_id": g.grant_id, "user_id": str(g.user_id), "permissions": g.permissions, "valid_to": g.valid_to.isoformat()}
            for g in grants
        ],
    }


async def revoke_assignment(scope: AccessScope, assignment_id: str) -> dict:
    authorize_finance_settings_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    doc = await FinanceAccessAssignment.find_one(
        Eq(FinanceAccessAssignment.tenant_id, tenant_id),
        Eq(FinanceAccessAssignment.assignment_id, assignment_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Assignment not found", status_code=404)
    doc.active = False
    await doc.save()
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="finance.access.scope_revoked",
        module="accounts_finance",
        resource_type="finance_access_assignment",
        resource_id=assignment_id,
    )
    return {"assignment_id": assignment_id, "active": False}


def assert_finance_scope(scope: AccessScope, *, campus_id=None, department_id=None) -> None:
    """Optional scope guard when finance_access_assignments exist for the user."""
    return