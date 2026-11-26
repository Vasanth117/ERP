"""Library settings page (CA 12.13)."""

from __future__ import annotations

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.academic_config_models import AcademicRegulation
from app.modules.college_admin.library_admin_models import LibraryBorrowingPolicy
from app.modules.college_admin.library_admin_schemas import BorrowingPolicyUpsert
from app.modules.college_admin.library_admin_service import upsert_borrowing_policy
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    InstitutionFieldMeta,
    InstitutionFieldOption,
    LibrarySettingsFormValues,
    LibrarySettingsPageRead,
    LibrarySettingsSave,
    LibrarySettingsToggleRule,
)
from app.modules.library.fine_models import LibraryFinePolicy
from app.modules.library.settings_enums import LibraryPolicyStatus
from app.modules.library.settings_models import LibraryBorrowingRule

_SCOPE_KEY = "library_administration_settings"

_DEFAULTS: dict[str, object] = {
    "student_borrow_limit": "4",
    "faculty_borrow_limit": "10",
    "loan_period_days": "14",
    "renewals_allowed": "2",
    "fine_per_day": "2",
    "reservation_hold_days": "5",
    "block_unpaid_fines": True,
    "send_due_reminders": True,
    "allow_external_members": False,
    "reminder_days_before": 2,
}

_FIELD_META = [
    InstitutionFieldMeta(key="student_borrow_limit", label="Student limit", field_type="select", required=True),
    InstitutionFieldMeta(key="faculty_borrow_limit", label="Faculty limit", field_type="select", required=True),
    InstitutionFieldMeta(key="loan_period_days", label="Loan period", field_type="select", required=True),
    InstitutionFieldMeta(key="renewals_allowed", label="Renewals allowed", field_type="select", required=True),
    InstitutionFieldMeta(key="fine_per_day", label="Fine per day", field_type="select", required=True),
    InstitutionFieldMeta(key="reservation_hold_days", label="Reservation hold", field_type="select", required=True),
]

_BORROW_LIMIT_OPTIONS = [InstitutionFieldOption(value=str(n), label=f"{n} books") for n in (2, 3, 4, 5, 6, 8, 10, 12, 15)]
_LOAN_DAYS = [InstitutionFieldOption(value=str(n), label=f"{n} days") for n in (7, 10, 14, 21, 30)]
_RENEWALS = [InstitutionFieldOption(value=str(n), label=str(n)) for n in range(0, 6)]
_FINES = [InstitutionFieldOption(value=str(n), label=f"₹{n}") for n in (1, 2, 3, 5, 10, 15)]
_HOLDS = [InstitutionFieldOption(value=str(n), label=f"{n} days") for n in (3, 5, 7, 10, 14)]

_FIELD_OPTIONS: dict[str, list[InstitutionFieldOption]] = {
    "student_borrow_limit": _BORROW_LIMIT_OPTIONS,
    "faculty_borrow_limit": _BORROW_LIMIT_OPTIONS,
    "loan_period_days": _LOAN_DAYS,
    "renewals_allowed": _RENEWALS,
    "fine_per_day": _FINES,
    "reservation_hold_days": _HOLDS,
}


async def _load_rules(tenant_id) -> dict[str, object]:
    doc = await AcademicRegulation.find_one(
        Eq(AcademicRegulation.tenant_id, tenant_id),
        Eq(AcademicRegulation.scope_key, _SCOPE_KEY),
    )
    merged = dict(_DEFAULTS)
    if doc and doc.rules:
        merged.update(doc.rules)

    policy = await LibraryBorrowingPolicy.find_one(
        Eq(LibraryBorrowingPolicy.tenant_id, tenant_id),
        Eq(LibraryBorrowingPolicy.branch_code, None),
    )
    if policy:
        merged["student_borrow_limit"] = str(policy.max_books)
        merged["loan_period_days"] = str(policy.loan_days)
        merged["renewals_allowed"] = str(policy.renewal_limit)
        merged["fine_per_day"] = str(int(policy.fine_per_day) if policy.fine_per_day == int(policy.fine_per_day) else policy.fine_per_day)

    rule = await LibraryBorrowingRule.find_one(
        Eq(LibraryBorrowingRule.tenant_id, tenant_id),
        Eq(LibraryBorrowingRule.member_category, "faculty"),
        Eq(LibraryBorrowingRule.status, LibraryPolicyStatus.ACTIVE.value),
    )
    if rule:
        merged["faculty_borrow_limit"] = str(rule.max_books)
        merged["reservation_hold_days"] = str(max(1, rule.hold_hours // 24))

    fine_policy = await LibraryFinePolicy.find_one(Eq(LibraryFinePolicy.tenant_id, tenant_id), Eq(LibraryFinePolicy.branch_code, None))
    if fine_policy:
        merged["fine_per_day"] = str(int(fine_policy.fine_per_day) if fine_policy.fine_per_day == int(fine_policy.fine_per_day) else fine_policy.fine_per_day)

    return merged


def _form_values(rules: dict[str, object]) -> LibrarySettingsFormValues:
    return LibrarySettingsFormValues(
        student_borrow_limit=str(rules.get("student_borrow_limit", _DEFAULTS["student_borrow_limit"])),
        faculty_borrow_limit=str(rules.get("faculty_borrow_limit", _DEFAULTS["faculty_borrow_limit"])),
        loan_period_days=str(rules.get("loan_period_days", _DEFAULTS["loan_period_days"])),
        renewals_allowed=str(rules.get("renewals_allowed", _DEFAULTS["renewals_allowed"])),
        fine_per_day=str(rules.get("fine_per_day", _DEFAULTS["fine_per_day"])),
        reservation_hold_days=str(rules.get("reservation_hold_days", _DEFAULTS["reservation_hold_days"])),
        block_unpaid_fines=bool(rules.get("block_unpaid_fines", True)),
        send_due_reminders=bool(rules.get("send_due_reminders", True)),
        allow_external_members=bool(rules.get("allow_external_members", False)),
    )


def _toggle_rules(form: LibrarySettingsFormValues, rules: dict[str, object]) -> list[LibrarySettingsToggleRule]:
    reminder = rules.get("reminder_days_before", 2)
    return [
        LibrarySettingsToggleRule(
            key="block_unpaid_fines",
            label="Block members with unpaid fines",
            enabled=form.block_unpaid_fines,
        ),
        LibrarySettingsToggleRule(
            key="send_due_reminders",
            label="Send due-date reminders",
            badge_label=f"{reminder} days before",
            enabled=form.send_due_reminders,
        ),
        LibrarySettingsToggleRule(
            key="allow_external_members",
            label="Allow external members",
            enabled=form.allow_external_members,
        ),
    ]


async def get_library_settings_page(scope: AccessScope) -> LibrarySettingsPageRead:
    authorize(scope, Permission.LIBRARY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    rules = await _load_rules(tenant_id)
    form = _form_values(rules)
    return LibrarySettingsPageRead(
        page_title="Library Settings",
        page_subtitle="Borrowing rules and fines",
        cancel_label="Cancel",
        save_label="Save",
        borrowing_rules_section_title="Borrowing rules",
        controls_section_title="Controls",
        field_meta=_FIELD_META,
        field_options=_FIELD_OPTIONS,
        form=form,
        toggle_rules=_toggle_rules(form, rules),
        generated_at=now,
    )


async def save_library_settings_page(scope: AccessScope, payload: LibrarySettingsSave) -> LibrarySettingsPageRead:
    authorize(scope, Permission.LIBRARY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    form = payload.form
    rules = {
        **_DEFAULTS,
        **form.model_dump(),
    }
    doc = await AcademicRegulation.find_one(
        Eq(AcademicRegulation.tenant_id, tenant_id),
        Eq(AcademicRegulation.scope_key, _SCOPE_KEY),
    )
    if doc is None:
        doc = AcademicRegulation(tenant_id=tenant_id, scope_key=_SCOPE_KEY, rules=rules, updated_by=scope.user_id)
        await doc.insert()
    else:
        doc.rules = rules
        doc.updated_by = scope.user_id
        doc.updated_at = utcnow()
        await doc.save()

    await upsert_borrowing_policy(
        scope,
        BorrowingPolicyUpsert(
            branch_code=None,
            max_books=int(form.student_borrow_limit),
            loan_days=int(form.loan_period_days),
            renewal_limit=int(form.renewals_allowed),
            fine_per_day=float(form.fine_per_day),
        ),
    )

    return await get_library_settings_page(scope)