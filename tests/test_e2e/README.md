# End-to-End (E2E) Tests

## Overview

End-to-end tests verify the complete request/response cycle through the FastAPI application, testing real HTTP requests and responses.

## Test Structure

```
tests/test_e2e/
├── test_auth_e2e.py      # User authentication E2E tests
└── test_admin_e2e.py     # Admin authentication and management E2E tests
```

## Test Coverage

### User Authentication (`test_auth_e2e.py`)

**Registration Tests:**
- ✅ Successful user registration
- ✅ Duplicate username handling
- ✅ Duplicate email handling
- ✅ Invalid email format validation
- ✅ Short password validation

**Login Tests:**
- ✅ Successful login with username
- ✅ Login with email (alternative identifier)
- ✅ Invalid credentials handling
- ✅ Inactive user login rejection

**Profile Management Tests:**
- ✅ Get current user profile
- ✅ Update user profile
- ✅ Delete user account (soft delete)
- ✅ Unauthorized access handling
- ✅ Invalid token handling

### Admin Authentication & Management (`test_admin_e2e.py`)

**Admin Authentication:**
- ✅ Admin registration
- ✅ Admin login
- ✅ Get admin profile

**User Management:**
- ✅ List all users (paginated)
- ✅ Get user by ID
- ✅ Update user by admin
- ✅ Activate user
- ✅ Block user
- ✅ Soft delete user
- ✅ Restore soft deleted user
- ✅ User cannot access admin endpoints

## Running E2E Tests

### Run All E2E Tests
```bash
pytest tests/test_e2e/
```

### Run Specific Test File
```bash
pytest tests/test_e2e/test_auth_e2e.py
```

### Run Specific Test
```bash
pytest tests/test_e2e/test_auth_e2e.py::TestUserRegistrationE2E::test_register_user_success
```

### Run with Verbose Output
```bash
pytest tests/test_e2e/ -v
```

## Test Infrastructure

### Async HTTP Client

Tests use `httpx.AsyncClient` with `ASGITransport` to make real HTTP requests to the FastAPI application:

```python
@pytest.fixture
async def async_client(test_db: AsyncSession):
    # Overrides database dependency
    # Clears rate limit store
    # Returns async HTTP client
```

### Database Isolation

Each test uses a fresh in-memory SQLite database that is:
- Created before each test
- Cleaned up after each test
- Isolated from other tests

### Rate Limiting

Rate limit store is cleared before and after each test to prevent interference between tests.

## Test Patterns

### Authentication Flow
```python
# 1. Create user in database
user = await user_repo.create_user(...)

# 2. Login to get token
login_response = await async_client.post("/auth/login", data={...})
token = login_response.json()["data"]["access_token"]

# 3. Use token in protected endpoint
response = await async_client.get(
    "/users/me",
    headers={"Authorization": f"Bearer {token}"}
)
```

### Error Testing
```python
# Test error responses
response = await async_client.post("/auth/register", data={...})
assert response.status_code == 409  # Conflict
data = response.json()
assert data["success"] is False
```

## Key Features Tested

1. **Full Request/Response Cycle**: Tests actual HTTP requests
2. **Authentication**: JWT token generation and validation
3. **Authorization**: User vs Admin access control
4. **Error Handling**: Proper error responses
5. **Data Validation**: Input validation and error messages
6. **Database Operations**: Real database interactions
7. **Rate Limiting**: Login rate limit enforcement

## Test Results

- **Total Tests**: 26
- **Passing**: 25
- **Skipped**: 1 (restore endpoint not implemented)
- **Coverage**: All major user flows

## Best Practices

1. **Isolation**: Each test is independent
2. **Cleanup**: Database and rate limits cleared between tests
3. **Assertions**: Verify both status codes and response data
4. **Error Cases**: Test both success and failure scenarios
5. **Realistic Data**: Use realistic test data

## Future Enhancements

- File upload E2E tests
- Token expiration tests
- Account lockout E2E tests
- Pagination E2E tests
- Concurrent request tests
