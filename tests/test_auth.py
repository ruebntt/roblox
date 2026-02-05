import pytest
from fastapi.testclient import TestClient
from api.main import app
from dependencies import get_db
from unittest.mock import AsyncMock, patch
import sqlalchemy as sa

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

@pytest.fixture(scope="function")
async def mock_db():
    mock_session = AsyncMock()
    mock_session.execute.return_value.scalars.return_value.first.return_value = {
        "id": 1,
        "username": "test_user",
        "is_active": True
    }
    with patch("api.dependencies.get_db", return_value=mock_session):
        yield mock_session

@pytest.mark.asyncio
async def test_successful_authentication(client, mock_db):
    payload = {
        "username": "test_user",
        "password": "correct_password"
    }
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    mock_db.execute.assert_called()
    
@pytest.mark.asyncio
async def test_failed_authentication(client, mock_db):
    mock_db.execute.return_value.scalars.return_value.first.return_value = None
    payload = {
        "username": "nonexistent_user",
        "password": "wrong_password"
    }
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

@pytest.mark.asyncio
async def test_token_expiry(client, mock_db):
    headers = {"Authorization": "Bearer expired_token"}
    response = client.get("/user/me", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Token has expired"
