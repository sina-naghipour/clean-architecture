# Authentication Guide

## Overview

The Ecommerce API uses JWT (JSON Web Token) based authentication with a refresh token mechanism. All protected endpoints require a valid access token in the Authorization header.

## Authentication Flow

### 1. User Registration
First, create a user account:

```http
POST /auth/register
Content-Type: application/json

{
  "email": "alice@example.com",
  "password": "S3cureP@ss",
  "name": "Alice"
}
```

**Response:**
```json
{
  "id": "user_123",
  "email": "alice@example.com",
  "name": "Alice"
}
```

### 2. Login to Get Tokens
Authenticate to receive access and refresh tokens:

```http
POST /auth/login
Content-Type: application/json

{
  "email": "alice@example.com",
  "password": "S3cureP@ss"
}
```

**Response:**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "rft_abcdef1234567890"
}
```

### 3. Using the Access Token
Include the access token in the Authorization header for all protected endpoints:

```http
GET /products
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 4. Refreshing Expired Tokens
When the access token expires (after 15 minutes), use the refresh token to get a new one:

```http
POST /auth/refresh-token
Content-Type: application/json

{
  "refreshToken": "rft_abcdef1234567890"
}
```

**Response:**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 5. Logout (Revoke Refresh Token)
To invalidate the refresh token:

```http
POST /auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Token Details

### Access Token
- **Type**: JWT (JSON Web Token)
- **Expiration**: 15 minutes
- **Claims**: User ID, roles, permissions
- **Usage**: Required for all protected endpoints

### Refresh Token
- **Type**: Opaque string
- **Expiration**: 7 days
- **Usage**: To obtain new access tokens
- **Storage**: Should be stored securely on client side

## Authorization Header Format

All authenticated requests must include the Authorization header with the following format:

```
Authorization: Bearer <access_token>
```

**Example:**
```http
GET /cart
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

## User Roles & Permissions

### Customer Role (Default)
- View products
- Manage own cart
- Create and view own orders
- Update own profile

### Admin Role
- All customer permissions
- Create, update, delete products
- Manage product images
- Update inventory
- View all orders

## Password Requirements

- Minimum 8 characters
- Must include at least one uppercase letter
- Must include at least one lowercase letter
- Must include at least one number
- Must include at least one special character

## Error Responses

### 401 Unauthorized
```json
{
  "type": "https://example.com/errors/unauthorized",
  "title": "Unauthorized",
  "status": 401,
  "detail": "Missing or invalid Authorization header.",
  "instance": "/auth/login"
}
```

### 403 Forbidden
```json
{
  "type": "https://example.com/errors/forbidden",
  "title": "Forbidden",
  "status": 403,
  "detail": "Insufficient permissions.",
  "instance": "/products"
}
```

## Security Best Practices

### Client-Side Storage
- **Access Token**: Store in memory (not localStorage/sessionStorage)
- **Refresh Token**: Store in HTTP-only cookie or secure storage
- **Never store tokens in plain text or client-accessible storage**

### Token Rotation
- Access tokens expire every 15 minutes
- Refresh tokens should be rotated on use
- Implement automatic token refresh before expiration

### Secure Transmission
- Always use HTTPS in production
- Include tokens only in Authorization header
- Never pass tokens in URL parameters

## Example: Complete Authentication Flow

```javascript
// 1. Register
const register = await fetch('/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'alice@example.com',
    password: 'S3cureP@ss',
    name: 'Alice'
  })
});

// 2. Login
const login = await fetch('/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'alice@example.com',
    password: 'S3cureP@ss'
  })
});

const { accessToken, refreshToken } = await login.json();

// 3. Make authenticated request
const products = await fetch('/products', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

// 4. Handle token refresh (when 401 received)
async function refreshAccessToken() {
  const response = await fetch('/auth/refresh-token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refreshToken })
  });
  
  const { accessToken: newAccessToken } = await response.json();
  return newAccessToken;
}

// 5. Logout
await fetch('/auth/logout', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});
```

## Troubleshooting

### Common Issues

1. **"Unauthorized" error**
   - Check if token is included in Authorization header
   - Verify token hasn't expired
   - Ensure correct "Bearer " prefix

2. **"Forbidden" error**
   - User lacks required permissions for the endpoint
   - Check user role (Customer vs Admin)

3. **Token expiration**
   - Access tokens expire after 15 minutes
   - Use refresh token to get new access token
   - Implement automatic token refresh

4. **Invalid credentials**
   - Verify email and password are correct
   - Check password requirements are met