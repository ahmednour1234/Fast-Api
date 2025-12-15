# FastAPI Project - Code Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Directory Structure](#directory-structure)
4. [Core Components](#core-components)
5. [Models](#models)
6. [Repositories](#repositories)
7. [Services](#services)
8. [API Routes](#api-routes)
9. [Security](#security)
10. [Testing](#testing)

---

## Project Overview

This is a production-ready FastAPI application with:
- **Separate User and Admin tables** for role-based access control
- **JWT Authentication** with OAuth2 password flow
- **Personal Access Tokens** table for token management
- **Rate Limiting** and **Account Lockout** security features
- **Clean Architecture** with separation of concerns (MVC pattern)
- **Comprehensive Error Handling** with consistent response format
- **Image Upload** functionality with validation

---

## Architecture

The project follows a **layered architecture** (MVC pattern):

```
┌─────────────────────────────────────┐
│         API Routes (Controllers)    │  ← HTTP Request/Response
├─────────────────────────────────────┤
│         Services (Business Logic)   │  ← Business Rules
├─────────────────────────────────────┤
│      Repositories (Data Access)     │  ← Database Operations
├─────────────────────────────────────┤
│         Models (Database Schema)    │  ← SQLAlchemy ORM
└─────────────────────────────────────┘
```

### Flow:
1. **Request** → API Route receives HTTP request
2. **Validation** → Route validates input using Pydantic schemas
3. **Service** → Business logic is executed in Service layer
4. **Repository** → Data access operations via Repository
5. **Model** → Database operations through SQLAlchemy models
6. **Response** → Consistent ResponseResource format returned

---

## Directory Structure

```
app/
├── main.py                 # FastAPI app initialization, exception handlers, routers
├── core/                   # Core functionality
│   ├── config.py          # Settings from .env file
│   ├── database.py        # Database engine, session, Base class
│   ├── security.py        # Password hashing, JWT, rate limiting
│   ├── exceptions.py      # Custom exception classes
│   ├── resources.py       # Standard API response format
│   └── error_handler.py   # Global exception handlers
├── models/                 # SQLAlchemy ORM models
│   ├── user.py            # User, Admin, PersonalAccessToken models
│   └── mixins.py          # SoftDeleteMixin for soft delete functionality
├── schemas/                # Pydantic models for validation
│   ├── auth.py            # Authentication request/response schemas
│   ├── user.py            # User request/response schemas
│   ├── admin.py           # Admin request/response schemas
│   └── token.py           # Token response schemas
├── repositories/           # Data access layer
│   ├── user_repo.py       # User database operations
│   ├── admin_repo.py       # Admin database operations
│   └── token_repo.py      # Token database operations
├── services/               # Business logic layer
│   ├── auth_service.py    # User authentication logic
│   ├── admin_auth_service.py  # Admin authentication logic
│   ├── user_service.py    # User management logic
│   └── admin_service.py   # Admin management logic
├── api/                    # API layer
│   ├── deps.py            # FastAPI dependencies (guards)
│   └── routes/            # API endpoints
│       ├── auth.py        # User authentication endpoints
│       ├── admin_auth.py  # Admin authentication endpoints
│       ├── users.py       # User management endpoints
│       └── admin.py       # Admin management endpoints
└── utils/                  # Utility functions
    ├── upload.py          # Image upload helper
    └── seed.py            # Database seeder

tests/                      # Unit tests
├── conftest.py            # Pytest fixtures
├── test_repositories.py   # Repository tests
├── test_services.py       # Service tests
├── test_security.py       # Security tests
└── test_utils.py          # Utility tests
```

---

## Core Components

### 1. Configuration (`app/core/config.py`)

Loads settings from `.env` file using `pydantic-settings`:

```python
class Settings(BaseSettings):
    DATABASE_URL: str          # PostgreSQL connection string
    SECRET_KEY: str            # JWT secret key
    ALGORITHM: str = "HS256"   # JWT algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_MB: int = 10
    # Security settings
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    RATE_LIMIT_ATTEMPTS: int = 5
    RATE_LIMIT_WINDOW_MINUTES: int = 15
```

### 2. Database (`app/core/database.py`)

- **Engine**: Async SQLAlchemy engine with asyncpg driver
- **Session**: AsyncSessionLocal for database sessions
- **Base**: DeclarativeBase for all models
- **get_db()**: Dependency for FastAPI to inject database sessions

### 3. Security (`app/core/security.py`)

**Password Hashing:**
- Uses **Argon2** (via passlib) - Windows compatible, secure
- `hash_password()`: Hash plain password
- `verify_password()`: Verify password against hash

**JWT Tokens:**
- `create_access_token()`: Create JWT with username as subject
- `decode_access_token()`: Decode and validate JWT

**Rate Limiting:**
- In-memory storage: `{ip: {count, reset_at}}`
- `check_rate_limit()`: Check if request exceeds limit
- Limits: 5 attempts per 15 minutes per IP

### 4. Exceptions (`app/core/exceptions.py`)

Custom exception classes:
- `AppException`: Base exception
- `NotFoundError`: 404 errors
- `UnauthorizedError`: 401 errors
- `ForbiddenError`: 403 errors
- `ValidationError`: 400 errors
- `ConflictError`: 409 errors

### 5. Resources (`app/core/resources.py`)

Standard API response format:

```python
{
    "success": true/false,
    "message": "Success message",
    "data": {...},      # Response data
    "error": {...}      # Error details (only on errors)
}
```

### 6. Error Handlers (`app/core/error_handler.py`)

Global exception handlers:
- `app_exception_handler`: Handles AppException
- `validation_exception_handler`: Handles Pydantic validation errors
- `integrity_error_handler`: Handles database integrity errors
- `general_exception_handler`: Handles all other exceptions

---

## Models

### User Model (`app/models/user.py`)

**User Table:**
- `id`: Primary key
- `username`: Unique, indexed
- `name`: Full name
- `email`: Unique, indexed
- `phone`: Optional, unique, indexed
- `hashed_password`: Argon2 hash
- `avatar`: Filename string
- `is_active`: Boolean flag
- `failed_login_attempts`: Counter for lockout
- `locked_until`: DateTime for account lockout
- `created_at`: Timestamp
- `deleted_at`: Soft delete timestamp (from SoftDeleteMixin)

**Admin Table:**
- Same structure as User table
- Separate table for administrators
- Independent authentication

**PersonalAccessToken Table:**
- `id`: Primary key
- `token`: Unique token string, indexed
- `name`: Optional token name/description
- `user_id`: Foreign key to users (nullable)
- `admin_id`: Foreign key to admins (nullable)
- `last_used_at`: Last usage timestamp
- `expires_at`: Expiration timestamp, indexed
- `created_at`: Creation timestamp
- Relationships: `user`, `admin`

**SoftDeleteMixin:**
- Provides `deleted_at` field
- `soft_delete()`: Mark as deleted
- `restore()`: Restore deleted record
- `is_deleted`: Property to check deletion status

---

## Repositories

Repositories handle all database operations. They use SQLAlchemy async sessions.

### UserRepository (`app/repositories/user_repo.py`)

**Methods:**
- `get_by_username()`: Get user by username
- `get_by_email()`: Get user by email
- `get_by_username_or_email()`: Get by username or email
- `get_by_phone()`: Get user by phone
- `get_by_id()`: Get user by ID
- `create_user()`: Create new user
- `increment_failed_attempts()`: Increment and lock if threshold reached
- `reset_failed_attempts()`: Reset attempts and unlock
- `lock_account()`: Lock user account
- `unlock_account()`: Unlock user account
- `soft_delete_user()`: Soft delete user
- `restore_user()`: Restore soft deleted user

### AdminRepository (`app/repositories/admin_repo.py`)

Same methods as UserRepository but for Admin model.

### TokenRepository (`app/repositories/token_repo.py`)

**Methods:**
- `create_token()`: Create new personal access token
- `get_by_token()`: Get token by token string
- `get_by_id()`: Get token by ID
- `get_user_tokens()`: Get all tokens for a user
- `get_admin_tokens()`: Get all tokens for an admin
- `update_last_used()`: Update last used timestamp
- `delete_token()`: Delete a token
- `delete_expired_tokens()`: Cleanup expired tokens

---

## Services

Services contain business logic and orchestrate repository calls.

### AuthService (`app/services/auth_service.py`)

**User Authentication:**

1. **register()**:
   - Validates username/email/phone uniqueness
   - Handles avatar upload
   - Hashes password with Argon2
   - Creates user record

2. **login()**:
   - Checks rate limiting
   - Finds user by username or email
   - Checks account lock status
   - Verifies password
   - Increments failed attempts on failure
   - Resets attempts on success
   - Returns JWT token

### AdminAuthService (`app/services/admin_auth_service.py`)

Same logic as AuthService but for Admin model.

### UserService (`app/services/user_service.py`)

**User Management:**

- `get_user_by_id()`: Get user by ID
- `get_all_users()`: Get paginated list of users
- `update_user()`: Update user data with validation
- `activate_user()`: Activate user account
- `deactivate_user()`: Deactivate user account
- `soft_delete_user()`: Soft delete user

### AdminService (`app/services/admin_service.py`)

Same methods as UserService but for Admin model.

---

## API Routes

### User Authentication (`app/api/routes/auth.py`)

**Endpoints:**
- `POST /auth/register`: Register new user
  - Accepts: multipart form (username, name, email, password, phone, avatar)
  - Returns: UserResponse with avatar_url
  
- `POST /auth/login`: User login
  - Accepts: OAuth2PasswordRequestForm (username/email, password)
  - Returns: TokenResponse with access_token

### Admin Authentication (`app/api/routes/admin_auth.py`)

**Endpoints:**
- `POST /admin/auth/register`: Register new admin
- `POST /admin/auth/login`: Admin login

### User Management (`app/api/routes/users.py`)

**Endpoints (Protected - requires authentication):**
- `GET /users/me`: Get current user profile
- `PUT /users/me`: Update current user profile
- `DELETE /users/me`: Delete current user account (soft delete)

### Admin Management (`app/api/routes/admin.py`)

**Endpoints (Protected - requires admin authentication):**
- `GET /admin/me`: Get admin profile
- `GET /admin/users`: List all users (paginated)
- `GET /admin/users/{user_id}`: Get user by ID
- `PUT /admin/users/{user_id}`: Update user
- `PATCH /admin/users/{user_id}/activate`: Activate user
- `PATCH /admin/users/{user_id}/block`: Block user

---

## Security

### Authentication Flow

1. **User Registration:**
   ```
   POST /auth/register
   → Validate email format
   → Check uniqueness (username, email, phone)
   → Hash password (Argon2)
   → Save avatar if provided
   → Create user record
   → Return user data
   ```

2. **User Login:**
   ```
   POST /auth/login
   → Check rate limiting (5 per 15 min per IP)
   → Find user by username/email
   → Check account lock status
   → Verify password
   → Increment failed attempts on failure
   → Reset attempts on success
   → Generate JWT token
   → Return token
   ```

3. **Protected Endpoints:**
   ```
   GET /users/me (with Bearer token)
   → Extract token from Authorization header
   → Decode JWT
   → Get username from token
   → Load user from database
   → Check user is active
   → Return user data
   ```

### Security Features

1. **Rate Limiting:**
   - 5 login attempts per 15 minutes per IP
   - In-memory storage (use Redis in production)
   - Returns 429 Too Many Requests

2. **Account Lockout:**
   - 5 failed attempts = 30 minute lockout
   - Tracks `failed_login_attempts` and `locked_until`
   - Returns 423 Locked status

3. **Password Security:**
   - Argon2 hashing (resistant to GPU attacks)
   - No plain text passwords stored
   - Timing attack protection (delays on failed login)

4. **JWT Tokens:**
   - HS256 algorithm
   - Contains: `sub` (username), `exp` (expiration), `iat` (issued at)
   - Configurable expiration (default: 60 minutes)

5. **Input Validation:**
   - Email format validation (Pydantic EmailStr)
   - Password minimum length (6 characters)
   - File type validation (jpeg, png, webp only)
   - File size limits (configurable)

---

## Testing

### Test Structure

Tests are located in `tests/` directory:

- `conftest.py`: Pytest fixtures (db_session, test_user, test_admin)
- `test_repositories.py`: Repository layer tests
- `test_services.py`: Service layer tests
- `test_security.py`: Security function tests
- `test_utils.py`: Utility function tests

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_services.py

# Run with verbose output
pytest -v
```

### Test Database

Tests use **SQLite in-memory database** for speed:
- Created fresh for each test
- No external database required
- Fast test execution

---

## Code Quality & Best Practices

### 1. Type Hints
- All functions have type hints
- Uses `typing.Optional`, `typing.List`, etc.
- SQLAlchemy Mapped types for model fields

### 2. Error Handling
- Custom exceptions for different error types
- Consistent error response format
- Global exception handlers

### 3. Code Organization
- Single Responsibility Principle
- Separation of concerns (Routes → Services → Repositories)
- DRY (Don't Repeat Yourself)

### 4. Security
- Password hashing with Argon2
- JWT token authentication
- Rate limiting
- Account lockout
- Input validation

### 5. Documentation
- Docstrings for all functions
- Type hints for clarity
- Clear variable names

---

## Environment Variables

Required `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
UPLOAD_DIR=uploads
MAX_UPLOAD_MB=10
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30
RATE_LIMIT_ATTEMPTS=5
RATE_LIMIT_WINDOW_MINUTES=15
```

---

## Database Migrations

Using Alembic for database migrations:

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Seed database
python -m app.seed

# Start server
uvicorn app.main:app --reload
```

---

## API Response Format

All endpoints return consistent format:

**Success:**
```json
{
    "success": true,
    "message": "Operation successful",
    "data": {
        // Response data
    }
}
```

**Error:**
```json
{
    "success": false,
    "message": "Error message",
    "error": {
        "code": "ERROR_CODE",
        "message": "Detailed error message",
        "details": {}  // Optional
    }
}
```

---

## Future Improvements

1. **Redis for Rate Limiting**: Replace in-memory storage
2. **Refresh Tokens**: Implement token refresh mechanism
3. **Email Verification**: Add email verification flow
4. **Password Reset**: Implement password reset functionality
5. **Logging**: Add structured logging
6. **Monitoring**: Add health checks and metrics
7. **Caching**: Implement caching layer
8. **Background Tasks**: Add Celery for async tasks

---

## License

MIT License
