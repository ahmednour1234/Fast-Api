# Architecture Documentation

## System Architecture

This document describes the high-level architecture and design decisions of the FastAPI application.

## Design Patterns

### 1. Layered Architecture

The application follows a strict layered architecture:

```
┌─────────────────────────────────────┐
│         API Layer (Routes)         │  ← HTTP Request/Response
├─────────────────────────────────────┤
│        Service Layer                │  ← Business Logic
├─────────────────────────────────────┤
│      Repository Layer               │  ← Data Access
├─────────────────────────────────────┤
│         Model Layer                 │  ← Database Schema
└─────────────────────────────────────┘
```

**Benefits**:
- Clear separation of concerns
- Easy to test each layer independently
- Maintainable and scalable
- Follows SOLID principles

### 2. Dependency Injection

FastAPI's dependency injection system is used throughout:

```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    # Dependencies automatically injected
```

**Benefits**:
- Loose coupling
- Easy to mock for testing
- Automatic dependency resolution

### 3. Repository Pattern

Data access is abstracted through repositories:

```python
class UserRepository:
    async def get_by_username(self, username: str) -> Optional[User]:
        # Database query logic
```

**Benefits**:
- Database-agnostic business logic
- Easy to swap database implementations
- Centralized query logic

### 4. Service Pattern

Business logic is encapsulated in services:

```python
class AuthService:
    async def register(self, ...) -> User:
        # Business rules and validation
```

**Benefits**:
- Reusable business logic
- Testable without HTTP layer
- Clear business rules

## Security Architecture

### Authentication Flow

```
┌─────────┐
│ Client  │
└────┬────┘
     │ 1. POST /auth/login (username, password)
     ▼
┌─────────────────┐
│  AuthService    │
│  - Rate Limit   │
│  - Find User    │
│  - Verify Pass │
│  - Check Lock  │
└────┬────────────┘
     │ 2. Generate JWT
     ▼
┌─────────┐
│ Client  │ (receives token)
└────┬────┘
     │ 3. Request with Bearer token
     ▼
┌─────────────────┐
│ get_current_user│
│  - Decode JWT   │
│  - Find User    │
│  - Check Active │
└────┬────────────┘
     │ 4. User object
     ▼
┌─────────┐
│ Handler │
└─────────┘
```

### Authorization

**User Guard** (`get_current_user`):
- Validates JWT token
- Loads user from database
- Checks if user is active
- Returns User object

**Admin Guard** (`get_current_admin`):
- Validates JWT token
- Loads admin from database
- Checks if admin is active
- Returns Admin object

## Database Design

### Entity Relationship

```
┌─────────────┐         ┌──────────────────────┐
│    User     │────────▶│ PersonalAccessToken  │
└─────────────┘         └──────────────────────┘
     │                           ▲
     │                           │
     │                           │
┌─────────────┐                  │
│    Admin    │──────────────────┘
└─────────────┘
```

### Table Relationships

- **User → PersonalAccessToken**: One-to-Many (CASCADE delete)
- **Admin → PersonalAccessToken**: One-to-Many (CASCADE delete)
- **PersonalAccessToken**: Can belong to either User or Admin (not both)

## Error Handling Strategy

### Exception Flow

```
Route Handler
    ↓ (raises exception)
Service Layer
    ↓ (raises AppException)
Global Exception Handler
    ↓ (catches exception)
ResponseResource.error_response()
    ↓
JSON Response to Client
```

### Exception Types

1. **NotFoundError** (404): Resource not found
2. **UnauthorizedError** (401): Authentication failed
3. **ForbiddenError** (403): Insufficient permissions
4. **ValidationError** (400): Invalid input data
5. **ConflictError** (409): Resource conflict (duplicate)

## Response Format

### Success Response
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    // Response data
  }
}
```

### Error Response
```json
{
  "success": false,
  "message": "Error message",
  "error": {
    "code": "ERROR_CODE",
    "message": "Detailed message",
    "details": {}  // Optional
  }
}
```

### List Response
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "items": [...],
    "count": 10,
    "total": 100
  }
}
```

## Rate Limiting Architecture

### In-Memory Storage

```
{
  "IP_ADDRESS": {
    "count": 3,
    "reset_at": "2025-12-15T10:30:00"
  }
}
```

### Flow

1. Check IP in storage
2. If exists and not expired: increment count
3. If count >= limit: return False
4. If expired: reset count and window
5. Cleanup expired entries periodically

## Account Lockout Architecture

### State Machine

```
Active → Failed Attempts → Locked → Active
  ↑                              ↓
  └────────── Reset on Success ───┘
```

### Implementation

- Track `failed_login_attempts` in database
- Set `locked_until` when threshold reached
- Check `locked_until > now()` before login
- Reset on successful login

## File Upload Architecture

### Flow

```
Client Upload
    ↓
Route Handler (receives UploadFile)
    ↓
save_image() utility
    ↓ (validates type & size)
    ↓ (generates UUID filename)
    ↓ (saves to UPLOAD_DIR)
    ↓
Returns filename
    ↓
Stored in database
    ↓
Served via /uploads/<filename>
```

### Validation

- **Content Types**: image/jpeg, image/png, image/webp
- **Size Limit**: Configurable (default 10MB)
- **Filename**: UUID-based to prevent conflicts

## Testing Strategy

### Test Pyramid

```
        ┌─────┐
       / E2E  \      (Few)
      └───────┘
     ┌─────────┐
    /Integration\   (Some)
   └───────────┘
  ┌─────────────┐
 /   Unit Tests  \  (Many)
└───────────────┘
```

### Test Types

1. **Unit Tests**: Test individual functions/classes
   - Services
   - Repositories
   - Utilities

2. **Integration Tests**: Test component interactions
   - Service + Repository
   - Route + Service

3. **E2E Tests**: Test full flows
   - Registration → Login → Protected endpoint

## Performance Considerations

### Database

- **Indexes**: On frequently queried fields (username, email, phone)
- **Async Operations**: All database operations are async
- **Connection Pooling**: Managed by SQLAlchemy

### Caching (Future)

- Rate limit data (currently in-memory)
- User lookups (could use Redis)
- Token validation (could cache decoded tokens)

## Scalability

### Horizontal Scaling

- **Stateless API**: Can run multiple instances
- **Database**: Shared PostgreSQL instance
- **Rate Limiting**: Currently in-memory (needs Redis for multi-instance)

### Vertical Scaling

- **Async Operations**: Non-blocking I/O
- **Connection Pooling**: Efficient database connections
- **Background Tasks**: Can offload heavy operations

## Deployment Considerations

### Environment Variables

All configuration via environment variables:
- Database credentials
- Secret keys
- Feature flags

### Database Migrations

- Alembic for schema management
- Version controlled migrations
- Rollback capability

### Logging (Future)

- Structured logging
- Request/response logging
- Error tracking
- Performance metrics

## Code Quality

### Type Safety

- Type hints throughout
- Pydantic for validation
- SQLAlchemy type annotations

### Documentation

- Docstrings on all public methods
- API documentation via Swagger
- Architecture documentation

### Testing

- Unit tests for core logic
- Integration tests for flows
- Coverage reporting

## Future Improvements

1. **Caching Layer**: Redis for rate limiting and caching
2. **Message Queue**: Celery/RQ for background tasks
3. **Monitoring**: Prometheus metrics, health checks
4. **Logging**: Structured logging with correlation IDs
5. **API Versioning**: Version endpoints for backward compatibility
6. **GraphQL**: Alternative API interface
7. **WebSockets**: Real-time features
8. **Microservices**: Split into smaller services if needed
