# FastAPI Production Scaffold

A production-ready FastAPI application with PostgreSQL, SQLAlchemy Async, JWT authentication, separate user/admin tables, and comprehensive testing.

## Features

- ✅ **Separate User and Admin Tables**: Clean separation of regular users and administrators
- ✅ **Personal Access Tokens**: Token management system for API access
- ✅ **JWT Authentication**: Secure token-based authentication
- ✅ **Argon2 Password Hashing**: Windows-compatible password security
- ✅ **Rate Limiting**: IP-based rate limiting for login endpoints
- ✅ **Account Lockout**: Automatic lockout after failed login attempts
- ✅ **Soft Delete**: Recoverable user deletion
- ✅ **File Upload**: Image upload with validation
- ✅ **Clean Architecture**: Layered architecture (Routes → Services → Repositories → Models)
- ✅ **Comprehensive Testing**: Unit tests with pytest
- ✅ **Type Hints**: Full type annotation throughout
- ✅ **Error Handling**: Centralized error handling with consistent responses
- ✅ **API Documentation**: Auto-generated Swagger/ReDoc documentation

## Project Structure

```
app/
├── main.py              # FastAPI app entry point
├── core/                # Core utilities and configuration
├── models/              # SQLAlchemy database models
├── schemas/             # Pydantic request/response schemas
├── repositories/        # Data access layer
├── services/            # Business logic layer
├── api/                 # API routes and dependencies
└── utils/               # Utility functions
```

See [CODE_STRUCTURE.md](CODE_STRUCTURE.md) for detailed documentation.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 3. Run Migrations

```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### 4. Seed Database

```bash
python -m app.seed
```

### 5. Run Server

```bash
uvicorn app.main:app --reload
```

## API Endpoints

### User Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login (returns JWT token)

### User Management (Requires Authentication)
- `GET /users/me` - Get my profile
- `PUT /users/me` - Update my profile
- `DELETE /users/me` - Delete my account

### Admin Authentication
- `POST /admin/auth/register` - Register new admin
- `POST /admin/auth/login` - Admin login (returns JWT token)
- `GET /admin/me` - Get admin profile (requires admin token)

### Admin User Management (Requires Admin Token)
- `GET /admin/users` - List all users (paginated)
- `GET /admin/users/{id}` - Get user by ID
- `PUT /admin/users/{id}` - Update user
- `PATCH /admin/users/{id}/activate` - Activate user
- `PATCH /admin/users/{id}/block` - Block user

## Authentication Guide

See [API_AUTHENTICATION_GUIDE.md](API_AUTHENTICATION_GUIDE.md) for detailed instructions on:
- How to login and get tokens
- How to use tokens in requests
- Swagger UI authentication
- Code examples (Python, JavaScript, cURL)

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_services/test_auth_service.py
```

### Test Coverage

View coverage report:
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## Default Credentials

After seeding:

**Admin:**
- Username: `admin`
- Email: `admin@example.com`
- Password: `admin123`

**User:**
- Username: `testuser`
- Email: `user@example.com`
- Password: `user123`

⚠️ **Change default passwords in production!**

## Documentation

- **Code Structure**: [CODE_STRUCTURE.md](CODE_STRUCTURE.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)

## Environment Variables

See `.env.example` for all required variables:

- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT secret key
- `ALGORITHM` - JWT algorithm (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration
- `UPLOAD_DIR` - Upload directory
- `MAX_UPLOAD_MB` - Max file size
- `MAX_LOGIN_ATTEMPTS` - Failed attempts before lockout
- `LOCKOUT_DURATION_MINUTES` - Lockout duration
- `RATE_LIMIT_ATTEMPTS` - Rate limit threshold
- `RATE_LIMIT_WINDOW_MINUTES` - Rate limit window

## Security Features

### Password Security
- Argon2 hashing algorithm
- Automatic salt generation
- Constant-time verification

### JWT Tokens
- HS256 algorithm
- Configurable expiration
- Secure token generation

### Rate Limiting
- IP-based rate limiting
- Configurable thresholds
- Automatic cleanup

### Account Lockout
- Failed attempt tracking
- Automatic lockout
- Time-based unlock

## Database Schema

### Tables

- **users**: Regular user accounts
- **admins**: Administrator accounts
- **personal_access_tokens**: API tokens for users/admins

See [CODE_STRUCTURE.md](CODE_STRUCTURE.md) for detailed schema.

## Development

### Code Style

- Type hints required
- Docstrings for all public methods
- Follow PEP 8
- Use black formatter (optional)

### Adding New Features

1. Create/update model in `app/models/`
2. Create migration: `alembic revision --autogenerate`
3. Create repository in `app/repositories/`
4. Create service in `app/services/`
5. Create route in `app/api/routes/`
6. Add tests in `tests/`
7. Update documentation

## License

MIT