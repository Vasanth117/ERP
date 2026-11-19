"""Accounts / Finance Staff authorization."""

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.core.exceptions import AppError


def _has_finance_dashboard(scope: AccessScope) -> bool:
    return (
        Permission.FINANCE_DASHBOARD_READ in scope.effective_permissions
        or Permission.FINANCE_ADMIN_READ in scope.effective_permissions
    )


def authorize_finance_dashboard(scope: AccessScope) -> None:
    if _has_finance_dashboard(scope):
        return
    authorize(scope, Permission.FINANCE_DASHBOARD_READ)


def authorize_finance_fee_category_read(scope: AccessScope) -> None:
    if Permission.FINANCE_FEE_CATEGORY_READ in scope.effective_permissions or Permission.FINANCE_ADMIN_READ in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_FEE_CATEGORY_READ)


def authorize_finance_fee_category_manage(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_FEE_CATEGORY_MANAGE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_CONFIG in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_FEE_CATEGORY_MANAGE)


def authorize_finance_structure_read(scope: AccessScope) -> None:
    if Permission.FINANCE_STRUCTURE_READ in scope.effective_permissions or Permission.FINANCE_ADMIN_READ in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_STRUCTURE_READ)


def authorize_finance_structure_manage(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_STRUCTURE_MANAGE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_CONFIG in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_STRUCTURE_MANAGE)


def authorize_finance_structure_approve(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_STRUCTURE_APPROVE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_APPROVE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_STRUCTURE_APPROVE)


def require_finance_tenant_scope(scope: AccessScope) -> PydanticObjectId:
    authorize_finance_dashboard(scope)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context is required", status_code=403)
    return scope.tenant_id


def authorize_finance_assessment_read(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_ASSESSMENT_READ in scope.effective_permissions
        or Permission.FINANCE_ADMIN_READ in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_ASSESSMENT_READ)


def authorize_finance_assessment_manage(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_ASSESSMENT_MANAGE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_MANAGE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_ASSESSMENT_MANAGE)


def authorize_finance_assessment_approve(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_ASSESSMENT_APPROVE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_APPROVE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_ASSESSMENT_APPROVE)


def authorize_finance_invoice_read(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_INVOICE_READ in scope.effective_permissions
        or Permission.FINANCE_ADMIN_READ in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_INVOICE_READ)


def authorize_finance_invoice_manage(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_INVOICE_MANAGE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_MANAGE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_INVOICE_MANAGE)


def authorize_finance_invoice_issue(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_INVOICE_ISSUE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_APPROVE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_INVOICE_ISSUE)


def authorize_finance_payment_config(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_PAYMENT_CONFIG in scope.effective_permissions
        or Permission.FINANCE_ADMIN_CONFIG in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_PAYMENT_CONFIG)


def authorize_finance_payment_read(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_PAYMENT_READ in scope.effective_permissions
        or Permission.FINANCE_TRANSACTIONS_READ in scope.effective_permissions
        or Permission.FINANCE_ADMIN_READ in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_PAYMENT_READ)


def authorize_finance_offline_collect(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_OFFLINE_COLLECT in scope.effective_permissions
        or Permission.FINANCE_ADMIN_TRANSACTIONS in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_OFFLINE_COLLECT)


def authorize_finance_offline_verify(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_OFFLINE_VERIFY in scope.effective_permissions
        or Permission.FINANCE_ADMIN_RECONCILE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_OFFLINE_VERIFY)


def authorize_finance_ledger_read(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_LEDGER_READ in scope.effective_permissions
        or Permission.FINANCE_ADMIN_READ in scope.effective_permissions
        or Permission.FINANCE_TRANSACTIONS_READ in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_LEDGER_READ)


def authorize_finance_ledger_manage(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_LEDGER_MANAGE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_MANAGE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_APPROVE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_LEDGER_MANAGE)


def authorize_finance_receipt_read(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_RECEIPT_READ in scope.effective_permissions
        or Permission.FINANCE_ADMIN_READ in scope.effective_permissions
        or Permission.FINANCE_PAYMENT_READ in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_RECEIPT_READ)


def authorize_finance_receipt_issue(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_RECEIPT_ISSUE in scope.effective_permissions
        or Permission.FINANCE_OFFLINE_VERIFY in scope.effective_permissions
        or Permission.FINANCE_ADMIN_TRANSACTIONS in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_RECEIPT_ISSUE)


def authorize_finance_receipt_manage(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_RECEIPT_MANAGE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_MANAGE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_RECEIPT_MANAGE)


def authorize_finance_scholarship_read(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_SCHOLARSHIP_READ in scope.effective_permissions
        or Permission.FINANCE_ADMIN_READ in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_SCHOLARSHIP_READ)


def authorize_finance_scholarship_manage(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_SCHOLARSHIP_MANAGE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_MANAGE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_SCHOLARSHIP_MANAGE)


def authorize_finance_scholarship_approve(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_SCHOLARSHIP_APPROVE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_APPROVE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_SCHOLARSHIP_APPROVE)


def authorize_finance_concession_read(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_CONCESSION_READ in scope.effective_permissions
        or Permission.FINANCE_ADMIN_READ in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_CONCESSION_READ)


def authorize_finance_concession_manage(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_CONCESSION_MANAGE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_MANAGE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_CONCESSION_MANAGE)


def authorize_finance_concession_approve(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_CONCESSION_APPROVE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_APPROVE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_CONCESSION_APPROVE)


def authorize_finance_installment_read(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_INSTALLMENT_READ in scope.effective_permissions
        or Permission.FINANCE_ADMIN_READ in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_INSTALLMENT_READ)


def authorize_finance_installment_manage(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_INSTALLMENT_MANAGE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_MANAGE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_INSTALLMENT_MANAGE)


def authorize_finance_installment_approve(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_INSTALLMENT_APPROVE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_APPROVE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_INSTALLMENT_APPROVE)


def authorize_finance_late_fee_read(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_LATE_FEE_READ in scope.effective_permissions
        or Permission.FINANCE_ADMIN_READ in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_LATE_FEE_READ)


def authorize_finance_late_fee_manage(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_LATE_FEE_MANAGE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_MANAGE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_LATE_FEE_MANAGE)


def authorize_finance_late_fee_approve(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_LATE_FEE_APPROVE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_APPROVE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_LATE_FEE_APPROVE)


def authorize_finance_refund_read(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_REFUND_READ in scope.effective_permissions
        or Permission.FINANCE_ADMIN_READ in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_REFUND_READ)


def authorize_finance_refund_manage(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_REFUND_MANAGE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_MANAGE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_REFUND_MANAGE)


def authorize_finance_refund_approve(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_REFUND_APPROVE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_APPROVE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_REFUND_APPROVE)


def authorize_finance_reconciliation_read(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_RECONCILIATION_READ in scope.effective_permissions
        or Permission.FINANCE_ADMIN_RECONCILE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_READ in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_RECONCILIATION_READ)


def authorize_finance_reconciliation_manage(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_RECONCILIATION_MANAGE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_RECONCILE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_RECONCILIATION_MANAGE)


def authorize_finance_reconciliation_confirm(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_RECONCILIATION_CONFIRM in scope.effective_permissions
        or Permission.FINANCE_ADMIN_RECONCILE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_RECONCILIATION_CONFIRM)


def authorize_finance_outstanding_read(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_OUTSTANDING_READ in scope.effective_permissions
        or Permission.FINANCE_DASHBOARD_READ in scope.effective_permissions
        or Permission.FINANCE_ADMIN_READ in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_OUTSTANDING_READ)


def authorize_finance_report_read(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_REPORT_READ in scope.effective_permissions
        or Permission.FINANCE_DASHBOARD_READ in scope.effective_permissions
        or Permission.FINANCE_ADMIN_READ in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_REPORT_READ)


def authorize_finance_report_manage(scope: AccessScope) -> None:
    if Permission.FINANCE_REPORT_MANAGE in scope.effective_permissions or Permission.FINANCE_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_REPORT_MANAGE)


def authorize_finance_report_export(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_REPORT_EXPORT in scope.effective_permissions
        or Permission.FINANCE_REPORT_READ in scope.effective_permissions
        or Permission.FINANCE_ADMIN_READ in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_REPORT_EXPORT)


def authorize_finance_period_read(scope: AccessScope) -> None:
    if Permission.FINANCE_PERIOD_READ in scope.effective_permissions or Permission.FINANCE_ADMIN_READ in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_PERIOD_READ)


def authorize_finance_period_manage(scope: AccessScope) -> None:
    if Permission.FINANCE_PERIOD_MANAGE in scope.effective_permissions or Permission.FINANCE_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_PERIOD_MANAGE)


def authorize_finance_period_close(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_PERIOD_CLOSE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_APPROVE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_PERIOD_CLOSE)


def authorize_finance_period_reopen_approve(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_PERIOD_REOPEN_APPROVE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_APPROVE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_PERIOD_REOPEN_APPROVE)


def authorize_finance_gl_read(scope: AccessScope) -> None:
    if Permission.FINANCE_GL_READ in scope.effective_permissions or Permission.FINANCE_ADMIN_READ in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_GL_READ)


def authorize_finance_gl_manage(scope: AccessScope) -> None:
    if Permission.FINANCE_GL_MANAGE in scope.effective_permissions or Permission.FINANCE_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_GL_MANAGE)


def authorize_finance_gl_approve(scope: AccessScope) -> None:
    if Permission.FINANCE_GL_APPROVE in scope.effective_permissions or Permission.FINANCE_ADMIN_APPROVE in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_GL_APPROVE)


def authorize_finance_gl_journal_post(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_GL_JOURNAL_POST in scope.effective_permissions
        or Permission.FINANCE_GL_APPROVE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_MANAGE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_GL_JOURNAL_POST)


def authorize_finance_budget_read(scope: AccessScope) -> None:
    if Permission.FINANCE_BUDGET_READ in scope.effective_permissions or Permission.FINANCE_ADMIN_READ in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_BUDGET_READ)


def authorize_finance_budget_manage(scope: AccessScope) -> None:
    if Permission.FINANCE_BUDGET_MANAGE in scope.effective_permissions or Permission.FINANCE_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_BUDGET_MANAGE)


def authorize_finance_budget_approve(scope: AccessScope) -> None:
    if Permission.FINANCE_BUDGET_APPROVE in scope.effective_permissions or Permission.FINANCE_ADMIN_APPROVE in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_BUDGET_APPROVE)


def authorize_finance_vendor_read(scope: AccessScope) -> None:
    if Permission.FINANCE_VENDOR_READ in scope.effective_permissions or Permission.FINANCE_ADMIN_READ in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_VENDOR_READ)


def authorize_finance_vendor_manage(scope: AccessScope) -> None:
    if Permission.FINANCE_VENDOR_MANAGE in scope.effective_permissions or Permission.FINANCE_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_VENDOR_MANAGE)


def authorize_finance_vendor_bank(scope: AccessScope) -> None:
    if Permission.FINANCE_VENDOR_BANK in scope.effective_permissions or Permission.FINANCE_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_VENDOR_BANK)


def authorize_finance_procurement_read(scope: AccessScope) -> None:
    if Permission.FINANCE_PROCUREMENT_READ in scope.effective_permissions or Permission.FINANCE_ADMIN_READ in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_PROCUREMENT_READ)


def authorize_finance_procurement_manage(scope: AccessScope) -> None:
    if Permission.FINANCE_PROCUREMENT_MANAGE in scope.effective_permissions or Permission.FINANCE_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_PROCUREMENT_MANAGE)


def authorize_finance_procurement_approve(scope: AccessScope) -> None:
    if Permission.FINANCE_PROCUREMENT_APPROVE in scope.effective_permissions or Permission.FINANCE_ADMIN_APPROVE in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_PROCUREMENT_APPROVE)


def authorize_finance_procurement_pay(scope: AccessScope) -> None:
    if Permission.FINANCE_PROCUREMENT_PAY in scope.effective_permissions or Permission.FINANCE_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_PROCUREMENT_PAY)


def authorize_finance_expense_read(scope: AccessScope) -> None:
    if Permission.FINANCE_EXPENSE_READ in scope.effective_permissions or Permission.FINANCE_ADMIN_READ in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_EXPENSE_READ)


def authorize_finance_expense_manage(scope: AccessScope) -> None:
    if Permission.FINANCE_EXPENSE_MANAGE in scope.effective_permissions or Permission.FINANCE_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_EXPENSE_MANAGE)


def authorize_finance_expense_approve(scope: AccessScope) -> None:
    if Permission.FINANCE_EXPENSE_APPROVE in scope.effective_permissions or Permission.FINANCE_ADMIN_APPROVE in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_EXPENSE_APPROVE)


def authorize_finance_tax_read(scope: AccessScope) -> None:
    if Permission.FINANCE_TAX_READ in scope.effective_permissions or Permission.FINANCE_ADMIN_READ in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_TAX_READ)


def authorize_finance_tax_manage(scope: AccessScope) -> None:
    if Permission.FINANCE_TAX_MANAGE in scope.effective_permissions or Permission.FINANCE_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_TAX_MANAGE)


def authorize_finance_tax_approve(scope: AccessScope) -> None:
    if Permission.FINANCE_TAX_APPROVE in scope.effective_permissions or Permission.FINANCE_ADMIN_APPROVE in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_TAX_APPROVE)


def authorize_finance_notify_read(scope: AccessScope) -> None:
    if Permission.FINANCE_NOTIFY_READ in scope.effective_permissions or Permission.FINANCE_DASHBOARD_READ in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_NOTIFY_READ)


def authorize_finance_notify_manage(scope: AccessScope) -> None:
    if Permission.FINANCE_NOTIFY_MANAGE in scope.effective_permissions or Permission.FINANCE_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.FINANCE_NOTIFY_MANAGE)


def authorize_finance_settings_read(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_SETTINGS_READ in scope.effective_permissions
        or Permission.FINANCE_ADMIN_READ in scope.effective_permissions
        or Permission.FINANCE_PAYMENT_CONFIG in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_SETTINGS_READ)


def authorize_finance_settings_manage(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_SETTINGS_MANAGE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_CONFIG in scope.effective_permissions
        or Permission.FINANCE_ADMIN_MANAGE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_SETTINGS_MANAGE)


def authorize_finance_settings_approve(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_SETTINGS_APPROVE in scope.effective_permissions
        or Permission.FINANCE_ADMIN_APPROVE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_SETTINGS_APPROVE)


def authorize_finance_audit_read(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_AUDIT_READ in scope.effective_permissions
        or Permission.TENANT_AUDIT_READ in scope.effective_permissions
        or Permission.FINANCE_ADMIN_READ in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_AUDIT_READ)


def authorize_finance_audit_export(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_AUDIT_EXPORT in scope.effective_permissions
        or Permission.FINANCE_REPORT_EXPORT in scope.effective_permissions
        or Permission.FINANCE_ADMIN_MANAGE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_AUDIT_EXPORT)


def authorize_finance_audit_investigate(scope: AccessScope) -> None:
    if (
        Permission.FINANCE_AUDIT_INVESTIGATE in scope.effective_permissions
        or Permission.FINANCE_AUDIT_READ in scope.effective_permissions
        or Permission.TENANT_AUDIT_READ in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.FINANCE_AUDIT_INVESTIGATE)