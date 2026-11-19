"""Fee category management."""

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.core.exceptions import AppError
from app.modules.accounts_finance.models import FinanceFeeCategory
from app.modules.accounts_finance.policy import (
    authorize_finance_fee_category_manage,
    authorize_finance_fee_category_read,
    require_finance_tenant_scope,
)
from app.modules.accounts_finance.schemas import FeeCategoryRead, FeeCategoryUpsert
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.common.time import utcnow


async def upsert_fee_category(scope: AccessScope, payload: FeeCategoryUpsert) -> FeeCategoryRead:
    authorize_finance_fee_category_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    if payload.mandatory and payload.optional_flag:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Fee cannot be both mandatory and optional",
            status_code=422,
        )
    code = payload.fee_code
    existing = await FinanceFeeCategory.find_one(
        Eq(FinanceFeeCategory.tenant_id, tenant_id),
        Eq(FinanceFeeCategory.fee_code, code),
    )
    programme_codes = [c.upper() for c in payload.programme_codes]
    if existing:
        existing.name = payload.name
        existing.description = payload.description
        existing.classification = payload.classification
        existing.programme_codes = programme_codes
        existing.student_categories = payload.student_categories
        existing.mandatory = payload.mandatory
        existing.optional_flag = payload.optional_flag
        existing.refundability = payload.refundability
        existing.tax_reference = payload.tax_reference
        existing.active = payload.active
        existing.updated_by = scope.user_id
        existing.updated_at = utcnow()
        await existing.save()
        doc = existing
    else:
        doc = FinanceFeeCategory(
            tenant_id=tenant_id,
            fee_code=code,
            name=payload.name,
            description=payload.description,
            classification=payload.classification,
            programme_codes=programme_codes,
            student_categories=payload.student_categories,
            mandatory=payload.mandatory,
            optional_flag=payload.optional_flag,
            refundability=payload.refundability,
            tax_reference=payload.tax_reference,
            active=payload.active,
            created_by=scope.user_id,
            updated_by=scope.user_id,
        )
        await doc.insert()
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="finance.fee_category.upsert",
        module="accounts_finance",
        resource_type="fee_category",
        resource_id=code,
    )
    return FeeCategoryRead.from_document(doc)


async def list_fee_categories(scope: AccessScope, pagination: Pagination, *, active_only: bool = False) -> Page[FeeCategoryRead]:
    authorize_finance_fee_category_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    if active_only:
        query = FinanceFeeCategory.find(
            Eq(FinanceFeeCategory.tenant_id, tenant_id),
            Eq(FinanceFeeCategory.active, True),
        )
    else:
        query = FinanceFeeCategory.find(Eq(FinanceFeeCategory.tenant_id, tenant_id))
    total = await query.count()
    rows = await query.sort("-updated_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[FeeCategoryRead.from_document(r) for r in rows],
        total=total,
        offset=pagination.offset,
        limit=pagination.limit,
    )


async def get_fee_category(scope: AccessScope, fee_code: str) -> FeeCategoryRead:
    authorize_finance_fee_category_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    doc = await FinanceFeeCategory.find_one(
        Eq(FinanceFeeCategory.tenant_id, tenant_id),
        Eq(FinanceFeeCategory.fee_code, fee_code.strip().upper()),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Fee category not found", status_code=404)
    return FeeCategoryRead.from_document(doc)