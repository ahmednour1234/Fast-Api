# Testing Documentation

## Overview

This project includes comprehensive unit tests for core functionality including security utilities, services, repositories, and utilities.

## Test Structure

```
tests/
├── conftest.py                    # Pytest fixtures and configuration
├── test_security.py               # Security utility tests
├── test_services/                 # Service layer tests
│   └── test_auth_service.py       # Authentication service tests
├── test_repositories/             # Repository layer tests
│   └── test_user_repo.py          # User repository tests
└── test_utils.py                  # Utility function tests
```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run with Verbose Output
```bash
pytest -v
```

### Run Specific Test File
```bash
pytest tests/test_security.py
```

### Run Specific Test Class
```bash
pytest tests/test_security.py::TestPasswordHashing
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

## Test Coverage

### Security Tests (`test_security.py`)

**Password Hashing:**
- ✅ Hash password generation
- ✅ Password verification (correct)
- ✅ Password verification (incorrect)
- ✅ Different hashes for same password (salt)

**JWT Tokens:**
- ✅ Token creation
- ✅ Token decoding (valid)
- ✅ Token decoding (invalid)
- ✅ Token decoding (expired)

**Rate Limiting:**
- ✅ First request allowed
- ✅ Requests within limit
- ✅ Requests exceeding limit blocked

### Service Tests (`test_services/test_auth_service.py`)

**Registration:**
- ✅ Successful registration
- ✅ Username already exists
- ✅ Email already exists

**Login:**
- ✅ Successful login
- ✅ Invalid credentials
- ✅ Wrong password
- ✅ Inactive user

### Repository Tests (`test_repositories/test_user_repo.py`)

**User Operations:**
- ✅ Create user
- ✅ Get by username
- ✅ Get by email
- ✅ Increment failed attempts
- ✅ Account lockout after max attempts
- ✅ Reset failed attempts
- ✅ Soft delete user
- ✅ Exclude deleted users from queries

### Utility Tests (`test_utils.py`)

**File Upload:**
- ✅ Save JPEG image
- ✅ Save PNG image
- ✅ Reject invalid file types
- ✅ Reject files exceeding size limit

## Test Fixtures

### `test_db`
Provides an in-memory SQLite database session for testing:
```python
@pytest.mark.asyncio
async def test_something(test_db):
    # test_db is an AsyncSession
    repo = UserRepository(test_db)
    # ... test code
```

### `mock_db_session`
Provides a mock database session for unit testing:
```python
def test_something(mock_db_session):
    # mock_db_session is an AsyncMock
    service = AuthService(mock_db_session)
    # ... test code
```

### `sample_user_data`
Provides sample user data dictionary:
```python
def test_something(sample_user_data):
    username = sample_user_data["username"]
    # ... test code
```

### `sample_admin_data`
Provides sample admin data dictionary:
```python
def test_something(sample_admin_data):
    # ... test code
```

## Writing New Tests

### Test Naming Convention
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### Example Test
```python
import pytest
from app.services.auth_service import AuthService

class TestAuthService:
    @pytest.mark.asyncio
    async def test_register_success(self, mock_db_session):
        """Test successful user registration."""
        service = AuthService(mock_db_session)
        # ... test implementation
```

### Async Tests
Use `@pytest.mark.asyncio` decorator for async test functions:
```python
@pytest.mark.asyncio
async def test_async_operation(test_db):
    # Async test code
```

## Test Database

Tests use an in-memory SQLite database (`sqlite+aiosqlite:///:memory:`) which:
- Is created fresh for each test
- Is automatically cleaned up after tests
- Doesn't require a running PostgreSQL instance
- Is fast and isolated

## Mocking

For unit tests that don't require database access, use mocks:

```python
from unittest.mock import AsyncMock, MagicMock

def test_with_mocks(mock_db_session):
    # Mock repository methods
    mock_repo = AsyncMock()
    mock_repo.get_by_username = AsyncMock(return_value=None)
    
    # Test service with mocked repository
    service = AuthService(mock_db_session)
    service.user_repo = mock_repo
```

## Continuous Integration

Tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=app --cov-report=xml
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Naming**: Use descriptive test names
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Fixtures**: Use fixtures for common setup
5. **Mocks**: Mock external dependencies
6. **Coverage**: Aim for high code coverage
7. **Speed**: Keep tests fast (use in-memory DB)

## Troubleshooting

### Import Errors
Ensure test dependencies are installed:
```bash
pip install pytest pytest-asyncio pytest-cov aiosqlite
```

### Database Errors
Check that `aiosqlite` is installed for async SQLite support.

### Async Test Issues
Ensure `pytest-asyncio` is installed and configured in `pytest.ini`.

## Future Test Additions

- Integration tests for full request/response cycles
- E2E tests for critical user flows
- Performance tests for rate limiting
- Security tests for authentication flows
