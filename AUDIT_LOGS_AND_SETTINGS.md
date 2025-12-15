# Audit Logs and Settings Documentation

## Overview

This document describes the audit logging system and settings management features added to the FastAPI application.

## Audit Logs

### Purpose

The audit log system tracks all important system events for security, compliance, and debugging purposes. Every login attempt, user action, and admin operation is logged with detailed information.

### Database Schema

**Table:** `audit_logs`

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| action | Enum | Type of action (login, update, delete, etc.) |
| entity_type | String | Type of entity (user, admin, settings) |
| entity_id | Integer | ID of the affected entity |
| user_id | Integer | ID of user who performed action (if applicable) |
| admin_id | Integer | ID of admin who performed action (if applicable) |
| ip_address | String | IP address of the request |
| user_agent | String | User agent string |
| description | Text | Human-readable description |
| extra_data | Text | JSON string with additional metadata |
| success | Boolean | Whether the action succeeded |
| error_message | Text | Error message if action failed |
| created_at | DateTime | Timestamp of the event |

### Audit Log Actions

The system tracks the following action types:

- `LOGIN` - User/admin login attempts
- `LOGOUT` - User/admin logout
- `REGISTER` - User/admin registration
- `UPDATE` - Entity updates
- `DELETE` - Entity deletion
- `CREATE` - Entity creation
- `ACTIVATE` - Entity activation
- `DEACTIVATE` - Entity deactivation
- `BLOCK` - Entity blocking
- `UNBLOCK` - Entity unblocking
- `SOFT_DELETE` - Soft deletion
- `RESTORE` - Restore soft deleted entity
- `PASSWORD_CHANGE` - Password changes
- `TOKEN_CREATE` - Token creation
- `TOKEN_REVOKE` - Token revocation
- `SETTINGS_UPDATE` - Settings updates
- `OTHER` - Other actions

### Login Logging

**User Login:**
- Logs every login attempt (successful and failed)
- Captures IP address and user agent
- Records error messages for failed attempts
- Tracks account lockout events

**Admin Login:**
- Same logging as user login
- Separate entity type for admin tracking

**Example Log Entry:**
```json
{
  "action": "login",
  "entity_type": "user",
  "entity_id": 1,
  "user_id": 1,
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "description": "User login attempt",
  "success": true,
  "created_at": "2025-01-15T10:30:00Z"
}
```

### API Endpoints

#### Get Audit Logs (Admin Only)
**Endpoint:** `GET /admin/logs`

**Query Parameters:**
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Results per page (default: 100, max: 1000)
- `action` (string): Filter by action type
- `entity_type` (string): Filter by entity type
- `user_id` (int): Filter by user ID
- `admin_id` (int): Filter by admin ID
- `start_date` (datetime): Filter by start date
- `end_date` (datetime): Filter by end date
- `success_only` (bool): Filter by success status

**Example:**
```bash
GET /admin/logs?action=login&entity_type=user&limit=50
```

**Response:**
```json
{
  "success": true,
  "message": "Audit logs retrieved successfully",
  "data": {
    "items": [...],
    "total": 150,
    "page": 1,
    "size": 50
  }
}
```

#### Get Specific Audit Log (Admin Only)
**Endpoint:** `GET /admin/logs/{log_id}`

**Response:**
```json
{
  "success": true,
  "message": "Audit log retrieved successfully",
  "data": {
    "id": 1,
    "action": "login",
    "entity_type": "user",
    "entity_id": 1,
    "ip_address": "192.168.1.100",
    "success": true,
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

## Settings Management

### Purpose

The settings system provides a key-value store for application configuration that can be managed through the API without code changes.

### Database Schema

**Table:** `settings`

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| key | String(100) | Unique setting key |
| value | Text | Setting value |
| description | Text | Human-readable description |
| is_public | Boolean | Can be accessed without authentication |
| is_encrypted | Boolean | Should be encrypted (for sensitive data) |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

### API Endpoints

#### Get Public Settings (No Auth Required)
**Endpoint:** `GET /settings/public`

**Response:**
```json
{
  "success": true,
  "message": "Public settings retrieved successfully",
  "data": {
    "site_name": "My App",
    "maintenance_mode": "false"
  }
}
```

#### Get All Settings (Admin Only)
**Endpoint:** `GET /settings/`

**Response:**
```json
{
  "success": true,
  "message": "Settings retrieved successfully",
  "data": [
    {
      "id": 1,
      "key": "site_name",
      "value": "My App",
      "description": "Application name",
      "is_public": true,
      "is_encrypted": false,
      "created_at": "2025-01-15T10:00:00Z",
      "updated_at": "2025-01-15T10:00:00Z"
    }
  ]
}
```

#### Get Specific Setting (Admin Only)
**Endpoint:** `GET /settings/{key}`

**Example:**
```bash
GET /settings/site_name
```

#### Create/Update Setting (Admin Only)
**Endpoint:** `POST /settings/` (create) or `PUT /settings/{key}` (update)

**Request Body:**
```json
{
  "key": "site_name",
  "value": "My Application",
  "description": "Application display name",
  "is_public": true,
  "is_encrypted": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Setting created successfully",
  "data": {
    "id": 1,
    "key": "site_name",
    "value": "My Application",
    "is_public": true,
    "created_at": "2025-01-15T10:00:00Z"
  }
}
```

#### Delete Setting (Admin Only)
**Endpoint:** `DELETE /settings/{key}`

**Response:**
```json
{
  "success": true,
  "message": "Setting deleted successfully",
  "data": {
    "deleted": true
  }
}
```

### Usage Examples

#### Setting Application Name
```python
# Create setting
POST /settings/
{
  "key": "app_name",
  "value": "FastAPI Production App",
  "description": "Application name",
  "is_public": true
}
```

#### Setting Maintenance Mode
```python
# Update setting
PUT /settings/maintenance_mode
{
  "value": "true",
  "description": "Enable maintenance mode"
}
```

#### Getting Public Settings in Frontend
```javascript
// No authentication required
const response = await fetch('/settings/public');
const { data } = await response.json();
console.log(data.app_name); // "FastAPI Production App"
```

## Integration

### Automatic Logging

The following actions are automatically logged:

1. **User Login** - All login attempts (success/failure)
2. **Admin Login** - All admin login attempts
3. **User Activation** - When admin activates a user
4. **User Blocking** - When admin blocks a user
5. **User Updates** - When admin updates user data
6. **Settings Changes** - When settings are created/updated/deleted

### Manual Logging

You can manually log custom actions:

```python
from app.services.audit_service import AuditService
from app.models.audit_log import AuditLogAction

audit_service = AuditService(db)

await audit_service.log_action(
    action=AuditLogAction.OTHER,
    entity_type="custom",
    entity_id=123,
    admin_id=current_admin.id,
    description="Custom action performed",
    extra_data={"custom_field": "value"},
    success=True,
    request=request
)
```

## Best Practices

### Audit Logs

1. **Don't Log Sensitive Data**: Never log passwords, tokens, or other sensitive information
2. **Log All Important Actions**: Log user management, authentication, and configuration changes
3. **Retention Policy**: Implement a retention policy to archive old logs
4. **Performance**: Use indexes on frequently queried fields (action, entity_type, created_at)

### Settings

1. **Use Descriptive Keys**: Use clear, descriptive keys (e.g., `app_name` not `an`)
2. **Mark Sensitive Settings**: Use `is_encrypted=True` for sensitive data
3. **Public vs Private**: Only mark non-sensitive settings as public
4. **Documentation**: Always provide descriptions for settings

## Migration

To apply the database changes:

```bash
# Generate migration (already done)
alembic revision --autogenerate -m "Add audit logs and settings tables"

# Apply migration
alembic upgrade head
```

## Example Use Cases

### 1. Track Failed Login Attempts
```python
# Query failed login attempts
GET /admin/logs?action=login&success_only=false&entity_type=user
```

### 2. Monitor Admin Actions
```python
# Get all admin actions in last 24 hours
GET /admin/logs?admin_id=1&start_date=2025-01-14T00:00:00Z
```

### 3. Application Configuration
```python
# Set application-wide settings
POST /settings/
{
  "key": "max_upload_size_mb",
  "value": "50",
  "description": "Maximum file upload size in MB",
  "is_public": true
}
```

### 4. Feature Flags
```python
# Enable/disable features
PUT /settings/feature_new_dashboard
{
  "value": "true",
  "description": "Enable new dashboard feature"
}
```
