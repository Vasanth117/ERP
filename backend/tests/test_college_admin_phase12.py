"""College Admin phase 12 — finance and operations extensions."""

from datetime import date
from uuid import uuid4

import pytest

from app.authorization.permissions import Permission, permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.finance_ext_schemas import (
    BudgetAllocationUpsert,
    BudgetUpsert,
    ExpenseApprove,
    ExpenseCreate,
    PurchaseOrderCreate,
    PurchaseRequestApprove,
    PurchaseRequestCreate,
    VendorUpsert,
)
from app.modules.college_admin.finance_ext_service import (
    allocate_department_budget,
    approve_expense,
    approve_purchase_request,
    budget_report,
    budget_utilization,
    create_expense,
    create_purchase_order,
    create_purchase_request,
    upsert_budget,
    upsert_vendor,
)
from app.modules.college_admin.operations_ext_schemas import (
    AssetAllocate,
    AssetUpsert,
    InventoryUpsert,
    MaintenanceAssign,
    MaintenanceCreate,
    StockMovementCreate,
)
from app.modules.college_admin.operations_ext_service import (
    allocate_asset,
    assign_maintenance,
    create_maintenance,
    operations_report,
    record_stock_movement,
    upsert_asset,
    upsert_inventory,
)
from app.modules.tenants.models import Department, Tenant


@pytest.fixture
async def db_ready():
    try:
        await connect_to_mongo()
    except Exception as exc:
        pytest.skip(f"MongoDB not available: {exc}")
    try:
        await connect_redis()
    except Exception:
        pass
    for model in document_models():
        await model.get_motor_collection().delete_many({})
    yield
    await close_redis()
    await close_mongo()


async def _seed_admin(suffix: str) -> tuple[Tenant, User, AccessScope, Department]:
    tenant = Tenant(name=f"College P12 {suffix}", code=f"p12_{suffix}")
    await tenant.insert()
    dept = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await dept.insert()
    user = User(
        email=f"admin+p12+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await user.insert()
    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=user.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    return tenant, user, scope, dept


@pytest.mark.anyio
async def test_budget_allocation_and_expense_approval(db_ready):
    _, admin, scope, dept = await _seed_admin(uuid4().hex[:6])
    bid = f"bud_{uuid4().hex[:8]}"
    await upsert_budget(
        scope,
        admin,
        BudgetUpsert(
            budget_id=bid,
            label="FY Ops",
            fiscal_year="2025-26",
            period_start=date(2025, 4, 1),
            period_end=date(2026, 3, 31),
            total_amount=100_000,
        ),
    )
    await allocate_department_budget(
        scope,
        admin,
        BudgetAllocationUpsert(
            allocation_id=f"alloc_{uuid4().hex[:8]}",
            budget_id=bid,
            department_id=str(dept.id),
            allocated_amount=50_000,
        ),
    )
    eid = f"exp_{uuid4().hex[:8]}"
    await create_expense(
        scope,
        admin,
        ExpenseCreate(
            expense_id=eid,
            title="Lab consumables",
            amount=5_000,
            budget_id=bid,
            department_id=str(dept.id),
            submit_for_approval=True,
        ),
    )
    await approve_expense(scope, admin, eid, ExpenseApprove(approved=True))
    util = await budget_utilization(scope, bid)
    assert util.utilized == 5_000
    report = await budget_report(scope, bid)
    assert report.expense_count == 1


@pytest.mark.anyio
async def test_procurement_vendor_pr_po(db_ready):
    _, admin, scope, dept = await _seed_admin(uuid4().hex[:6])
    vid = f"ven_{uuid4().hex[:8]}"
    await upsert_vendor(scope, admin, VendorUpsert(vendor_id=vid, name="Acme Supplies", contact_email="vendor@example.com"))
    rid = f"pr_{uuid4().hex[:8]}"
    await create_purchase_request(
        scope,
        admin,
        PurchaseRequestCreate(
            request_id=rid,
            description="Projectors",
            estimated_amount=120_000,
            vendor_id=vid,
            department_id=str(dept.id),
            submit=True,
        ),
    )
    await approve_purchase_request(scope, admin, rid, PurchaseRequestApprove(approved=True))
    oid = f"po_{uuid4().hex[:8]}"
    result = await create_purchase_order(
        scope,
        admin,
        PurchaseOrderCreate(order_id=oid, request_id=rid, vendor_id=vid, total_amount=118_000),
    )
    assert result["order_id"] == oid
    with pytest.raises(AppError) as exc:
        await create_purchase_order(
            scope,
            admin,
            PurchaseOrderCreate(order_id=f"po_{uuid4().hex[:8]}", request_id=rid, vendor_id=vid, total_amount=1),
        )
    assert exc.value.status_code == 422


@pytest.mark.anyio
async def test_operations_asset_maintenance_inventory(db_ready):
    _, admin, scope, dept = await _seed_admin(uuid4().hex[:6])
    asset_id = f"ast_{uuid4().hex[:8]}"
    await upsert_asset(scope, admin, AssetUpsert(asset_id=asset_id, tag="TAG-001", name="Server rack", category="it"))
    await allocate_asset(
        scope,
        admin,
        asset_id,
        AssetAllocate(allocation_id=f"al_{uuid4().hex[:8]}", department_id=str(dept.id)),
    )
    mrid = f"mnt_{uuid4().hex[:8]}"
    await create_maintenance(scope, admin, MaintenanceCreate(request_id=mrid, title="Cooling failure", description="Fan dead", asset_id=asset_id))
    await assign_maintenance(scope, admin, mrid, MaintenanceAssign(assigned_team="facilities"))
    item_id = f"inv_{uuid4().hex[:8]}"
    await upsert_inventory(scope, admin, InventoryUpsert(item_id=item_id, sku="SKU-1", name="Cable", quantity_on_hand=10, reorder_level=3))
    await record_stock_movement(
        scope,
        admin,
        StockMovementCreate(movement_id=f"mv_{uuid4().hex[:8]}", item_id=item_id, quantity=2, direction="out"),
    )
    with pytest.raises(AppError) as exc:
        await record_stock_movement(
            scope,
            admin,
            StockMovementCreate(movement_id=f"mv_{uuid4().hex[:8]}", item_id=item_id, quantity=20, direction="out"),
        )
    assert exc.value.status_code == 422
    report = await operations_report(scope)
    assert report.assets_total >= 1


@pytest.mark.anyio
async def test_finance_budget_permission_denied(db_ready):
    _, admin, scope, _ = await _seed_admin(uuid4().hex[:6])
    read_only = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=scope.user_id,
        tenant_id=scope.tenant_id,
        department_id=None,
        effective_permissions=frozenset({Permission.FINANCE_EXT_READ}),
    )
    with pytest.raises(AppError) as exc:
        await upsert_budget(
            read_only,
            admin,
            BudgetUpsert(
                budget_id="bud_denied",
                label="X",
                fiscal_year="2025",
                period_start=date(2025, 1, 1),
                period_end=date(2025, 12, 31),
                total_amount=1,
            ),
        )
    assert exc.value.status_code == 403


@pytest.mark.anyio
async def test_tenant_isolation_budget(db_ready):
    _, admin1, scope1, dept = await _seed_admin(uuid4().hex[:6])
    _, _, scope2, _ = await _seed_admin(uuid4().hex[:6])
    bid = f"bud_{uuid4().hex[:8]}"
    await upsert_budget(
        scope1,
        admin1,
        BudgetUpsert(
            budget_id=bid,
            label="Iso",
            fiscal_year="2025",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            total_amount=10_000,
        ),
    )
    with pytest.raises(AppError) as exc:
        await budget_utilization(scope2, bid)
    assert exc.value.status_code == 404
    assert dept.id is not None