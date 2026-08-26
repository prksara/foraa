import pytest
from fastapi.testclient import TestClient
from main import app
from auth.security import get_current_user
from database.models import User

# Mock users
mock_user_a = User(id="user_a", email="a@test.com")
mock_user_b = User(id="user_b", email="b@test.com")

def override_get_current_user_a():
    return mock_user_a

def override_get_current_user_b():
    return mock_user_b

client = TestClient(app)

def test_create_and_get_health_profile():
    app.dependency_overrides[get_current_user] = override_get_current_user_a
    
    # Create profile
    response = client.put("/health/profile", json={
        "sex": "female",
        "blood_type": "O+"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["sex"] == "female"
    assert data["blood_type"] == "O+"

    # Get profile
    response = client.get("/health/profile")
    assert response.status_code == 200
    assert response.json()["sex"] == "female"

def test_tenant_isolation():
    # User A creates condition
    app.dependency_overrides[get_current_user] = override_get_current_user_a
    res_a = client.post("/health/conditions", json={
        "name": "Asthma",
        "status": "active"
    })
    assert res_a.status_code == 200
    cond_id = res_a.json()["id"]

    # User B should not see it
    app.dependency_overrides[get_current_user] = override_get_current_user_b
    res_b = client.get("/health/conditions")
    assert res_b.status_code == 200
    # Should be empty or not contain Asthma from User A
    conditions = res_b.json()
    assert not any(c["id"] == cond_id for c in conditions)

    # User B cannot delete User A's condition
    res_b_del = client.delete(f"/health/conditions/{cond_id}")
    assert res_b_del.status_code == 404

def test_health_summary():
    app.dependency_overrides[get_current_user] = override_get_current_user_a
    response = client.get("/health/summary")
    assert response.status_code == 200
    data = response.json()
    assert "profile" in data
    assert "active_conditions_count" in data
    assert data["active_conditions_count"] >= 1  # From previous test
