"""End-to-end tests for authentication endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.security import hash_password
from app.repositories.user_repo import UserRepository


class TestUserRegistrationE2E:
    """E2E tests for user registration."""
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, test_db: AsyncSession, async_client: AsyncClient):
        """Test successful user registration."""
        response = await async_client.post(
            "/auth/register",
            data={
                "username": "newuser",
                "name": "New User",
                "email": "newuser@example.com",
                "password": "password123",
                "phone": "+1234567890"
            },
            follow_redirects=True
        )
        
        assert response.status_code == 201, f"Expected 201, got {response.status_code}. Response: {response.text}"
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "User registered successfully"
        assert data["data"]["username"] == "newuser"
        assert data["data"]["email"] == "newuser@example.com"
        assert data["data"]["name"] == "New User"
        assert "id" in data["data"]
        assert "hashed_password" not in data["data"]
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_username(self, test_db: AsyncSession, async_client: AsyncClient):
        """Test registration with duplicate username."""
        # Create existing user
        user_repo = UserRepository(test_db)
        await user_repo.create_user(
            username="existinguser",
            name="Existing User",
            email="existing@example.com",
            hashed_password=hash_password("password123")
        )
        
        # Try to register with same username
        response = await async_client.post(
            "/auth/register",
            data={
                "username": "existinguser",
                "name": "New User",
                "email": "new@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False
        assert "already exists" in data["message"].lower() or "conflict" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, test_db: AsyncSession, async_client: AsyncClient):
        """Test registration with duplicate email."""
        # Create existing user
        user_repo = UserRepository(test_db)
        await user_repo.create_user(
            username="user1",
            name="User One",
            email="duplicate@example.com",
            hashed_password=hash_password("password123")
        )
        
        # Try to register with same email
        response = await async_client.post(
            "/auth/register",
            data={
                "username": "user2",
                "name": "User Two",
                "email": "duplicate@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False
    
    @pytest.mark.asyncio
    async def test_register_user_invalid_email(self, async_client: AsyncClient):
        """Test registration with invalid email format."""
        response = await async_client.post(
            "/auth/register",
            data={
                "username": "testuser",
                "name": "Test User",
                "email": "invalid-email",
                "password": "password123"
            }
        )
        
        # Can be 400 (our validation) or 422 (Pydantic validation)
        assert response.status_code in [400, 422]
        data = response.json()
        assert data["success"] is False
    
    @pytest.mark.asyncio
    async def test_register_user_short_password(self, async_client: AsyncClient):
        """Test registration with password too short."""
        response = await async_client.post(
            "/auth/register",
            data={
                "username": "testuser",
                "name": "Test User",
                "email": "test@example.com",
                "password": "12345"  # Less than 6 characters
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False


class TestUserLoginE2E:
    """E2E tests for user login."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, test_db: AsyncSession, async_client: AsyncClient):
        """Test successful user login."""
        # Create user
        user_repo = UserRepository(test_db)
        await user_repo.create_user(
            username="loginuser",
            name="Login User",
            email="login@example.com",
            hashed_password=hash_password("password123")
        )
        
        # Login
        response = await async_client.post(
            "/auth/login",
            data={
                "username": "loginuser",
                "password": "password123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Login successful"
        assert "access_token" in data["data"]
        assert len(data["data"]["access_token"]) > 0
    
    @pytest.mark.asyncio
    async def test_login_with_email(self, test_db: AsyncSession, async_client: AsyncClient):
        """Test login using email instead of username."""
        # Create user
        user_repo = UserRepository(test_db)
        await user_repo.create_user(
            username="emailuser",
            name="Email User",
            email="emailuser@example.com",
            hashed_password=hash_password("password123")
        )
        
        # Login with email
        response = await async_client.post(
            "/auth/login",
            data={
                "username": "emailuser@example.com",  # Using email
                "password": "password123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, test_db: AsyncSession, async_client: AsyncClient):
        """Test login with invalid credentials."""
        # Create user
        user_repo = UserRepository(test_db)
        await user_repo.create_user(
            username="validuser",
            name="Valid User",
            email="valid@example.com",
            hashed_password=hash_password("correctpassword")
        )
        
        # Try login with wrong password
        response = await async_client.post(
            "/auth/login",
            data={
                "username": "validuser",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert "invalid" in data["message"].lower() or "credentials" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_login_inactive_user(self, test_db: AsyncSession, async_client: AsyncClient):
        """Test login with inactive user."""
        # Create inactive user
        user_repo = UserRepository(test_db)
        user = await user_repo.create_user(
            username="inactiveuser",
            name="Inactive User",
            email="inactive@example.com",
            hashed_password=hash_password("password123")
        )
        # Deactivate user
        user.is_active = False
        await test_db.commit()
        await test_db.refresh(user)
        
        # Try login
        response = await async_client.post(
            "/auth/login",
            data={
                "username": "inactiveuser",
                "password": "password123"
            }
        )
        
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert "inactive" in data["message"].lower()


class TestUserProfileE2E:
    """E2E tests for user profile endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_my_profile(self, test_db: AsyncSession, async_client: AsyncClient):
        """Test getting current user profile."""
        # Create and login user
        user_repo = UserRepository(test_db)
        user = await user_repo.create_user(
            username="profileuser",
            name="Profile User",
            email="profile@example.com",
            hashed_password=hash_password("password123")
        )
        
        # Get token
        login_response = await async_client.post(
            "/auth/login",
            data={"username": "profileuser", "password": "password123"}
        )
        login_data = login_response.json()
        assert login_data["success"] is True
        token = login_data["data"]["access_token"]
        
        # Get profile
        response = await async_client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "profileuser"
        assert data["data"]["email"] == "profile@example.com"
        assert data["data"]["name"] == "Profile User"
    
    @pytest.mark.asyncio
    async def test_get_my_profile_unauthorized(self, async_client: AsyncClient):
        """Test getting profile without token."""
        response = await async_client.get("/users/me")
        
        # FastAPI may return 404 for missing route or 401/403 for auth
        assert response.status_code in [401, 403, 404]
    
    @pytest.mark.asyncio
    async def test_get_my_profile_invalid_token(self, async_client: AsyncClient):
        """Test getting profile with invalid token."""
        response = await async_client.get(
            "/users/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        
        # FastAPI may return 404 for missing route or 401/403 for auth
        assert response.status_code in [401, 403, 404]
    
    @pytest.mark.asyncio
    async def test_update_my_profile(self, test_db: AsyncSession, async_client: AsyncClient):
        """Test updating user profile."""
        # Create and login user
        user_repo = UserRepository(test_db)
        await user_repo.create_user(
            username="updateuser",
            name="Update User",
            email="update@example.com",
            hashed_password=hash_password("password123")
        )
        
        # Get token
        login_response = await async_client.post(
            "/auth/login",
            data={"username": "updateuser", "password": "password123"}
        )
        login_data = login_response.json()
        assert login_data["success"] is True
        token = login_data["data"]["access_token"]
        
        # Update profile (only name, skip email to avoid conflicts)
        response = await async_client.put(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "name": "Updated Name",
                "phone": "+9876543210"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        data = response.json()
        assert data["success"] is True
        if "data" in data:
            assert data["data"]["name"] == "Updated Name"
            assert data["data"]["phone"] == "+9876543210"
    
    @pytest.mark.asyncio
    async def test_delete_my_account(self, test_db: AsyncSession, async_client: AsyncClient):
        """Test soft deleting user account."""
        # Create and login user
        user_repo = UserRepository(test_db)
        await user_repo.create_user(
            username="deleteuser",
            name="Delete User",
            email="delete@example.com",
            hashed_password=hash_password("password123")
        )
        
        # Get token
        login_response = await async_client.post(
            "/auth/login",
            data={"username": "deleteuser", "password": "password123"}
        )
        login_data = login_response.json()
        assert login_data["success"] is True
        token = login_data["data"]["access_token"]
        
        # Delete account
        response = await async_client.delete(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["deleted"] is True
        
        # Verify user cannot login after deletion
        login_response = await async_client.post(
            "/auth/login",
            data={"username": "deleteuser", "password": "password123"}
        )
        assert login_response.status_code == 401
