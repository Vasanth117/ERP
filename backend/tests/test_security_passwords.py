"""Password hashing tests."""

from app.core.security import hash_password, password_needs_upgrade, verify_password


def test_argon2_hash_and_verify() -> None:
    hashed = hash_password("StrongPass123!")
    assert verify_password("StrongPass123!", hashed)
    assert not verify_password("wrong", hashed)
    assert not password_needs_upgrade(hashed)
