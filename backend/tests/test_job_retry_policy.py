"""Background job retry allowlist."""

from app.modules.platform_ops.health_service import SAFE_RETRY_JOB_TYPES


def test_financial_job_types_not_retryable() -> None:
    assert "payment.capture" not in SAFE_RETRY_JOB_TYPES
    assert "notification.send" not in SAFE_RETRY_JOB_TYPES


def test_allowlisted_safe_jobs() -> None:
    assert "erp.jobs.ping" in SAFE_RETRY_JOB_TYPES
    assert "tenant.provisioning" in SAFE_RETRY_JOB_TYPES
