"""HR staff portal phase 7 — statutory/tax configuration and employee self-service."""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.college_admin.models import InstitutionCampus
from app.modules.hr.employee_profile_schemas import EmployeeRegister
from app.modules.hr.employee_profile_service import register_employee
from app.modules.hr.employee_self_service_service import get_my_profile
from app.modules.hr.enums import HrStatutoryComponentKind, HrTaxFinancialYearStatus, LeaveDayPortion
from app.modules.hr.statutory_tax_schemas import (
    StatutoryComponentUpsert,
    StatutoryRuleVersionCreate,
    TaxDeclarationUpsert,
    TaxFinancialYearUpsert,
)
from app.modules.hr.statutory_tax_service import (
    create_statutory_rule_version,
    save_tax_declaration_draft,
    submit_tax_declaration,
    upsert_statutory_component,
    upsert_tax_financial_year,
)
from app.modules.hr.statutory_calculation import resolve_statutory_rates_for_employee
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
    tenant = Tenant(name=f"HR7 {suffix}", code=f"hr7_{suffix}")
    await tenant.insert()
    dept = Department(tenant_id=tenant.id, name="HR", code=f"HR-{suffix}")
    await dept.insert()
    campus = InstitutionCampus(tenant_id=tenant.id, campus_code=f"C{suffix}", name="Main", is_main=True)
    await campus.insert()
    hr_user = User(
        email=f"hr7+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="HR Staff",
        role=Role.HR_STAFF,
        tenant_id=tenant.id,
    )
    await hr_user.insert()
    emp_user = User(
        email=f"emp7+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Employee",
        role=Role.FACULTY,
        tenant_id=tenant.id,
    )
    await emp_user.insert()
    hr_scope = _scope(hr_user, Role.HR_STAFF)
    emp_scope = _scope(emp_user, Role.FACULTY)
    await register_employee(
        hr_scope,
        EmployeeRegister(
            employee_code=f"EMP7-{suffix}",
            first_name="Test",
            last_name="Employee",
            official_email=f"official7+{suffix}@college.edu",
            mobile_number="9999999999",
            joining_date=date.today() - timedelta(days=90),
            employee_category="faculty",
            employment_type="permanent",
            department_id=str(dept.id),
            designation="Assistant Professor",
            campus_id=str(campus.id),
            link_existing_user_id=str(emp_user.id),
            institution_role=Role.FACULTY,
        ),
    )
    return tenant, hr_scope, emp_scope, emp_user


@pytest.mark.asyncio
async def test_statutory_tax_and_self_service(db_ready):
    suffix = uuid4().hex[:6]
    tenant, hr_scope, emp_scope, emp_user = await _seed(suffix)

    component = await upsert_statutory_component(
        hr_scope,
        StatutoryComponentUpsert(
            component_code="pf",
            display_name="Provident Fund",
            component_kind=HrStatutoryComponentKind.EMPLOYEE_DEDUCTION,
            statutory_ref="provident_fund",
            employee_categories=["faculty"],
        ),
    )
    await create_statutory_rule_version(
        hr_scope,
        StatutoryRuleVersionCreate(
            component_id=component.id,
            effective_from=date.today() - timedelta(days=30),
            employee_rate_percent="12",
            employer_rate_percent="12",
        ),
    )
    rates, warnings, meta = await resolve_statutory_rates_for_employee(
        tenant_id=tenant.id,
        as_of=date.today(),
        employee_category="faculty",
        employee_user_id=emp_user.id,
    )
    assert rates.get("provident_fund") == "12"
    assert meta.get("source") == "statutory_configuration"

    fy = await upsert_tax_financial_year(
        hr_scope,
        TaxFinancialYearUpsert(
            fy_code="FY2425",
            label="FY 2024-25",
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            assessment_year="2025-26",
            status=HrTaxFinancialYearStatus.ACTIVE,
        ),
    )
    decl = await save_tax_declaration_draft(
        emp_scope,
        str(emp_user.id),
        TaxDeclarationUpsert(financial_year_id=fy.id, regime_code="new", declaration_lines={"80c": {"amount": "150000"}}),
        self_service=True,
    )
    assert decl.status.value == "draft"
    submitted = await submit_tax_declaration(emp_scope, decl.id, self_service=True)
    assert submitted.status.value == "submitted"

    profile = await get_my_profile(emp_scope, emp_user)
    assert profile.employee_user_id == str(emp_user.id)
    assert profile.designation == "Assistant Professor"

    from beanie.odm.operators.find.comparison import Eq

    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant.id), Eq(EmployeeRecord.user_id, emp_user.id))
    assert employee is not None