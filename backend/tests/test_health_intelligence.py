import pytest
import httpx
from main import app
from auth.security import get_current_user
from database.models import User
from database.database import get_db, SQLALCHEMY_DATABASE_URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

# Use NullPool for isolated testing without connection pooling conflicts
test_engine = create_async_engine(SQLALCHEMY_DATABASE_URL, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)

async def override_get_db():
    async with TestSessionLocal() as session:
        yield session

mock_user_a = User(id="test_user_a_id", email="a@test.com")
mock_user_b = User(id="test_user_b_id", email="b@test.com")

def override_get_current_user_a():
    return mock_user_a

def override_get_current_user_b():
    return mock_user_b

@pytest.fixture(autouse=True)
async def setup_test_environment():
    app.dependency_overrides[get_db] = override_get_db
    async with TestSessionLocal() as session:
        for u in [mock_user_a, mock_user_b]:
            existing = await session.get(User, u.id)
            if not existing:
                session.add(User(id=u.id, email=u.email))
        await session.commit()
    yield
    # Cleanup overrides if needed

@pytest.mark.anyio
async def test_create_and_get_health_profile():
    app.dependency_overrides[get_current_user] = override_get_current_user_a
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.put("/health/profile", json={
            "sex": "female",
            "blood_type": "O+"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["sex"] == "female"
        assert data["blood_type"] == "O+"

        response = await ac.get("/health/profile")
        assert response.status_code == 200
        assert response.json()["sex"] == "female"

@pytest.mark.anyio
async def test_tenant_isolation():
    transport = httpx.ASGITransport(app=app)
    # User A creates condition
    app.dependency_overrides[get_current_user] = override_get_current_user_a
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac_a:
        res_a = await ac_a.post("/health/conditions", json={
            "name": "Asthma",
            "status": "active"
        })
        assert res_a.status_code == 200
        cond_id = res_a.json()["id"]

    # User B should not see it
    app.dependency_overrides[get_current_user] = override_get_current_user_b
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac_b:
        res_b = await ac_b.get("/health/conditions")
        assert res_b.status_code == 200
        conditions = res_b.json()
        assert not any(c["id"] == cond_id for c in conditions)

        res_b_del = await ac_b.delete(f"/health/conditions/{cond_id}")
        assert res_b_del.status_code == 404

@pytest.mark.anyio
async def test_health_summary():
    app.dependency_overrides[get_current_user] = override_get_current_user_a
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health/summary")
        assert response.status_code == 200
        data = response.json()
        assert "profile" in data
        assert "active_conditions_count" in data
