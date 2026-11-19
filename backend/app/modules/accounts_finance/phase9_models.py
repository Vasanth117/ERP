"""Phase 9 General Ledger and Finance Budget collections."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.accounts_finance.phase9_enums import FinanceBudgetStatus, JournalSource, JournalStatus


class JournalLineInput(BaseModel):
    account_code: str
    debit: float = Field(default=0, ge=0)
    credit: float = Field(default=0, ge=0)
    department_id: str | None = None
    campus_id: str | None = None
    cost_centre_code: str | None = None
    narration: str | None = None


class ChartOfAccount(Document):
    tenant_id: PydanticObjectId
    account_code: str
    account_name: str
    account_type: str
    classification: str = "other"
    parent_account_code: str | None = None
    account_group: str | None = None
    normal_balance: str
    description: str | None = None
    currency: str = "INR"
    active: bool = True
    effective_from: date | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "chart_of_accounts"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("account_code", ASCENDING)], unique=True, name="unique_coa_code"),
        ]


class AccountGroup(Document):
    tenant_id: PydanticObjectId
    group_code: str
    group_name: str
    parent_group_code: str | None = None
    account_type: str
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "account_groups"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("group_code", ASCENDING)], unique=True, name="unique_account_group"),
        ]


class AccountingDimension(Document):
    tenant_id: PydanticObjectId
    dimension_type: str
    dimension_code: str
    label: str
    reference_id: str | None = None
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "accounting_dimensions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("dimension_type", ASCENDING), ("dimension_code", ASCENDING)],
                unique=True,
                name="unique_accounting_dimension",
            ),
        ]


class AccountingMappingVersion(Document):
    tenant_id: PydanticObjectId
    version_id: str
    label: str
    active: bool = False
    approved_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    activated_at: datetime | None = None

    class Settings:
        name = "accounting_mapping_versions"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("version_id", ASCENDING)], unique=True, name="unique_mapping_version"),
        ]


class AccountingMappingRule(Document):
    tenant_id: PydanticObjectId
    rule_id: str
    version_id: str
    event_type: str
    debit_account_code: str
    credit_account_code: str
    description: str | None = None
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "accounting_mapping_rules"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("rule_id", ASCENDING)], unique=True, name="unique_mapping_rule"),
            IndexModel([("tenant_id", ASCENDING), ("version_id", ASCENDING), ("event_type", ASCENDING)], name="mapping_by_event"),
        ]


class JournalEntry(Document):
    tenant_id: PydanticObjectId
    journal_id: str
    journal_number: str | None = None
    journal_date: date
    financial_period_code: str | None = None
    narration: str
    lines: list[dict[str, Any]] = Field(default_factory=list)
    journal_source: str = JournalSource.MANUAL.value
    source_reference: str | None = None
    posting_key: str | None = None
    status: JournalStatus = JournalStatus.DRAFT
    currency: str = "INR"
    document_refs: list[str] = Field(default_factory=list)
    created_by: PydanticObjectId
    approved_by: PydanticObjectId | None = None
    posted_at: datetime | None = None
    reversal_of_journal_id: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "journal_entries"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("journal_id", ASCENDING)], unique=True, name="unique_journal"),
            IndexModel([("tenant_id", ASCENDING), ("posting_key", ASCENDING)], unique=True, sparse=True, name="unique_journal_posting_key"),
        ]


class JournalEntryLine(Document):
    tenant_id: PydanticObjectId
    line_id: str
    journal_id: str
    account_code: str
    debit: float = Field(ge=0)
    credit: float = Field(ge=0)
    department_id: PydanticObjectId | None = None
    campus_id: PydanticObjectId | None = None
    cost_centre_code: str | None = None
    narration: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "journal_entry_lines"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("line_id", ASCENDING)], unique=True, name="unique_journal_line"),
            IndexModel([("tenant_id", ASCENDING), ("journal_id", ASCENDING)], name="journal_lines_by_journal"),
        ]


class JournalApprovalHistory(Document):
    tenant_id: PydanticObjectId
    history_id: str
    journal_id: str
    from_status: str | None
    to_status: str
    actor_id: PydanticObjectId | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "journal_approval_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("history_id", ASCENDING)], unique=True, name="unique_journal_approval_hist"),
        ]


class GeneralLedgerEntry(Document):
    tenant_id: PydanticObjectId
    gl_entry_id: str
    journal_id: str
    journal_number: str | None = None
    journal_date: date
    financial_period_code: str | None = None
    account_code: str
    debit: float = Field(ge=0)
    credit: float = Field(ge=0)
    source_reference: str | None = None
    department_id: PydanticObjectId | None = None
    campus_id: PydanticObjectId | None = None
    cost_centre_code: str | None = None
    posted_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "general_ledger_entries"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("gl_entry_id", ASCENDING)], unique=True, name="unique_gl_entry"),
            IndexModel([("tenant_id", ASCENDING), ("account_code", ASCENDING), ("journal_date", DESCENDING)], name="gl_by_account_date"),
            IndexModel([("tenant_id", ASCENDING), ("journal_id", ASCENDING)], name="gl_by_journal"),
        ]


class AccountOpeningBalance(Document):
    tenant_id: PydanticObjectId
    balance_id: str
    financial_year_id: str
    account_code: str
    debit: float = Field(ge=0)
    credit: float = Field(ge=0)
    as_of_date: date
    created_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "account_opening_balances"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("financial_year_id", ASCENDING), ("account_code", ASCENDING)],
                unique=True,
                name="unique_opening_balance",
            ),
        ]


class AccountingReversalHistory(Document):
    tenant_id: PydanticObjectId
    reversal_id: str
    original_journal_id: str
    reversal_journal_id: str
    reason: str
    actor_id: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "accounting_reversal_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("reversal_id", ASCENDING)], unique=True, name="unique_gl_reversal"),
        ]


class FinanceBudget(Document):
    tenant_id: PydanticObjectId
    budget_id: str
    budget_code: str
    budget_name: str
    financial_year_id: str
    budget_category: str = "operational"
    department_id: PydanticObjectId | None = None
    campus_id: PydanticObjectId | None = None
    cost_centre_code: str | None = None
    total_amount: float = Field(ge=0)
    currency: str = "INR"
    status: FinanceBudgetStatus = FinanceBudgetStatus.DRAFT
    owner_id: PydanticObjectId | None = None
    justification: str | None = None
    document_refs: list[str] = Field(default_factory=list)
    created_by: PydanticObjectId
    approved_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_budgets"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("budget_id", ASCENDING)], unique=True, name="unique_finance_budget"),
        ]


class FinanceBudgetLine(Document):
    tenant_id: PydanticObjectId
    line_id: str
    budget_id: str
    category: str
    period_code: str | None = None
    amount: float = Field(ge=0)
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_budget_lines"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("line_id", ASCENDING)], unique=True, name="unique_budget_line"),
        ]


class FinanceBudgetAllocation(Document):
    tenant_id: PydanticObjectId
    allocation_id: str
    budget_id: str
    department_id: PydanticObjectId | None = None
    cost_centre_code: str | None = None
    project_code: str | None = None
    allocated_amount: float = Field(ge=0)
    revised_amount: float | None = None
    period_code: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_budget_allocations"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("allocation_id", ASCENDING)], unique=True, name="unique_budget_allocation"),
        ]


class FinanceBudgetRevision(Document):
    tenant_id: PydanticObjectId
    revision_id: str
    budget_id: str
    previous_amount: float
    revised_amount: float
    reason: str
    status: str = "submitted"
    requested_by: PydanticObjectId
    approved_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_budget_revisions"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("revision_id", ASCENDING)], unique=True, name="unique_budget_revision"),
        ]


class FinanceBudgetCommitment(Document):
    tenant_id: PydanticObjectId
    commitment_id: str
    budget_id: str
    allocation_id: str | None = None
    reference_type: str
    reference_id: str
    amount: float = Field(ge=0)
    status: str = "open"
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_budget_commitments"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("commitment_id", ASCENDING)], unique=True, name="unique_budget_commitment"),
            IndexModel(
                [("tenant_id", ASCENDING), ("reference_type", ASCENDING), ("reference_id", ASCENDING)],
                unique=True,
                name="unique_budget_commitment_ref",
            ),
        ]


class FinanceBudgetApprovalHistory(Document):
    tenant_id: PydanticObjectId
    history_id: str
    budget_id: str
    from_status: str | None
    to_status: str
    actor_id: PydanticObjectId | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_budget_approval_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("history_id", ASCENDING)], unique=True, name="unique_budget_approval_hist"),
        ]