# POST /auth/register

**Register New User** - Create a new user account

**Tags:** Auth

---

## Description
Register a new user account with email, password, and name. Upon successful registration, the user can immediately log in using their credentials.

## Authentication
None required - this is a public endpoint

## Request

### Headers
```
Content-Type: application/json
```

### Body
**Schema:** RegisterRequest

```json
{
  "email": "alice@example.com",
  "password": "S3cureP@ss",
  "name": "Alice"
}
```

**Fields:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `email` | string | ✓ | Valid email format | User's email address |
| `password` | string | ✓ | Min 8 characters | Account password |
| `name` | string | ✓ | - | User's full name |

## Responses

### 201 Created - User successfully registered
**Headers:**
- `Location`: `/auth/login` (URI to login endpoint)

**Body:**
```json
{
  "id": "user_123",
  "email": "alice@example.com",
  "name": "Alice"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique user identifier |
| `email` | string | Registered email address |
| `name` | string | User's full name |

### 400 Bad Request - Invalid input
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/bad-request",
  "title": "Bad Request",
  "status": 400,
  "detail": "Malformed JSON body.",
  "instance": "/auth/register"
}
```

**Common Causes:**
- Invalid JSON syntax
- Missing required fields
- Incorrect data types

### 409 Conflict - Duplicate user
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/conflict",
  "title": "Conflict",
  "status": 409,
  "detail": "Email already registered.",
  "instance": "/auth/register"
}
```

**Cause:** Email address is already registered

### 422 Unprocessable Entity - Validation error
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/validation",
  "title": "Validation failed",
  "status": 422,
  "detail": "Field 'email' is required.",
  "instance": "/auth/register"
}
```

**Common Validation Errors:**
- Password too short (< 8 characters)
- Invalid email format
- Name contains invalid characters

### 500 Internal Server Error
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/internal",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "Unexpected server error.",
  "instance": "/auth/register"
}
```

## Examples

### cURL
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "S3cureP@ss",
    "name": "Alice"
  }'
```

### JavaScript (Fetch)
```javascript
const response = await fetch('http://localhost:8000/api/auth/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'alice@example.com',
    password: 'S3cureP@ss',
    name: 'Alice'
  })
});

if (response.status === 201) {
  const user = await response.json();
  console.log('User created:', user);
} else {
  const error = await response.json();
  console.error('Registration failed:', error);
}
```

### Python
```python
import requests

data = {
    "email": "alice@example.com",
    "password": "S3cureP@ss",
    "name": "Alice"
}

response = requests.post(
    "http://localhost:8000/api/auth/register",
    json=data
)

if response.status_code == 201:
    user = response.json()
    print(f"User created: {user}")
else:
    error = response.json()
    print(f"Error: {error}")
```

### Postman
1. **Method:** POST
2. **URL:** `http://localhost:8000/api/auth/register`
3. **Headers:** 
   - `Content-Type: application/json`
4. **Body (raw JSON):**
   ```json
   {
     "email": "alice@example.com",
     "password": "S3cureP@ss",
     "name": "Alice"
   }
   ```

## Next Steps

After successful registration:

1. **Immediate Login:** Use the same credentials to log in
2. **Get Tokens:** Call `/auth/login` to receive access and refresh tokens
3. **Set Authentication:** Use the `accessToken` in the `Authorization: Bearer <token>` header for protected endpoints

## Security Notes

### Password Requirements
- Minimum 8 characters
- Consider implementing additional complexity rules:
  - Mix of uppercase/lowercase
  - Include numbers
  - Special characters

### Email Verification
Consider adding email verification flow:
1. Send verification email after registration
2. Require email confirmation before full account activation
3. Provide resend verification email endpoint

### Data Protection
- Passwords are hashed before storage (using bcrypt/scrypt/argon2)
- No sensitive data returned in response
- Implement rate limiting to prevent brute force attacks

---

## Related Endpoints
- [POST /auth/login](./login.md) - Login with credentials
- [POST /auth/refresh-token](./refresh-token.md) - Refresh access token
- [POST /auth/logout](./logout.md) - Logout user
- [Error Responses](../../errors.md) - Error handling details

## Notes
- Registration does not automatically log the user in
- Users must call `/auth/login` after registration to obtain tokens
- All user data is validated before processing
- Consider implementing CAPTCHA for public registration endpoints