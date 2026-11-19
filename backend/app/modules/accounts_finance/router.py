"""Accounts / Finance Staff portal."""

from fastapi import APIRouter

from app.modules.accounts_finance.assessment_router import router as assessment_router
from app.modules.accounts_finance.budget_router import router as budget_router
from app.modules.accounts_finance.concession_router import router as concession_router
from app.modules.accounts_finance.dues_router import router as dues_router
from app.modules.accounts_finance.expense_router import router as expense_router
from app.modules.accounts_finance.finance_audit_router import router as finance_audit_router
from app.modules.accounts_finance.finance_notifications_router import router as finance_notifications_router
from app.modules.accounts_finance.finance_settings_router import router as finance_settings_router
from app.modules.accounts_finance.dashboard_router import router as dashboard_router
from app.modules.accounts_finance.fee_category_router import router as fee_category_router
from app.modules.accounts_finance.gl_router import router as gl_router
from app.modules.accounts_finance.fee_structure_router import router as fee_structure_router
from app.modules.accounts_finance.installment_router import router as installment_router
from app.modules.accounts_finance.invoice_router import router as invoice_router
from app.modules.accounts_finance.ledger_router import router as ledger_router
from app.modules.accounts_finance.payment_router import router as payment_router
from app.modules.accounts_finance.period_closing_router import router as period_closing_router
from app.modules.accounts_finance.procurement_router import router as procurement_router
from app.modules.accounts_finance.receipt_router import router as receipt_router
from app.modules.accounts_finance.reconciliation_router import router as reconciliation_router
from app.modules.accounts_finance.reports_router import router as reports_router
from app.modules.accounts_finance.refund_router import router as refund_router
from app.modules.accounts_finance.scholarship_router import router as scholarship_router
from app.modules.accounts_finance.tax_router import router as tax_router

router = APIRouter()
router.include_router(dashboard_router)
router.include_router(fee_category_router)
router.include_router(fee_structure_router)
router.include_router(assessment_router)
router.include_router(invoice_router)
router.include_router(payment_router)
router.include_router(ledger_router)
router.include_router(receipt_router)
router.include_router(scholarship_router)
router.include_router(concession_router)
router.include_router(installment_router)
router.include_router(dues_router)
router.include_router(refund_router)
router.include_router(reconciliation_router)
router.include_router(reports_router)
router.include_router(period_closing_router)
router.include_router(gl_router)
router.include_router(budget_router)
router.include_router(procurement_router)
router.include_router(expense_router)
router.include_router(tax_router)
router.include_router(finance_notifications_router)
router.include_router(finance_settings_router)
router.include_router(finance_audit_router)