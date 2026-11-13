"""Export tenant isolation rules."""

from app.modules.data_governance.export_service import _validate_export_scope
from app.modules.data_governance.schemas import ExportRequestCreate
from app.modules.data_governance.enums import ExportFormat
from pydantic import ValidationError
import pytest


def test_export_scope_rejects_unknown_modules() -> None:
    payload = ExportRequestCreate(
        module_scopes=["tenant_registry", "unknown_module"],
        formats=[ExportFormat.JSON],
    )
    with pytest.raises(Exception) as exc:
        _validate_export_scope(payload)
    assert "unknown" in str(exc.value).lower() or exc.value.args


def test_export_requires_modules() -> None:
    with pytest.raises(ValidationError):
        ExportRequestCreate(module_scopes=[], formats=[ExportFormat.JSON])
