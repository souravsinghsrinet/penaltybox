# Admin User Setup Guide

## Creating Admin Users

Admin users can only be created through the backend API using the `/auth/register-admin` endpoint. This is a security measure to prevent unauthorized admin account creation through the frontend UI.

### Using curl

```bash
curl -X POST "http://localhost:8000/auth/register-admin" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Admin User",
    "email": "admin@example.com",
    "password": "securepassword123"
  }'
```

### Using HTTPie

```bash
http POST http://localhost:8000/auth/register-admin \
  name="Admin User" \
  email="admin@example.com" \
  password="securepassword123"
```

### Using Python requests

```python
import requests

response = requests.post(
    "http://localhost:8000/auth/register-admin",
    json={
        "name": "Admin User",
        "email": "admin@example.com",
        "password": "securepassword123"
    }
)

print(response.json())
```

## Admin Permissions

Admin users have the following additional permissions:

- **Groups**: Create new groups and add members
- **Penalties**: Create penalties and update penalty status
- **Rules**: Create and delete group rules
- **Proofs**: Approve and delete payment proofs

## Regular User Creation

Regular users can be created through:
1. The frontend registration page (http://localhost:5173/register)
2. The `/auth/register` API endpoint

Regular users will have `is_admin: false` by default and cannot perform admin-only operations.

## Verifying Admin Status

After logging in, you can verify your admin status by:
1. Checking the user badge on the Dashboard (should show "Admin" instead of "User")
2. Calling the `/auth/me` endpoint:

```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

The response will include `"is_admin": true` for admin users.
