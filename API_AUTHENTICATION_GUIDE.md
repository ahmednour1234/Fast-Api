# API Authentication Guide

## Overview

This guide explains how to authenticate and use protected endpoints in the FastAPI application.

## Authentication Flow

1. **Login** → Get JWT token
2. **Use Token** → Include token in Authorization header for protected endpoints

## User Authentication

### Step 1: Register a User (Optional)

If you don't have an account, register first:

**Endpoint:** `POST /auth/register`

**Request (Form Data):**
```
username: your_username
name: Your Name
email: your@email.com
password: your_password
phone: +1234567890 (optional)
```

**Example using cURL:**
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/auth/register' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=testuser&name=Test User&email=test@example.com&password=password123'
```

**Response:**
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "id": 1,
    "username": "testuser",
    "name": "Test User",
    "email": "test@example.com",
    "is_active": true,
    "created_at": "2025-01-15T10:30:00"
  }
}
```

### Step 2: Login to Get Token

**Endpoint:** `POST /auth/login`

**Request (Form Data):**
```
username: your_username (or email)
password: your_password
```

**Example using cURL:**
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/auth/login' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=testuser&password=password123'
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```

**Save the `access_token` value!**

### Step 3: Use Token for Protected Endpoints

**Example: Get User Profile**

**Endpoint:** `GET /users/me`

**Request with Authorization:**
```bash
curl -X 'GET' \
  'http://127.0.0.1:8000/users/me' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
```

**Important:** Replace `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` with your actual token!

## Admin Authentication

### Step 1: Register an Admin (Optional)

**Endpoint:** `POST /admin/auth/register`

**Request (Form Data):**
```
username: admin_username
name: Admin Name
email: admin@example.com
password: admin_password
phone: +1234567890 (optional)
```

**Example using cURL:**
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/admin/auth/register' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin&name=Admin User&email=admin@example.com&password=admin123'
```

### Step 2: Login as Admin

**Endpoint:** `POST /admin/auth/login`

**Request (Form Data):**
```
username: admin_username (or email)
password: admin_password
```

**Example using cURL:**
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/admin/auth/login' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin&password=admin123'
```

**Response:**
```json
{
  "success": true,
  "message": "Admin login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```

### Step 3: Use Admin Token

**Example: Get Admin Profile**

**Endpoint:** `GET /admin/me`

```bash
curl -X 'GET' \
  'http://127.0.0.1:8000/admin/me' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
```

## Using Swagger UI

### Step 1: Login in Swagger UI

1. Open Swagger UI: `http://127.0.0.1:8000/docs`
2. Find the login endpoint:
   - For users: `/auth/login`
   - For admins: `/admin/auth/login`
3. Click "Try it out"
4. Enter your credentials:
   - `username`: your username or email
   - `password`: your password
5. Click "Execute"
6. Copy the `access_token` from the response

### Step 2: Authorize in Swagger UI

1. Click the **"Authorize"** button (lock icon) at the top right
2. In the "Value" field, paste your `access_token`
3. Click **"Authorize"**
4. Click **"Close"**

Now all protected endpoints will automatically include your token!

### Step 3: Test Protected Endpoints

1. Find any protected endpoint (e.g., `/users/me` or `/admin/me`)
2. Click "Try it out"
3. Click "Execute"
4. You should get a successful response!

## Using Python Requests

### User Authentication Example

```python
import requests

BASE_URL = "http://127.0.0.1:8000"

# Step 1: Login
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    data={
        "username": "testuser",
        "password": "password123"
    }
)

token_data = login_response.json()
access_token = token_data["data"]["access_token"]

# Step 2: Use token for protected endpoint
headers = {
    "Authorization": f"Bearer {access_token}"
}

profile_response = requests.get(
    f"{BASE_URL}/users/me",
    headers=headers
)

print(profile_response.json())
```

### Admin Authentication Example

```python
import requests

BASE_URL = "http://127.0.0.1:8000"

# Step 1: Admin Login
login_response = requests.post(
    f"{BASE_URL}/admin/auth/login",
    data={
        "username": "admin",
        "password": "admin123"
    }
)

token_data = login_response.json()
access_token = token_data["data"]["access_token"]

# Step 2: Use token for admin endpoint
headers = {
    "Authorization": f"Bearer {access_token}"
}

# Get admin profile
profile_response = requests.get(
    f"{BASE_URL}/admin/me",
    headers=headers
)

# List all users (admin only)
users_response = requests.get(
    f"{BASE_URL}/admin/users",
    headers=headers,
    params={"skip": 0, "limit": 10}
)

print(users_response.json())
```

## Using JavaScript/Fetch

### User Authentication Example

```javascript
const BASE_URL = 'http://127.0.0.1:8000';

// Step 1: Login
async function login(username, password) {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);
  
  const response = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData
  });
  
  const data = await response.json();
  return data.data.access_token;
}

// Step 2: Use token
async function getProfile(token) {
  const response = await fetch(`${BASE_URL}/users/me`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json'
    }
  });
  
  return await response.json();
}

// Usage
const token = await login('testuser', 'password123');
const profile = await getProfile(token);
console.log(profile);
```

## Token Expiration

- Tokens expire after the time specified in `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 60 minutes)
- When a token expires, you'll get a `401 Unauthorized` error
- Simply login again to get a new token

## Common Errors

### 401 Unauthorized
- **Cause:** Missing or invalid token
- **Solution:** Login again and use the new token

### 403 Forbidden
- **Cause:** User account is inactive or insufficient permissions
- **Solution:** Check if account is active, or use admin account for admin endpoints

### 429 Too Many Requests
- **Cause:** Rate limit exceeded (too many login attempts)
- **Solution:** Wait for the rate limit window to reset (default: 15 minutes)

## Quick Reference

### User Endpoints
- Register: `POST /auth/register`
- Login: `POST /auth/login`
- Get Profile: `GET /users/me` (requires token)
- Update Profile: `PUT /users/me` (requires token)
- Delete Account: `DELETE /users/me` (requires token)

### Admin Endpoints
- Register: `POST /admin/auth/register`
- Login: `POST /admin/auth/login`
- Get Profile: `GET /admin/me` (requires admin token)
- List Users: `GET /admin/users` (requires admin token)
- Get User: `GET /admin/users/{id}` (requires admin token)
- Update User: `PUT /admin/users/{id}` (requires admin token)
- Activate User: `PATCH /admin/users/{id}/activate` (requires admin token)
- Block User: `PATCH /admin/users/{id}/block` (requires admin token)

## Default Credentials

After running the seed script (`python -m app.seed`):

**Admin:**
- Username: `admin`
- Email: `admin@example.com`
- Password: `admin123`

⚠️ **Change these credentials in production!**
