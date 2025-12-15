# Collections, Dashboard, and Roles & Permissions API Documentation

## Overview

This document describes the Collections API, Dashboard API, and Roles & Permissions system for admin access control.

## Collections API

### Endpoints

#### 1. Get All Collections (Admin Only)
**Endpoint:** `GET /collections/`

**Query Parameters:**
- `skip` (int, default: 0): Pagination offset
- `limit` (int, default: 100, max: 1000): Results per page
- `is_active` (bool, optional): Filter by active status

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "success": true,
  "message": "Collections retrieved successfully",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "Electronics",
        "slug": "electronics",
        "description": "Electronic products",
        "image": "uuid-filename.png",
        "image_url": "/uploads/uuid-filename.png",
        "is_active": true,
        "sort_order": 0,
        "created_by_admin_id": 1,
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
      }
    ],
    "total": 10,
    "page": 1,
    "size": 10
  }
}
```

#### 2. Get Collection by ID (Admin Only)
**Endpoint:** `GET /collections/{collection_id}`

#### 3. Create Collection (Admin Only, Requires Permission)
**Endpoint:** `POST /collections/`

**Required Permission:** `collections:create`

**Form Data:**
- `name` (string, required): Collection name
- `slug` (string, optional): URL-friendly slug (auto-generated if not provided)
- `description` (string, optional): Collection description
- `is_active` (bool, default: true): Active status
- `sort_order` (int, default: 0): Sort order
- `image` (file, optional): Collection image (JPEG, PNG, WebP)

**Example:**
```bash
curl -X POST "http://localhost:8000/collections/" \
  -H "Authorization: Bearer <token>" \
  -F "name=Electronics" \
  -F "description=Electronic products" \
  -F "image=@electronics.jpg"
```

#### 4. Update Collection (Admin Only, Requires Permission)
**Endpoint:** `PUT /collections/{collection_id}`

**Required Permission:** `collections:update`

**Form Data:** Same as create, all fields optional

#### 5. Delete Collection (Admin Only, Requires Permission)
**Endpoint:** `DELETE /collections/{collection_id}`

**Required Permission:** `collections:delete`

**Note:** This performs a soft delete.

## Dashboard API

### Endpoints

#### 1. Get Dashboard Statistics (Admin Only)
**Endpoint:** `GET /dashboard/statistics`

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "success": true,
  "message": "Dashboard statistics retrieved successfully",
  "data": {
    "users": {
      "total": 150,
      "active": 120,
      "inactive": 30
    },
    "admins": {
      "total": 5,
      "active": 4,
      "inactive": 1
    },
    "collections": {
      "total": 25,
      "active": 20,
      "inactive": 5
    },
    "logins": {
      "recent_24h": 45,
      "successful_24h": 42,
      "failed_24h": 3
    }
  }
}
```

## Roles & Permissions API

### Permission Endpoints

#### 1. Get All Permissions (Admin Only)
**Endpoint:** `GET /admin/permissions`

**Response:**
```json
{
  "success": true,
  "message": "Permissions retrieved successfully",
  "data": [
    {
      "id": 1,
      "name": "collections:create",
      "resource": "collections",
      "action": "create",
      "description": "Create collections",
      "created_at": "2025-01-15T10:00:00Z"
    }
  ]
}
```

#### 2. Create Permission (Admin Only)
**Endpoint:** `POST /admin/permissions`

**Request Body:**
```json
{
  "name": "collections:create",
  "resource": "collections",
  "action": "create",
  "description": "Create collections"
}
```

### Role Endpoints

#### 1. Get All Roles (Admin Only)
**Endpoint:** `GET /admin/roles`

**Response:**
```json
{
  "success": true,
  "message": "Roles retrieved successfully",
  "data": [
    {
      "id": 1,
      "name": "Super Admin",
      "description": "Full access to all resources",
      "is_active": true,
      "created_at": "2025-01-15T10:00:00Z",
      "updated_at": "2025-01-15T10:00:00Z",
      "permissions": [...]
    }
  ]
}
```

#### 2. Get Role by ID (Admin Only)
**Endpoint:** `GET /admin/roles/{role_id}`

#### 3. Create Role (Admin Only)
**Endpoint:** `POST /admin/roles`

**Request Body:**
```json
{
  "name": "Manager",
  "description": "Manager role",
  "is_active": true,
  "permission_ids": [1, 2, 3, 4]
}
```

#### 4. Update Role (Admin Only)
**Endpoint:** `PUT /admin/roles/{role_id}`

**Request Body:**
```json
{
  "name": "Manager",
  "description": "Updated description",
  "is_active": true,
  "permission_ids": [1, 2, 3, 4, 5]
}
```

#### 5. Assign Roles to Admin (Admin Only)
**Endpoint:** `POST /admin/admins/{admin_id}/roles`

**Request Body:**
```json
{
  "role_ids": [1, 2]
}
```

## Default Permissions

The system includes the following default permissions:

### Collections
- `collections:create` - Create collections
- `collections:read` - Read collections
- `collections:update` - Update collections
- `collections:delete` - Delete collections

### Users
- `users:create` - Create users
- `users:read` - Read users
- `users:update` - Update users
- `users:delete` - Delete users

### Admins
- `admins:create` - Create admins
- `admins:read` - Read admins
- `admins:update` - Update admins
- `admins:delete` - Delete admins

### Settings
- `settings:create` - Create settings
- `settings:read` - Read settings
- `settings:update` - Update settings
- `settings:delete` - Delete settings

### Roles
- `roles:create` - Create roles
- `roles:read` - Read roles
- `roles:update` - Update roles
- `roles:delete` - Delete roles

### Audit Logs
- `audit_logs:read` - Read audit logs

## Default Roles

### Super Admin
- **Description:** Full access to all resources
- **Permissions:** All permissions

### Admin
- **Description:** Administrative access with limited role management
- **Permissions:** All permissions except role management

### Manager
- **Description:** Manager access with read and update permissions
- **Permissions:** Read and update permissions (no create/delete, no role management)

## Seeding Permissions and Roles

Run the seeder to create default permissions and roles:

```bash
python -m app.seed_permissions
```

This will:
1. Create all default permissions
2. Create three default roles (Super Admin, Admin, Manager)
3. Assign Super Admin role to the default admin user

## Permission Checking

### Using in Routes

To require a specific permission in a route:

```python
from app.api.deps import require_permission

@router.post("/collections/")
async def create_collection(
    current_admin: Admin = Depends(require_permission("collections", "create")),
    ...
):
    # Only admins with collections:create permission can access this
    ...
```

### Manual Permission Check

```python
from app.services.permission_service import PermissionService

permission_service = PermissionService(db)
has_permission = await permission_service.admin_has_permission(
    admin, "collections", "create"
)
```

## Usage Examples

### 1. Create a Collection

```python
import requests

url = "http://localhost:8000/collections/"
headers = {"Authorization": f"Bearer {admin_token}"}

files = {"image": open("collection.jpg", "rb")}
data = {
    "name": "Electronics",
    "description": "Electronic products",
    "is_active": True,
    "sort_order": 0
}

response = requests.post(url, headers=headers, files=files, data=data)
print(response.json())
```

### 2. Get Dashboard Statistics

```python
import requests

url = "http://localhost:8000/dashboard/statistics"
headers = {"Authorization": f"Bearer {admin_token}"}

response = requests.get(url, headers=headers)
stats = response.json()["data"]
print(f"Total users: {stats['users']['total']}")
print(f"Active collections: {stats['collections']['active']}")
```

### 3. Create a Role

```python
import requests

url = "http://localhost:8000/admin/roles"
headers = {
    "Authorization": f"Bearer {admin_token}",
    "Content-Type": "application/json"
}

data = {
    "name": "Content Manager",
    "description": "Manages collections and content",
    "is_active": True,
    "permission_ids": [1, 2, 3, 4]  # Collections permissions
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### 4. Assign Roles to Admin

```python
import requests

url = "http://localhost:8000/admin/admins/2/roles"
headers = {
    "Authorization": f"Bearer {admin_token}",
    "Content-Type": "application/json"
}

data = {
    "role_ids": [2, 3]  # Admin and Manager roles
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

## Database Schema

### Collections Table
- `id` - Primary key
- `name` - Collection name
- `slug` - URL-friendly identifier (unique)
- `description` - Collection description
- `image` - Image filename
- `is_active` - Active status
- `sort_order` - Sort order
- `created_by_admin_id` - Admin who created it
- `created_at` - Creation timestamp
- `updated_at` - Update timestamp
- `deleted_at` - Soft delete timestamp

### Roles Table
- `id` - Primary key
- `name` - Role name (unique)
- `description` - Role description
- `is_active` - Active status
- `created_at` - Creation timestamp
- `updated_at` - Update timestamp

### Permissions Table
- `id` - Primary key
- `name` - Permission name (unique)
- `resource` - Resource name (e.g., 'collections')
- `action` - Action name (e.g., 'create')
- `description` - Permission description
- `created_at` - Creation timestamp

### Association Tables
- `role_permissions` - Many-to-many: roles ↔ permissions
- `admin_roles` - Many-to-many: admins ↔ roles

## Best Practices

1. **Permission Naming:** Use format `resource:action` (e.g., `collections:create`)
2. **Role Assignment:** Assign roles to admins, not individual permissions
3. **Permission Checking:** Always check permissions in protected endpoints
4. **Default Roles:** Use default roles as templates for custom roles
5. **Audit Logging:** All role and permission changes are logged automatically
