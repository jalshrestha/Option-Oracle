"""
Integration tests for auth routes.

Covers:
  POST /api/v1/auth/register  — happy path, duplicate email, duplicate username, validation
  POST /api/v1/auth/login     — happy path, wrong password, missing user, inactive user,
                                no user-enumeration (same error message both ways)
  POST /api/v1/auth/refresh   — happy path, access-token-as-refresh, invalid token,
                                expired token, inactive user, deleted user
  POST /api/v1/auth/logout    — 200 message (stateless)
  GET  /api/v1/auth/me        — happy path, no token, invalid token,
                                refresh-token-as-access, inactive user

All DB calls are mocked via `dependency_overrides[get_db]` + `patch` on UserRepository
so no live database is required.
"""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from jose import jwt

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_EMAIL = "test@example.com"
VALID_USERNAME = "testuser"
VALID_PASSWORD = "Secure123!"

# Must match conftest.py env stub
TEST_JWT_SECRET = "test-jwt-secret-key-for-ci-testing-only-32plus"


# ---------------------------------------------------------------------------
# Helper builders
# ---------------------------------------------------------------------------

def _make_user(
    email: str = VALID_EMAIL,
    username: str = VALID_USERNAME,
    is_active: bool = True,
    is_verified: bool = False,
    risk_profile: str = "moderate",
) -> MagicMock:
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = email
    user.username = username
    user.hashed_password = "hashed_pw"
    user.is_active = is_active
    user.is_verified = is_verified
    user.risk_profile = risk_profile
    return user


def _mock_repo(
    by_email=None,
    by_username=None,
    created_user=None,
    by_id=None,
) -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_email.return_value = by_email
    repo.get_by_username.return_value = by_username
    repo.create.return_value = created_user if created_user is not None else _make_user()
    repo.get_by_id.return_value = by_id
    return repo


def _make_access_token(user_id: str, email: str) -> str:
    from src.auth.jwt import create_access_token
    return create_access_token(user_id, email)


def _make_refresh_token(user_id: str) -> str:
    from src.auth.jwt import create_refresh_token
    return create_refresh_token(user_id)


# ---------------------------------------------------------------------------
# Fixture — client with DB dependency overridden
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def auth_client() -> AsyncClient:
    from src.api.main import create_app
    from src.api.dependencies import get_db

    app = create_app()
    mock_session = AsyncMock()

    async def _mock_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = _mock_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

class TestRegister:
    """POST /api/v1/auth/register"""

    @pytest.mark.asyncio
    async def test_happy_path_returns_201_with_tokens(self, auth_client):
        user = _make_user()
        with patch("src.api.routes.auth.UserRepository") as MockRepo:
            MockRepo.return_value = _mock_repo(created_user=user)
            resp = await auth_client.post(
                "/api/v1/auth/register",
                json={
                    "email": VALID_EMAIL,
                    "username": VALID_USERNAME,
                    "password": VALID_PASSWORD,
                },
            )
        assert resp.status_code == 201
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_access_token_is_valid_jwt_with_correct_claims(self, auth_client):
        user = _make_user()
        with patch("src.api.routes.auth.UserRepository") as MockRepo:
            MockRepo.return_value = _mock_repo(created_user=user)
            resp = await auth_client.post(
                "/api/v1/auth/register",
                json={
                    "email": VALID_EMAIL,
                    "username": VALID_USERNAME,
                    "password": VALID_PASSWORD,
                },
            )
        token = resp.json()["access_token"]
        payload = jwt.decode(token, TEST_JWT_SECRET, algorithms=["HS256"])
        assert payload["type"] == "access"
        assert payload["email"] == VALID_EMAIL
        assert payload["sub"] == str(user.id)

    @pytest.mark.asyncio
    async def test_duplicate_email_returns_409(self, auth_client):
        existing = _make_user()
        with patch("src.api.routes.auth.UserRepository") as MockRepo:
            MockRepo.return_value = _mock_repo(by_email=existing)
            resp = await auth_client.post(
                "/api/v1/auth/register",
                json={
                    "email": VALID_EMAIL,
                    "username": "newuser",
                    "password": VALID_PASSWORD,
                },
            )
        assert resp.status_code == 409
        assert "Email" in resp.json()["error"]

    @pytest.mark.asyncio
    async def test_duplicate_username_returns_409(self, auth_client):
        existing = _make_user()
        with patch("src.api.routes.auth.UserRepository") as MockRepo:
            MockRepo.return_value = _mock_repo(by_email=None, by_username=existing)
            resp = await auth_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "fresh@example.com",
                    "username": VALID_USERNAME,
                    "password": VALID_PASSWORD,
                },
            )
        assert resp.status_code == 409
        assert "Username" in resp.json()["error"]

    @pytest.mark.asyncio
    async def test_password_too_short_returns_422(self, auth_client):
        resp = await auth_client.post(
            "/api/v1/auth/register",
            json={"email": VALID_EMAIL, "username": VALID_USERNAME, "password": "short"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_email_format_returns_422(self, auth_client):
        resp = await auth_client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "username": VALID_USERNAME,
                "password": VALID_PASSWORD,
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_fields_returns_422(self, auth_client):
        resp = await auth_client.post(
            "/api/v1/auth/register",
            json={"email": VALID_EMAIL},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestLogin:
    """POST /api/v1/auth/login"""

    @pytest.mark.asyncio
    async def test_happy_path_returns_200_with_tokens(self, auth_client):
        user = _make_user()
        with (
            patch("src.api.routes.auth.UserRepository") as MockRepo,
            patch("src.api.routes.auth.verify_password", return_value=True),
        ):
            MockRepo.return_value = _mock_repo(by_email=user)
            resp = await auth_client.post(
                "/api/v1/auth/login",
                json={"email": VALID_EMAIL, "password": VALID_PASSWORD},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body

    @pytest.mark.asyncio
    async def test_wrong_password_returns_401(self, auth_client):
        user = _make_user()
        with (
            patch("src.api.routes.auth.UserRepository") as MockRepo,
            patch("src.api.routes.auth.verify_password", return_value=False),
        ):
            MockRepo.return_value = _mock_repo(by_email=user)
            resp = await auth_client.post(
                "/api/v1/auth/login",
                json={"email": VALID_EMAIL, "password": "WrongPass!"},
            )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_nonexistent_email_returns_401(self, auth_client):
        with patch("src.api.routes.auth.UserRepository") as MockRepo:
            MockRepo.return_value = _mock_repo(by_email=None)
            resp = await auth_client.post(
                "/api/v1/auth/login",
                json={"email": "ghost@example.com", "password": VALID_PASSWORD},
            )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_no_user_enumeration_same_detail_for_wrong_pw_and_missing_user(
        self, auth_client
    ):
        """Wrong password and missing user must return the exact same error message."""
        user = _make_user()

        with (
            patch("src.api.routes.auth.UserRepository") as MockRepo,
            patch("src.api.routes.auth.verify_password", return_value=False),
        ):
            MockRepo.return_value = _mock_repo(by_email=user)
            r_wrong_pw = await auth_client.post(
                "/api/v1/auth/login",
                json={"email": VALID_EMAIL, "password": "Wrong!"},
            )

        with patch("src.api.routes.auth.UserRepository") as MockRepo:
            MockRepo.return_value = _mock_repo(by_email=None)
            r_no_user = await auth_client.post(
                "/api/v1/auth/login",
                json={"email": "ghost@example.com", "password": VALID_PASSWORD},
            )

        assert r_wrong_pw.json()["error"] == r_no_user.json()["error"]

    @pytest.mark.asyncio
    async def test_inactive_user_returns_401(self, auth_client):
        inactive = _make_user(is_active=False)
        with (
            patch("src.api.routes.auth.UserRepository") as MockRepo,
            patch("src.api.routes.auth.verify_password", return_value=True),
        ):
            MockRepo.return_value = _mock_repo(by_email=inactive)
            resp = await auth_client.post(
                "/api/v1/auth/login",
                json={"email": VALID_EMAIL, "password": VALID_PASSWORD},
            )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------

class TestRefresh:
    """POST /api/v1/auth/refresh"""

    @pytest.mark.asyncio
    async def test_happy_path_returns_new_access_token_same_refresh(self, auth_client):
        user = _make_user()
        token = _make_refresh_token(str(user.id))
        with patch("src.api.routes.auth.UserRepository") as MockRepo:
            MockRepo.return_value = _mock_repo(by_id=user)
            resp = await auth_client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": token},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        # Existing refresh token is echoed back unchanged
        assert body["refresh_token"] == token

    @pytest.mark.asyncio
    async def test_new_access_token_has_correct_claims(self, auth_client):
        user = _make_user()
        token = _make_refresh_token(str(user.id))
        with patch("src.api.routes.auth.UserRepository") as MockRepo:
            MockRepo.return_value = _mock_repo(by_id=user)
            resp = await auth_client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": token},
            )
        access = resp.json()["access_token"]
        payload = jwt.decode(access, TEST_JWT_SECRET, algorithms=["HS256"])
        assert payload["type"] == "access"
        assert payload["sub"] == str(user.id)

    @pytest.mark.asyncio
    async def test_access_token_used_as_refresh_returns_401(self, auth_client):
        user = _make_user()
        wrong_token = _make_access_token(str(user.id), user.email)
        resp = await auth_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": wrong_token},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self, auth_client):
        resp = await auth_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "not.a.valid.token"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_expired_token_returns_401(self, auth_client):
        user_id = str(uuid.uuid4())
        expired_payload = {
            "sub": user_id,
            "type": "refresh",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        }
        expired = jwt.encode(expired_payload, TEST_JWT_SECRET, algorithm="HS256")
        resp = await auth_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": expired},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_inactive_user_returns_401(self, auth_client):
        user = _make_user(is_active=False)
        token = _make_refresh_token(str(user.id))
        with patch("src.api.routes.auth.UserRepository") as MockRepo:
            MockRepo.return_value = _mock_repo(by_id=user)
            resp = await auth_client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": token},
            )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_deleted_user_returns_401(self, auth_client):
        """User deleted between token issue and refresh — repo returns None."""
        user_id = str(uuid.uuid4())
        token = _make_refresh_token(user_id)
        with patch("src.api.routes.auth.UserRepository") as MockRepo:
            MockRepo.return_value = _mock_repo(by_id=None)
            resp = await auth_client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": token},
            )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

class TestLogout:
    """POST /api/v1/auth/logout"""

    @pytest.mark.asyncio
    async def test_returns_200_with_message(self, auth_client):
        resp = await auth_client.post("/api/v1/auth/logout")
        assert resp.status_code == 200
        assert "message" in resp.json()


# ---------------------------------------------------------------------------
# Me
# ---------------------------------------------------------------------------

class TestMe:
    """GET /api/v1/auth/me"""

    @pytest.mark.asyncio
    async def test_happy_path_returns_user_profile(self, auth_client):
        user = _make_user()
        token = _make_access_token(str(user.id), user.email)
        with patch("src.api.routes.auth.UserRepository") as MockRepo:
            MockRepo.return_value = _mock_repo(by_id=user)
            resp = await auth_client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == VALID_EMAIL
        assert body["username"] == VALID_USERNAME
        assert body["id"] == str(user.id)
        assert "risk_profile" in body
        assert "is_verified" in body

    @pytest.mark.asyncio
    async def test_no_token_returns_401(self, auth_client):
        resp = await auth_client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_malformed_token_returns_401(self, auth_client):
        resp = await auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not.a.real.token"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token_as_bearer_returns_401(self, auth_client):
        """Refresh tokens must not grant access to /me."""
        user = _make_user()
        token = _make_refresh_token(str(user.id))
        resp = await auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_inactive_user_returns_401(self, auth_client):
        user = _make_user(is_active=False)
        token = _make_access_token(str(user.id), user.email)
        with patch("src.api.routes.auth.UserRepository") as MockRepo:
            MockRepo.return_value = _mock_repo(by_id=user)
            resp = await auth_client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_bearer_prefix_returns_401(self, auth_client):
        user = _make_user()
        token = _make_access_token(str(user.id), user.email)
        resp = await auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": token},  # missing "Bearer " prefix
        )
        assert resp.status_code == 401
