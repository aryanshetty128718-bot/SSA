import pytest
import os
from pydantic import ValidationError
from app.schemas.auth_admin import UserRegister
from app.core.config import Settings

def test_production_secret_key_guard():
    # In production, default insecure SECRET_KEY must raise RuntimeError
    with pytest.raises(RuntimeError) as excinfo:
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="super-secret-key-mca-project-2026"
        )
    assert "CRITICAL SECURITY ERROR" in str(excinfo.value)

def test_production_custom_secret_key_allowed():
    # In production with strong key, it initializes successfully
    s = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="c8f18d7293e54b6ea32f1a08e1c6e43f1b0a8d42a6c8e9f2"
    )
    assert s.SECRET_KEY == "c8f18d7293e54b6ea32f1a08e1c6e43f1b0a8d42a6c8e9f2"

def test_password_policy_enforcement():
    # Reject short password
    with pytest.raises(ValidationError):
        UserRegister(email="user@test.com", full_name="User", password="short")

    # Reject password without digit
    with pytest.raises(ValidationError):
        UserRegister(email="user@test.com", full_name="User", password="NoDigitsAtAllHere")

    # Accept valid strong password
    u = UserRegister(email="user@test.com", full_name="User", password="ValidPass123")
    assert u.password == "ValidPass123"
