# Code Structure Documentation

## Overview

This FastAPI project follows a clean, layered architecture pattern with clear separation of concerns. The codebase is organized into distinct layers: API routes, services, repositories, models, and core utilities.

## Project Structure

```
app/
├── main.py                 # FastAPI application entry point
├── core/                   # Core functionality and utilities
│   ├── config.py          # Application settings and configuration
│   ├── database.py        # Database engine and session management
│   ├── security.py        # Password hashing, JWT, rate limiting
│   ├── exceptions.py      # Custom exception classes
│   ├── resources.py       # Standard API response resources
│   └── error_handler.py   # Global error handlers
├── models/                 # SQLAlchemy database models
│   ├── user.py            # User, Admin, PersonalAccessToken models
│   ├── mixins.py          # Reusable model mixins (SoftDeleteMixin)
│   ├── admin.py           # Admin model re-export
│   └── token.py           # Token model re-export
├── schemas/                # Pydantic schemas for request/response validation
│   ├── user.py            # User request/response schemas
│   ├── admin.py           # Admin request/response schemas
│   ├── auth.py            # Authentication schemas
│   └── token.py           # Token schemas
├── repositories/           # Data access layer
│   ├── user_repo.py       # User database operations
│   ├── admin_repo.py      # Admin database operations
│   └── token_repo.py      # Token database operations
├── services/               # Business logic layer
│   ├── auth_service.py    # User authentication logic
│   ├── admin_auth_service.py  # Admin authentication logic
│   ├── user_service.py    # User management logic
│   └── admin_service.py   # Admin management logic
├── api/                    # API layer
│   ├── deps.py            # FastAPI dependencies (guards)
│   └── routes/            # API route handlers
│       ├── auth.py        # User authentication endpoints
│       ├── admin_auth.py  # Admin authentication endpoints
│       ├── users.py       # User management endpoints
│       └── admin.py       # Admin management endpoints
└── utils/                  # Utility functions
    └── upload.py          # File upload utilities
```

## Architecture Layers

### 1. API Layer (`app/api/routes/`)

**Purpose**: Handle HTTP requests and responses, input validation, and route definitions.

**Responsibilities**:
- Define API endpoints
- Validate request data using Pydantic schemas
- Call service layer methods
- Format responses using ResponseResource
- Handle file uploads

**Key Files**:
- `auth.py`: User registration and login
- `admin_auth.py`: Admin registration and login
- `users.py`: User profile management (GET/PUT/DELETE /users/me)
- `admin.py`: Admin user management (list, get, update, activate, block users)

**Example Flow**:
```python
@router.post("/register")
async def register(...):
    # 1. Validate input (automatic via Pydantic)
    # 2. Call service
    user = await auth_service.register(...)
    # 3. Format response
    return ResponseResource.success_response(data=user)
```

### 2. Service Layer (`app/services/`)

**Purpose**: Implement business logic and orchestrate operations.

**Responsibilities**:
- Business rule validation
- Coordinate between repositories
- Handle complex operations
- Raise appropriate exceptions
- Security checks (rate limiting, account lockout)

**Key Services**:

#### AuthService (`auth_service.py`)
- `register()`: Register new user with validation
- `login()`: Authenticate user, handle rate limiting and account lockout

#### UserService (`user_service.py`)
- `get_user_by_id()`: Retrieve user by ID
- `get_all_users()`: List users with pagination
- `update_user()`: Update user data with uniqueness checks
- `activate_user()` / `deactivate_user()`: Toggle user status
- `soft_delete_user()`: Soft delete user account

#### AdminAuthService (`admin_auth_service.py`)
- Similar to AuthService but for admin accounts

#### AdminService (`admin_service.py`)
- Admin-specific management operations

**Example**:
```python
async def register(username, email, password, ...):
    # 1. Check uniqueness
    if await repo.get_by_username(username):
        raise ConflictError("Username exists")
    # 2. Hash password
    hashed = hash_password(password)
    # 3. Create user
    return await repo.create_user(...)
```

### 3. Repository Layer (`app/repositories/`)

**Purpose**: Abstract database operations, provide data access methods.

**Responsibilities**:
- Database queries (CRUD operations)
- Handle soft deletes
- Manage relationships
- Transaction management

**Key Repositories**:

#### UserRepository (`user_repo.py`)
- `get_by_username()`: Find user by username
- `get_by_email()`: Find user by email
- `get_by_phone()`: Find user by phone
- `get_by_id()`: Find user by ID
- `create_user()`: Create new user
- `increment_failed_attempts()`: Track login failures
- `reset_failed_attempts()`: Clear failed attempts
- `soft_delete_user()`: Soft delete user
- `restore_user()`: Restore soft deleted user

**Pattern**:
```python
async def get_by_username(username, include_deleted=False):
    query = select(User).where(User.username == username)
    if not include_deleted:
        query = query.where(User.deleted_at.is_(None))
    result = await self.db.execute(query)
    return result.scalar_one_or_none()
```

### 4. Model Layer (`app/models/`)

**Purpose**: Define database schema and relationships.

**Key Models**:

#### User (`user.py`)
- Regular user accounts
- Fields: id, username, name, email, phone, hashed_password, avatar, is_active, failed_login_attempts, locked_until, created_at, deleted_at
- Relationship: tokens (PersonalAccessToken)

#### Admin (`user.py`)
- Administrator accounts (separate table)
- Same structure as User but in `admins` table
- Relationship: tokens (PersonalAccessToken)

#### PersonalAccessToken (`user.py`)
- Stores API tokens for users and admins
- Fields: id, token, name, user_id, admin_id, last_used_at, expires_at, created_at
- Relationships: user, admin

#### SoftDeleteMixin (`mixins.py`)
- Provides soft delete functionality
- Methods: `soft_delete()`, `restore()`, `is_deleted` property

### 5. Core Layer (`app/core/`)

**Purpose**: Shared utilities and configuration.

#### config.py
- Loads settings from `.env` file
- Configuration: database URL, JWT settings, security settings, upload settings

#### database.py
- SQLAlchemy engine and session management
- `get_db()`: Dependency for database sessions
- `Base`: Declarative base for models

#### security.py
- `hash_password()`: Hash passwords with Argon2
- `verify_password()`: Verify password against hash
- `create_access_token()`: Generate JWT tokens
- `decode_access_token()`: Validate and decode JWT tokens
- `check_rate_limit()`: IP-based rate limiting
- `get_rate_limit_exception()`: Rate limit error

#### exceptions.py
- Custom exception classes:
  - `AppException`: Base exception
  - `NotFoundError`: 404 errors
  - `UnauthorizedError`: 401 errors
  - `ForbiddenError`: 403 errors
  - `ValidationError`: 400 errors
  - `ConflictError`: 409 errors

#### resources.py
- `ResponseResource`: Standard API response format
  - `success_response()`: Success responses
  - `error_response()`: Error responses
  - `list_response()`: List responses with pagination

#### error_handler.py
- Global exception handlers:
  - `app_exception_handler()`: Handle AppException
  - `validation_exception_handler()`: Handle Pydantic validation errors
  - `integrity_error_handler()`: Handle database integrity errors
  - `general_exception_handler()`: Catch-all handler

### 6. Schemas Layer (`app/schemas/`)

**Purpose**: Request/response validation and serialization.

**Key Schemas**:

#### UserResponse (`user.py`)
- User data for API responses
- Excludes sensitive fields (password)

#### UserUpdateRequest (`user.py`)
- Schema for updating user data
- All fields optional

#### AdminResponse (`admin.py`)
- Admin data for API responses

#### TokenResponse (`auth.py`)
- JWT token response format

## Data Flow

### Registration Flow
```
Client Request
    ↓
Route Handler (auth.py)
    ↓ (validates input)
AuthService.register()
    ↓ (checks uniqueness)
UserRepository.create_user()
    ↓ (saves to DB)
ResponseResource.success_response()
    ↓
Client Response
```

### Login Flow
```
Client Request
    ↓
Route Handler (auth.py)
    ↓
AuthService.login()
    ↓ (rate limit check)
    ↓ (find user)
    ↓ (verify password)
    ↓ (check lockout)
    ↓ (reset attempts)
    ↓ (create token)
ResponseResource.success_response()
    ↓
Client Response (JWT token)
```

### Protected Endpoint Flow
```
Client Request (with JWT)
    ↓
get_current_user() dependency
    ↓ (decode token)
    ↓ (find user in DB)
    ↓ (check active)
Route Handler
    ↓
Service Layer
    ↓
Repository Layer
    ↓
Database
```

## Security Features

### 1. Password Security
- **Hashing**: Argon2 algorithm (Windows-compatible)
- **Salt**: Automatic per-password salt
- **Verification**: Constant-time comparison

### 2. JWT Tokens
- **Algorithm**: HS256
- **Expiration**: Configurable (default 60 minutes)
- **Claims**: sub (username), exp, iat

### 3. Rate Limiting
- **Scope**: Per IP address
- **Limit**: 5 attempts per 15 minutes (configurable)
- **Storage**: In-memory dictionary
- **Cleanup**: Automatic expired entry removal

### 4. Account Lockout
- **Threshold**: 5 failed attempts (configurable)
- **Duration**: 30 minutes (configurable)
- **Reset**: Automatic on successful login

### 5. Soft Delete
- **Implementation**: `deleted_at` timestamp
- **Behavior**: Records hidden by default, can be restored
- **Queries**: `include_deleted` parameter to show deleted records

## Error Handling

### Exception Hierarchy
```
AppException (base)
├── NotFoundError (404)
├── UnauthorizedError (401)
├── ForbiddenError (403)
├── ValidationError (400)
└── ConflictError (409)
```

### Response Format
All errors follow consistent format:
```json
{
  "success": false,
  "message": "Error message",
  "error": {
    "code": "ERROR_CODE",
    "message": "Detailed error message",
    "details": {}  // Optional validation details
  }
}
```

## Database Schema

### Tables

#### users
- Primary key: `id`
- Unique indexes: `username`, `email`, `phone`
- Soft delete: `deleted_at`

#### admins
- Primary key: `id`
- Unique indexes: `username`, `email`, `phone`
- Soft delete: `deleted_at`

#### personal_access_tokens
- Primary key: `id`
- Foreign keys: `user_id` → users.id, `admin_id` → admins.id
- Unique index: `token`
- Indexes: `user_id`, `admin_id`, `expires_at`

## Testing

### Test Structure
```
tests/
├── conftest.py           # Pytest fixtures
├── test_security.py      # Security utility tests
├── test_services/        # Service layer tests
│   └── test_auth_service.py
└── test_repositories/    # Repository layer tests
    └── test_user_repo.py
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_services/test_auth_service.py
```

## Best Practices

### 1. Type Hints
- All functions use type hints
- Return types specified
- Optional types for nullable values

### 2. Docstrings
- All classes and methods documented
- Clear descriptions of purpose and parameters

### 3. Error Handling
- Specific exceptions for different error types
- Consistent error response format
- Meaningful error messages

### 4. Code Organization
- Single Responsibility Principle
- Clear separation of concerns
- Reusable components (mixins, utilities)

### 5. Security
- Password hashing (never store plain text)
- JWT token validation
- Rate limiting
- Account lockout
- Input validation

## Configuration

### Environment Variables
See `.env.example` for all required variables:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key
- `ALGORITHM`: JWT algorithm (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration
- `UPLOAD_DIR`: Upload directory path
- `MAX_UPLOAD_MB`: Maximum file size
- `MAX_LOGIN_ATTEMPTS`: Failed attempts before lockout
- `LOCKOUT_DURATION_MINUTES`: Lockout duration
- `RATE_LIMIT_ATTEMPTS`: Rate limit threshold
- `RATE_LIMIT_WINDOW_MINUTES`: Rate limit window

## API Documentation

### Swagger UI
- Available at: `http://localhost:8000/docs`
- Interactive API testing
- Schema validation
- Authentication testing

### ReDoc
- Available at: `http://localhost:8000/redoc`
- Alternative documentation format

## Migration Strategy

### Alembic Migrations
- Location: `alembic/versions/`
- Create: `alembic revision --autogenerate -m "description"`
- Apply: `alembic upgrade head`
- Rollback: `alembic downgrade -1`

## Future Enhancements

1. **Token Management**: Implement PersonalAccessToken usage
2. **Email Verification**: Add email verification flow
3. **Password Reset**: Implement password reset functionality
4. **Two-Factor Authentication**: Add 2FA support
5. **Audit Logging**: Track user actions
6. **Caching**: Add Redis for rate limiting and caching
7. **Background Tasks**: Celery for async tasks
8. **API Versioning**: Version API endpoints
