import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from datetime import timedelta

client = TestClient(app)

def test_user_registration_success():
    import uuid
    random_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "email": random_email,
        "full_name": "Test User",
        "password": "SecurePassword123"
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == payload["email"]
    assert data["role"] == "user"
    assert "hashed_password" not in data

def test_user_registration_validation_weak_password():
    payload = {
        "email": "weak@example.com",
        "full_name": "Weak User",
        "password": "short"  # < 8 chars and no digit
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 422

def test_user_registration_duplicate_email():
    payload = {
        "email": "test_user_phase6@example.com",
        "full_name": "Duplicate User",
        "password": "SecurePassword123"
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 400
    detail = resp.json()["detail"]
    msg = detail if isinstance(detail, str) else detail.get("message", "")
    assert "already exists" in msg.lower()

def test_login_success():
    resp = client.post("/api/v1/auth/login", json={
        "email": "test_user_phase6@example.com",
        "password": "SecurePassword123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test_user_phase6@example.com"

def test_login_invalid_password():
    resp = client.post("/api/v1/auth/login", json={
        "email": "test_user_phase6@example.com",
        "password": "WrongPassword999"
    })
    assert resp.status_code == 401
    detail = resp.json()["detail"]
    msg = detail if isinstance(detail, str) else detail.get("message", "")
    assert "invalid" in msg.lower()

def test_login_nonexistent_user():
    resp = client.post("/api/v1/auth/login", json={
        "email": "nonexistent_random_12345@example.com",
        "password": "Password123"
    })
    assert resp.status_code == 401

def test_auth_me_with_valid_token():
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "test_user_phase6@example.com",
        "password": "SecurePassword123"
    })
    token = login_resp.json()["access_token"]
    
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "test_user_phase6@example.com"

def test_auth_me_with_expired_token():
    # Expired token (-10 minutes)
    expired_token = create_access_token(
        data={"sub": "any-id", "email": "test_user_phase6@example.com", "role": "user"},
        expires_delta=timedelta(minutes=-10)
    )
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401
    detail = resp.json()["detail"]
    msg = detail if isinstance(detail, str) else detail.get("message", "")
    assert "invalid or expired" in msg.lower()

def test_auth_me_without_token():
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401

