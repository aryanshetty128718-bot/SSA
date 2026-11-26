import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password

client = TestClient(app)

@pytest.fixture(scope="module")
def admin_token():
    from app.core.rate_limiter import login_rate_limiter
    login_rate_limiter.reset()

    db = SessionLocal()
    admin_user = db.query(User).filter(User.email == "admin@example.com").first()
    if not admin_user:
        admin_user = User(
            email="admin@example.com",
            hashed_password=hash_password("AdminSecretPass2026"),
            full_name="System Administrator",
            role="admin",
            is_active=True
        )
        db.add(admin_user)
        db.commit()
    else:
        admin_user.hashed_password = hash_password("AdminSecretPass2026")
        admin_user.role = "admin"
        db.commit()
    db.close()

    resp = client.post("/api/v1/auth/login", json={
        "email": "admin@example.com",
        "password": "AdminSecretPass2026"
    })
    return resp.json()["access_token"]

@pytest.fixture(scope="module")
def user_token():
    # Ensure test user exists
    db = SessionLocal()
    user = db.query(User).filter(User.email == "test_user_phase6@example.com").first()
    if not user:
        user = User(
            email="test_user_phase6@example.com",
            hashed_password=hash_password("SecurePassword123"),
            full_name="Test User",
            role="user",
            is_active=True
        )
        db.add(user)
        db.commit()
    db.close()

    resp = client.post("/api/v1/auth/login", json={
        "email": "test_user_phase6@example.com",
        "password": "SecurePassword123"
    })
    return resp.json()["access_token"]

def test_admin_route_forbidden_for_regular_user(user_token):
    resp = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 403
    detail = resp.json()["detail"]
    msg = detail if isinstance(detail, str) else detail.get("message", "")
    assert "administrator privileges required" in msg.lower()

def test_admin_system_stats(admin_token):
    resp = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "total_catalog_products" in data
    assert "source_breakdown" in data
    assert "completeness_distribution" in data
    assert data["total_catalog_products"] > 0

def test_admin_product_crud_and_automatic_rescoring(admin_token):
    import uuid
    random_barcode = f"99{uuid.uuid4().int % 100000000000:011d}"
    # 1. Create Product
    create_payload = {
        "barcode": random_barcode,
        "name": "Admin Test Whole Wheat Flakes",
        "brand": "Admin Organics",
        "category_id": 1,
        "serving_size": "45g",
        "origin_country": "India",
        "nutrition": {
            "energy_kcal": 360.0,
            "sugars_g": 4.5,
            "saturated_fat_g": 0.8,
            "sodium_mg": 120.0,
            "fiber_g": 8.0,
            "proteins_g": 11.0
        }
    }
    resp = client.post("/api/v1/admin/products", json=create_payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 201
    prod_id = resp.json()["product_id"]
    initial_score = resp.json()["score"]
    assert initial_score >= 70.0  # Healthy choice

    # 2. Update Product (increases sugar to 28g -> triggers automatic re-scoring with cap)
    update_payload = {
        "nutrition": {
            "sugars_g": 28.0
        }
    }
    up_resp = client.put(f"/api/v1/admin/products/{prod_id}", json=update_payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert up_resp.status_code == 200
    new_score = up_resp.json()["score"]
    assert new_score <= 48.0  # Capped due to red sugar zone

    # 3. Delete Product
    del_resp = client.delete(f"/api/v1/admin/products/{prod_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert del_resp.status_code == 204

def test_admin_scoring_criteria_validation(admin_token):
    # 1. Invalid weights (sum != 1.0)
    bad_payload = {
        "product_type": "solid",
        "parameters": {
            "sugars": {"weight": 0.50, "t_low": 5.0, "t_high": 22.5},
            "sodium": {"weight": 0.20, "t_low": 120.0, "t_high": 600.0}
            # Sum = 0.70 != 1.0
        }
    }
    resp = client.put("/api/v1/admin/scoring-criteria", json=bad_payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 422

    # 2. Invalid thresholds (t_low >= t_high)
    bad_thresh = {
        "product_type": "solid",
        "parameters": {
            "sugars": {"weight": 0.50, "t_low": 25.0, "t_high": 10.0},
            "sodium": {"weight": 0.50, "t_low": 120.0, "t_high": 600.0}
        }
    }
    resp2 = client.put("/api/v1/admin/scoring-criteria", json=bad_thresh, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp2.status_code == 422

def test_admin_audit_logs(admin_token):
    resp = client.get("/api/v1/admin/audit-logs", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    logs = resp.json()
    assert isinstance(logs, list)
    assert len(logs) > 0
    actions = [log["action"] for log in logs]
    assert any(a in ("CREATE", "UPDATE", "DELETE") for a in actions)

