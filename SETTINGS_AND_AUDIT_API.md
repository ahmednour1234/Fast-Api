# Settings and Audit Logs API Documentation

## Overview

This document describes the Settings and Audit Logs APIs, including support for image uploads, key-value pairs, and application-specific settings.

## Settings API

### Endpoints

#### 1. Get Public Settings (No Auth)
**Endpoint:** `GET /settings/public`

**Description:** Get all public settings (no authentication required)

**Response:**
```json
{
  "success": true,
  "message": "Public settings retrieved successfully",
  "data": {
    "app_name": "FastAPI Production Scaffold",
    "email": "admin@example.com",
    "contact_info": "Contact us at admin@example.com",
    "url": "http://localhost:8000",
    "logo": "uuid-filename.png"
  }
}
```

#### 2. Get All Settings (Admin Only)
**Endpoint:** `GET /settings/`

**Description:** Get all settings (admin only)

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "success": true,
  "message": "Settings retrieved successfully",
  "data": [
    {
      "id": 1,
      "key": "app_name",
      "value": "FastAPI Production Scaffold",
      "description": "Application name",
      "is_public": true,
      "is_encrypted": false,
      "created_at": "2025-01-15T10:00:00Z",
      "updated_at": "2025-01-15T10:00:00Z"
    }
  ]
}
```

#### 3. Get Specific Setting (Admin Only)
**Endpoint:** `GET /settings/{key}`

**Example:**
```bash
GET /settings/app_name
```

#### 4. Get Application Settings
**Endpoint:** `GET /settings/app`

**Description:** Get application-specific settings (logo, email, contact_info, app_name, url)

**Response:**
```json
{
  "success": true,
  "message": "Application settings retrieved successfully",
  "data": {
    "logo": "uuid-filename.png",
    "logo_url": "/uploads/uuid-filename.png",
    "email": "admin@example.com",
    "contact_info": "Contact us at admin@example.com",
    "app_name": "FastAPI Production Scaffold",
    "url": "http://localhost:8000"
  }
}
```

#### 5. Create Setting (Admin Only)
**Endpoint:** `POST /settings/`

**Description:** Create a new setting using form data (supports key-value pairs)

**Headers:**
```
Authorization: Bearer <admin_token>
Content-Type: multipart/form-data
```

**Form Data:**
- `key` (string, required): Setting key
- `value` (string, required): Setting value
- `description` (string, optional): Description
- `is_public` (boolean, default: false): Make setting public
- `is_encrypted` (boolean, default: false): Mark as encrypted

**Example:**
```bash
curl -X POST "http://localhost:8000/settings/" \
  -H "Authorization: Bearer <token>" \
  -F "key=maintenance_mode" \
  -F "value=false" \
  -F "description=Enable/disable maintenance mode" \
  -F "is_public=true"
```

#### 6. Update Setting (Admin Only)
**Endpoint:** `PUT /settings/{key}`

**Description:** Update a setting using form data

**Form Data:**
- `value` (string, optional): New value
- `description` (string, optional): New description
- `is_public` (boolean, optional): Update public flag
- `is_encrypted` (boolean, optional): Update encrypted flag

**Example:**
```bash
curl -X PUT "http://localhost:8000/settings/maintenance_mode" \
  -H "Authorization: Bearer <token>" \
  -F "value=true"
```

#### 7. Bulk Create/Update Settings (Admin Only)
**Endpoint:** `POST /settings/bulk`

**Description:** Create or update multiple settings at once using key-value pairs

**Headers:**
```
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "settings": {
    "feature_flag_1": "enabled",
    "feature_flag_2": "disabled",
    "max_upload_size": "50",
    "api_rate_limit": "100"
  },
  "is_public": false,
  "description": "Feature flags and limits"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Bulk settings processed: 2 created, 2 updated",
  "data": {
    "created": 2,
    "updated": 2,
    "total": 4
  }
}
```

#### 8. Update Application Settings (Admin Only)
**Endpoint:** `PUT /settings/app`

**Description:** Update application-specific settings with logo image upload support

**Headers:**
```
Authorization: Bearer <admin_token>
Content-Type: multipart/form-data
```

**Form Data:**
- `logo` (file, optional): Logo image file (JPEG, PNG, WebP)
- `email` (string, optional): Contact email
- `contact_info` (string, optional): Contact information
- `app_name` (string, optional): Application name
- `url` (string, optional): Application URL

**Example:**
```bash
curl -X PUT "http://localhost:8000/settings/app" \
  -H "Authorization: Bearer <token>" \
  -F "logo=@/path/to/logo.png" \
  -F "app_name=My Application" \
  -F "email=contact@example.com" \
  -F "contact_info=Call us at +1234567890" \
  -F "url=https://myapp.com"
```

**Response:**
```json
{
  "success": true,
  "message": "Application settings updated successfully",
  "data": {
    "logo": "uuid-filename.png",
    "logo_url": "/uploads/uuid-filename.png",
    "email": "contact@example.com",
    "contact_info": "Call us at +1234567890",
    "app_name": "My Application",
    "url": "https://myapp.com"
  }
}
```

#### 9. Delete Setting (Admin Only)
**Endpoint:** `DELETE /settings/{key}`

**Example:**
```bash
DELETE /settings/maintenance_mode
```

## Audit Logs API

### Endpoints

#### 1. Get Audit Logs (Admin Only)
**Endpoint:** `GET /admin/logs`

**Description:** Get audit logs with filtering and pagination

**Query Parameters:**
- `skip` (int, default: 0): Pagination offset
- `limit` (int, default: 100, max: 1000): Results per page
- `action` (string, optional): Filter by action type (login, update, delete, etc.)
- `entity_type` (string, optional): Filter by entity type (user, admin, settings)
- `user_id` (int, optional): Filter by user ID
- `admin_id` (int, optional): Filter by admin ID
- `start_date` (datetime, optional): Filter by start date
- `end_date` (datetime, optional): Filter by end date
- `success_only` (boolean, optional): Filter by success status

**Example:**
```bash
GET /admin/logs?action=login&entity_type=user&limit=50&success_only=false
```

**Response:**
```json
{
  "success": true,
  "message": "Audit logs retrieved successfully",
  "data": {
    "items": [
      {
        "id": 1,
        "action": "login",
        "entity_type": "user",
        "entity_id": 1,
        "user_id": 1,
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0...",
        "description": "User login attempt",
        "extra_data": null,
        "success": true,
        "error_message": null,
        "created_at": "2025-01-15T10:30:00Z"
      }
    ],
    "total": 150,
    "page": 1,
    "size": 50
  }
}
```

#### 2. Get Specific Audit Log (Admin Only)
**Endpoint:** `GET /admin/logs/{log_id}`

**Example:**
```bash
GET /admin/logs/1
```

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
    "user_id": 1,
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "description": "User login attempt",
    "success": true,
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

## Seeder

### Run Settings Seeder

The seeder creates default application settings:

```bash
python -m app.seed
```

**Default Settings Created:**
- `app_name`: "FastAPI Production Scaffold"
- `email`: "admin@example.com"
- `contact_info`: "Contact us at admin@example.com"
- `url`: "http://localhost:8000"

**Note:** Logo is not seeded as it requires an image file upload. Use the `PUT /settings/app` endpoint to upload a logo.

## Usage Examples

### 1. Upload Logo and Update App Settings

```python
import requests

url = "http://localhost:8000/settings/app"
headers = {"Authorization": f"Bearer {admin_token}"}

files = {"logo": open("logo.png", "rb")}
data = {
    "app_name": "My Awesome App",
    "email": "contact@myapp.com",
    "contact_info": "Email us or call +1234567890",
    "url": "https://myapp.com"
}

response = requests.put(url, headers=headers, files=files, data=data)
print(response.json())
```

### 2. Bulk Update Settings

```python
import requests

url = "http://localhost:8000/settings/bulk"
headers = {
    "Authorization": f"Bearer {admin_token}",
    "Content-Type": "application/json"
}

data = {
    "settings": {
        "maintenance_mode": "false",
        "max_upload_size_mb": "50",
        "api_rate_limit": "100",
        "feature_new_dashboard": "true"
    },
    "is_public": False,
    "description": "Application configuration"
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### 3. Get Failed Login Attempts

```python
import requests
from datetime import datetime, timedelta

url = "http://localhost:8000/admin/logs"
headers = {"Authorization": f"Bearer {admin_token}"}

params = {
    "action": "login",
    "success_only": False,
    "start_date": (datetime.now() - timedelta(days=1)).isoformat(),
    "limit": 100
}

response = requests.get(url, headers=headers, params=params)
logs = response.json()["data"]["items"]
print(f"Found {len(logs)} failed login attempts")
```

### 4. Get Application Settings in Frontend

```javascript
// No authentication required for public settings
const response = await fetch('/settings/public');
const { data } = await response.json();

console.log(data.app_name); // "FastAPI Production Scaffold"
console.log(data.logo_url); // "/uploads/uuid-filename.png"

// Display logo
if (data.logo_url) {
  document.getElementById('logo').src = data.logo_url;
}
```

## Image Upload Details

### Supported Formats
- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)
- WebP (`.webp`)

### File Size Limit
- Maximum size is controlled by `MAX_UPLOAD_MB` in settings (default: 5MB)

### File Storage
- Images are stored in the `UPLOAD_DIR` directory (default: `uploads/`)
- Filenames are UUID-based to prevent conflicts
- Original file extension is preserved

### Accessing Uploaded Images
- Images are accessible via: `/uploads/{filename}`
- Example: `/uploads/123e4567-e89b-12d3-a456-426614174000.png`

## Best Practices

1. **Settings Keys**: Use descriptive, lowercase keys with underscores (e.g., `app_name`, `max_upload_size`)
2. **Public Settings**: Only mark non-sensitive settings as public
3. **Logo Upload**: Use the `/settings/app` endpoint for logo uploads
4. **Bulk Updates**: Use `/settings/bulk` for updating multiple settings at once
5. **Audit Logs**: Regularly review audit logs for security monitoring
6. **Image Optimization**: Optimize logo images before upload for better performance

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "message": "Error message",
  "error": {
    "code": "ERROR_CODE",
    "message": "Detailed error message"
  }
}
```

Common error codes:
- `VALIDATION_ERROR`: Invalid input data
- `NOT_FOUND`: Resource not found
- `UNAUTHORIZED`: Authentication required
- `FORBIDDEN`: Insufficient permissions
- `CONFLICT`: Resource already exists
