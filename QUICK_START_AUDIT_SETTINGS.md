# Quick Start: Audit Logs and Settings

## What Was Added

### 1. Audit Logs System
- **Database Table**: `audit_logs` - Tracks all system events
- **Automatic Logging**: Login attempts (user & admin) are automatically logged
- **Manual Logging**: Admin actions (activate, block, update users) are logged
- **API Endpoints**: View audit logs (admin only)

### 2. Settings System
- **Database Table**: `settings` - Key-value configuration store
- **Public Settings**: Some settings can be accessed without authentication
- **Admin Management**: Admins can create, update, and delete settings
- **API Endpoints**: Full CRUD for settings

## Database Migration

Run the migration to create the new tables:

```bash
alembic upgrade head
```

## Using Audit Logs

### View All Login Attempts
```bash
# Login as admin first, then:
GET /admin/logs?action=login
```

### View Failed Login Attempts
```bash
GET /admin/logs?action=login&success_only=false
```

### View Admin Actions
```bash
GET /admin/logs?admin_id=1&start_date=2025-01-15T00:00:00Z
```

## Using Settings

### Create a Setting
```bash
POST /settings/
{
  "key": "app_name",
  "value": "My Application",
  "description": "Application name",
  "is_public": true
}
```

### Get Public Settings (No Auth)
```bash
GET /settings/public
```

### Update a Setting
```bash
PUT /settings/app_name
{
  "value": "Updated App Name"
}
```

### Get All Settings (Admin Only)
```bash
GET /settings/
```

## What Gets Logged Automatically

✅ **User Login** - Success and failure
✅ **Admin Login** - Success and failure  
✅ **User Activation** - When admin activates a user
✅ **User Blocking** - When admin blocks a user
✅ **User Updates** - When admin updates user data
✅ **Settings Changes** - Create, update, delete settings

## Example: Check Login History

1. Login as admin
2. Get token from login response
3. Query audit logs:
   ```bash
   GET /admin/logs?action=login&entity_type=user&limit=50
   ```

## Example: Application Configuration

1. Set maintenance mode:
   ```bash
   POST /settings/
   {
     "key": "maintenance_mode",
     "value": "false",
     "description": "Enable/disable maintenance mode",
     "is_public": true
   }
   ```

2. Frontend can check without auth:
   ```javascript
   const response = await fetch('/settings/public');
   const { data } = await response.json();
   if (data.maintenance_mode === 'true') {
     // Show maintenance page
   }
   ```

## Files Created

- `app/models/audit_log.py` - Audit log model
- `app/models/settings.py` - Settings model
- `app/repositories/audit_log_repo.py` - Audit log repository
- `app/repositories/settings_repo.py` - Settings repository
- `app/services/audit_service.py` - Audit logging service
- `app/schemas/audit_log.py` - Audit log schemas
- `app/schemas/settings.py` - Settings schemas
- `app/api/routes/audit_logs.py` - Audit log endpoints
- `app/api/routes/settings.py` - Settings endpoints

## Documentation

See `AUDIT_LOGS_AND_SETTINGS.md` for complete documentation.
