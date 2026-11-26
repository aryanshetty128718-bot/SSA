import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password

client = TestClient(app)

@pytest.fixture(scope="module")
def user_token():
    from app.core.rate_limiter import login_rate_limiter
    login_rate_limiter.reset()

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

def test_user_history_endpoints(user_token):
    # Fetch history
    resp = client.get("/api/v1/users/history", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

def test_user_saved_products_lifecycle(user_token):
    # Find a valid product ID
    prod_resp = client.get("/api/v1/products/barcode/3017620422003")
    assert prod_resp.status_code == 200
    product_data = prod_resp.json()
    product_id = product_data["product"]["id"] if "product" in product_data else product_data["id"]

    # 1. Add saved product
    save_resp = client.post(
        "/api/v1/users/saved-products",
        json={"product_id": product_id, "notes": "Must buy for breakfast"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert save_resp.status_code == 201
    assert save_resp.json()["product_id"] == product_id

    # 2. List saved products
    list_resp = client.get("/api/v1/users/saved-products", headers={"Authorization": f"Bearer {user_token}"})
    assert list_resp.status_code == 200
    saved_list = list_resp.json()
    assert any(s["product_id"] == product_id for s in saved_list)

    # 3. Delete saved product
    del_resp = client.delete(f"/api/v1/users/saved-products/{product_id}", headers={"Authorization": f"Bearer {user_token}"})
    assert del_resp.status_code == 204

    # 4. Verify removal
    list_resp_after = client.get("/api/v1/users/saved-products", headers={"Authorization": f"Bearer {user_token}"})
    assert not any(s["product_id"] == product_id for s in list_resp_after.json())

