"""Department Admin phase 9 — unit tests (no Mongo)."""

from app.authorization.permissions import Permission, permissions_for_role
from app.common.roles import Role
from app.modules.department_admin.audit_redaction import action_category, redact_audit_metadata
from app.modules.department_admin.document_constants import DOCUMENT_CATEGORIES


def test_department_admin_phase9_permissions():
    perms = permissions_for_role(Role.DEPARTMENT_ADMIN)
    assert Permission.DEPARTMENT_DOCUMENTS_READ in perms
    assert Permission.DEPARTMENT_DOCUMENTS_MANAGE in perms
    assert Permission.DEPARTMENT_AUDIT_READ in perms
    assert Permission.DEPARTMENT_AUDIT_EXPORT in perms


def test_document_categories_allowlist():
    assert "department_administration" in DOCUMENT_CATEGORIES
    assert "reports" in DOCUMENT_CATEGORIES
    assert len(DOCUMENT_CATEGORIES) >= 8


def test_audit_metadata_redaction():
    meta = {"note": "ok", "access_token": "secret", "nested": {"refresh_token": "x"}}
    redacted = redact_audit_metadata(meta)
    assert redacted["access_token"] == "[redacted]"
    assert redacted["nested"]["refresh_token"] == "[redacted]"
    assert redacted["note"] == "ok"


def test_action_category_helper():
    assert action_category("department.document.uploaded") == "document"
    assert action_category("department.request.approved") == "request"
    assert action_category("other") == "other"


def test_department_audit_metadata():
    from beanie import PydanticObjectId

    from app.modules.department_admin.audit_meta import department_audit_metadata

    oid = PydanticObjectId()
    meta = department_audit_metadata(oid, {"report_type": "attendance"})
    assert meta["central_department_id"] == str(oid)
    assert meta["report_type"] == "attendance"