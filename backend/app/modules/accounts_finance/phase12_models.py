"""Phase 12 finance settings, access scope and audit trace index."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.accounts_finance.phase12_enums import FinanceSettingStatus


class FinanceSettingsRecord(Document):
    """Versioned tenant finance configuration (does not store gateway secrets)."""

    tenant_id: PydanticObjectId
    settings_domain: str
    version_id: str
    status: FinanceSettingStatus = FinanceSettingStatus.DRAFT
    effective_from: date | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    change_note: str | None = None
    created_by: PydanticObjectId
    approved_by: PydanticObjectId | None = None
    superseded_by: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_general_settings"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("settings_domain", ASCENDING), ("version_id", ASCENDING)],
                unique=True,
                name="unique_finance_settings_version",
            ),
            IndexModel([("tenant_id", ASCENDING), ("settings_domain", ASCENDING), ("status", ASCENDING)], name="finance_settings_by_status"),
        ]


class FinanceFeeSettings(FinanceSettingsRecord):
    class Settings:
        name = "finance_fee_settings"


class FinancePaymentSettings(FinanceSettingsRecord):
    class Settings:
        name = "finance_payment_settings"


class FinanceReceiptSettings(FinanceSettingsRecord):
    class Settings:
        name = "finance_receipt_settings"


class FinanceSettingHistory(Document):
    tenant_id: PydanticObjectId
    history_id: str
    settings_domain: str
    version_id: str
    from_status: str | None
    to_status: str
    actor_id: PydanticObjectId | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_setting_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("history_id", ASCENDING)], unique=True, name="unique_finance_setting_hist"),
        ]


class FinanceApprovalWorkflow(Document):
    tenant_id: PydanticObjectId
    workflow_key: str
    label: str
    transaction_category: str
    active_version_id: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_approval_workflows"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("workflow_key", ASCENDING)], unique=True, name="unique_finance_approval_workflow"),
        ]


class FinanceApprovalWorkflowVersion(Document):
    tenant_id: PydanticObjectId
    version_id: str
    workflow_key: str
    status: str = "draft"
    stages: list[dict[str, Any]] = Field(default_factory=list)
    rules: dict[str, Any] = Field(default_factory=dict)
    created_by: PydanticObjectId
    approved_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_approval_workflow_versions"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("version_id", ASCENDING)], unique=True, name="unique_finance_workflow_version"),
        ]


class FinanceAccessAssignment(Document):
    """Scope restrictions for finance users — complements central RBAC role assignment."""

    tenant_id: PydanticObjectId
    assignment_id: str
    user_id: PydanticObjectId
    scope_type: str
    scope_ref: str | None = None
    active: bool = True
    assigned_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_access_assignments"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("assignment_id", ASCENDING)], unique=True, name="unique_finance_access_assignment"),
            IndexModel([("tenant_id", ASCENDING), ("user_id", ASCENDING)], name="finance_access_by_user"),
        ]


class FinanceTemporaryAccessGrant(Document):
    tenant_id: PydanticObjectId
    grant_id: str
    user_id: PydanticObjectId
    permissions: list[str] = Field(default_factory=list)
    valid_from: datetime
    valid_to: datetime
    granted_by: PydanticObjectId
    revoked: bool = False
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_temporary_access_grants"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("grant_id", ASCENDING)], unique=True, name="unique_finance_temp_grant"),
        ]


class FinanceAccessReviewHistory(Document):
    tenant_id: PydanticObjectId
    review_id: str
    user_id: PydanticObjectId
    action: str
    detail: dict[str, Any] = Field(default_factory=dict)
    actor_id: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_access_review_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("review_id", ASCENDING)], unique=True, name="unique_finance_access_review"),
        ]


class FinanceTransactionRelationship(Document):
    """Cross-module traceability index — does not duplicate source financial rows."""

    tenant_id: PydanticObjectId
    relationship_id: str
    link_type: str
    from_type: str
    from_id: str
    to_type: str
    to_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_transaction_relationships"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("relationship_id", ASCENDING)], unique=True, name="unique_finance_tx_rel"),
            IndexModel([("tenant_id", ASCENDING), ("from_type", ASCENDING), ("from_id", ASCENDING)], name="finance_tx_rel_from"),
            IndexModel([("tenant_id", ASCENDING), ("to_type", ASCENDING), ("to_id", ASCENDING)], name="finance_tx_rel_to"),
        ]


class FinanceAuditExportHistory(Document):
    tenant_id: PydanticObjectId
    export_id: str
    export_type: str
    filters: dict[str, Any] = Field(default_factory=dict)
    row_count: int = 0
    actor_id: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_audit_export_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("export_id", ASCENDING)], unique=True, name="unique_finance_audit_export"),
        ]