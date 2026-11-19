"""HR staff portal phase 6 — payroll processing and payslips."""

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.college_admin.hr_admin_models import PayrollConfiguration
from app.modules.college_admin.models import InstitutionCampus
from app.modules.hr.employee_profile_schemas import EmployeeRegister
from app.modules.hr.employee_profile_service import register_employee
from app.modules.hr.enums import HrPayrollRunStatus, HrSalaryComponentCategory, HrSalaryCalcType
from app.modules.hr.payroll_schemas import PaymentConfirm, PayrollPeriodCreate, PayrollRunCreate, PayrollTransition, PayslipGenerateRequest
from app.modules.hr.payroll_service import (
    calculate_payroll_run,
    confirm_employee_payment,
    create_payroll_period,
    create_payroll_run,
    get_payroll_preview,
    submit_payroll_for_payment,
    transition_payroll_run,
)
from app.modules.hr.payslip_service import generate_payslips, list_payslips, publish_payslip
from app.modules.hr.salary_structure_schemas import SalaryAssignmentCreate, SalaryComponentUpsert, SalaryTemplateUpsert
from app.modules.hr.salary_structure_service import activate_salary_assignment, create_salary_assignment, submit_salary_assignment, upsert_salary_component, upsert_salary_template
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
    tenant = Tenant(name=f"HR6 {suffix}", code=f"hr6_{suffix}")
    await tenant.insert()
    dept = Department(tenant_id=tenant.id, name="Finance", code=f"FIN-{suffix}")
    await dept.insert()
    campus = InstitutionCampus(tenant_id=tenant.id, campus_code=f"C{suffix}", name="Main", is_main=True)
    await campus.insert()
    hr_user = User(
        email=f"hr6+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="HR Staff",
        role=Role.HR_STAFF,
        tenant_id=tenant.id,
    )
    await hr_user.insert()
    scope = _scope(hr_user, Role.HR_STAFF)
    profile = await register_employee(
        scope,
        EmployeeRegister(
            employee_code=f"EMP-{suffix}",
            first_name="Nina",
            last_name="Das",
            official_email=f"nina.{suffix}@example.com",
            password="password1234567890",
            mobile_number="9000000020",
            joining_date=date.today() - timedelta(days=400),
            employee_category="administrative",
            employment_type="full_time",
            department_id=str(dept.id),
            designation="Accountant",
            campus_id=str(campus.id),
        ),
    )
    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.employee_id, profile.employee_code))
    assert employee is not None
    await PayrollConfiguration(
        tenant_id=tenant.id,
        config_id=f"default-{suffix}",
        label="Default",
        confidential_config={"statutory_rates": {"provident_fund": "12"}},
    ).insert()
    await upsert_salary_component(
        scope,
        SalaryComponentUpsert(component_code="basic", name="Basic", category=HrSalaryComponentCategory.EARNING, effective_from=date.today()),
    )
    template = await upsert_salary_template(
        scope,
        SalaryTemplateUpsert(
            template_code=f"PAY-{suffix}",
            title="Payroll Template",
            template_kind="administrative",
            component_lines=[
                {"component_code": "basic", "category": "earning", "calc_type": "fixed"},
                {"component_code": "pf", "category": "deduction", "calc_type": "percentage", "percentage_of": "basic", "statutory_ref": "provident_fund"},
            ],
        ),
    )
    assignment = await create_salary_assignment(
        scope,
        SalaryAssignmentCreate(
            employee_user_id=str(employee.user_id),
            template_id=template.id,
            component_amounts={"basic": "30000.00"},
            effective_from=date.today() - timedelta(days=60),
        ),
    )
    await submit_salary_assignment(scope, assignment.id)
    await activate_salary_assignment(scope, assignment.id)
    return scope, employee


@pytest.mark.asyncio
async def test_payroll_to_payslip_lifecycle(db_ready):
    suffix = uuid4().hex[:8]
    scope, employee = await _seed(suffix)
    today = date.today()
    _, last_day = monthrange(today.year, today.month)
    period = await create_payroll_period(
        scope,
        PayrollPeriodCreate(
            period_year=today.year,
            period_month=today.month,
            start_date=date(today.year, today.month, 1),
            end_date=date(today.year, today.month, last_day),
            attendance_cutoff=date(today.year, today.month, last_day),
            expected_payment_date=today + timedelta(days=5),
        ),
    )
    run = await create_payroll_run(scope, PayrollRunCreate(payroll_period_id=period.id))
    calculated = await calculate_payroll_run(scope, run.id)
    assert calculated.status in {HrPayrollRunStatus.READY_FOR_REVIEW, HrPayrollRunStatus.VALIDATION_REQUIRED}
    preview = await get_payroll_preview(scope, run.id)
    assert preview.employees
    emp_preview = next(p for p in preview.employees if p.employee_user_id == str(employee.user_id))
    assert Decimal(emp_preview.net_payable) > 0

    if calculated.status == HrPayrollRunStatus.VALIDATION_REQUIRED:
        await transition_payroll_run(scope, run.id, PayrollTransition(target_status=HrPayrollRunStatus.READY_FOR_REVIEW))
    await transition_payroll_run(scope, run.id, PayrollTransition(target_status=HrPayrollRunStatus.UNDER_REVIEW))
    approved = await transition_payroll_run(scope, run.id, PayrollTransition(target_status=HrPayrollRunStatus.APPROVED))
    assert approved.status == HrPayrollRunStatus.APPROVED

    pay_submit = await submit_payroll_for_payment(scope, run.id)
    assert pay_submit["submitted_payments"] >= 1
    await confirm_employee_payment(
        scope,
        run.id,
        PaymentConfirm(employee_user_id=str(employee.user_id), payment_reference=f"TXN-{suffix}"),
    )
    gen = await generate_payslips(scope, PayslipGenerateRequest(payroll_run_id=run.id))
    assert gen["generated"] >= 1
    slips = await list_payslips(scope, period_label=f"{today.year}-{today.month:02d}")
    published = await publish_payslip(scope, slips[0].id)
    assert published.status.value == "published"