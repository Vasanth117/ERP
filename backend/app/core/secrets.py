"""Secret reference storage (no plaintext secrets in MongoDB)."""

import os
import re
from typing import Literal

SecretBackend = Literal["env", "vault"]

_REFERENCE_PATTERN = re.compile(r"^(env|vault)://[A-Za-z0-9_./:-]+$")


class SecretReference:
    """Pointer to a secret in env or external vault — never the secret value."""

    def __init__(self, reference: str) -> None:
        if not _REFERENCE_PATTERN.match(reference):
            raise ValueError("Invalid secret reference format")
        self.reference = reference
        self.backend: SecretBackend = reference.split("://", 1)[0]  # type: ignore[assignment]

    def resolve(self) -> str:
        if self.backend == "env":
            key = self.reference.split("://", 1)[1]
            value = os.environ.get(key)
            if not value:
                raise RuntimeError(f"Secret not available for reference {self.reference}")
            return value
        raise RuntimeError("Vault backend is not configured in this environment")


def assert_secret_reference(reference: str) -> str:
    SecretReference(reference)
    return reference


def redact_for_response(reference: str) -> dict[str, str]:
    return {"secret_ref": reference, "backend": reference.split("://", 1)[0]}
