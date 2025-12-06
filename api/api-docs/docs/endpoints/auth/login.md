# POST /auth/login

**Login User** - Authenticate user and receive access + refresh tokens

**Tags:** Auth

---

## Description
Authenticate a user with email and password credentials. Upon successful authentication, returns both access and refresh tokens for API authorization.

## Authentication
None required - this is a public endpoint

## Request

### Headers
```
Content-Type: application/json
```

### Body
**Schema:** LoginRequest

```json
{
  "email": "alice@example.com",
  "password": "S3cureP@ss"
}
```

**Fields:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `email` | string | ✓ | Valid email format | Registered email address |
| `password` | string | ✓ | - | Account password |

## Responses

### 200 OK - Authentication successful
**Body:**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "rft_abcdef1234567890"
}
```

**Response Fields:**

| Field | Type | Description | Expiration |
|-------|------|-------------|------------|
| `accessToken` | string | JWT for API authorization | Short-lived (15-60 min) |
| `refreshToken` | string | Token for obtaining new access tokens | Long-lived (7-30 days) |

### 400 Bad Request - Invalid input
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/bad-request",
  "title": "Bad Request",
  "status": 400,
  "detail": "Malformed JSON body.",
  "instance": "/auth/login"
}
```

**Common Causes:**
- Invalid JSON syntax
- Missing required fields
- Incorrect data types

### 401 Unauthorized - Invalid credentials
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/unauthorized",
  "title": "Unauthorized",
  "status": 401,
  "detail": "Invalid email or password.",
  "instance": "/auth/login"
}
```

**Causes:**
- Incorrect email or password
- Account locked/suspended
- Account not verified (if email verification required)

### 500 Internal Server Error
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/internal",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "Unexpected server error.",
  "instance": "/auth/login"
}
```

## Examples

### cURL
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "S3cureP@ss"
  }'
```

**Sample Response:**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzEyMyIsImVtYWlsIjoiYWxpY2VAZXhhbXBsZS5jb20iLCJuYW1lIjoiQWxpY2UiLCJyb2xlIjoiY3VzdG9tZXIiLCJpYXQiOjE2OTYxMzkwMjAsImV4cCI6MTY5NjE0MjYyMH0.signature",
  "refreshToken": "rft_abcdef1234567890"
}
```

### JavaScript (Fetch)
```javascript
async function login(email, password) {
  try {
    const response = await fetch('http://localhost:8000/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email: email,
        password: password
      })
    });

    if (response.ok) {
      const tokens = await response.json();
      
      // Store tokens securely
      localStorage.setItem('accessToken', tokens.accessToken);
      localStorage.setItem('refreshToken', tokens.refreshToken);
      
      console.log('Login successful');
      return tokens;
    } else {
      const error = await response.json();
      console.error('Login failed:', error);
      throw new Error(error.detail || 'Login failed');
    }
  } catch (error) {
    console.error('Network error:', error);
    throw error;
  }
}

// Usage
login('alice@example.com', 'S3cureP@ss')
  .then(tokens => console.log('Tokens:', tokens))
  .catch(error => console.error('Error:', error));
```

### Python
```python
import requests
import json

def login_user(email, password):
    """Authenticate user and get tokens."""
    url = "http://localhost:8000/api/auth/login"
    payload = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        tokens = response.json()
        print(f"Access Token: {tokens['accessToken'][:50]}...")
        print(f"Refresh Token: {tokens['refreshToken']}")
        
        # Store tokens (in secure storage for production)
        with open('tokens.json', 'w') as f:
            json.dump(tokens, f)
            
        return tokens
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("Error: Invalid credentials")
        else:
            print(f"Error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")

# Usage
login_user("alice@example.com", "S3cureP@ss")
```

### Postman
1. **Create Request:**
   - **Method:** POST
   - **URL:** `http://localhost:8000/api/auth/login`

2. **Headers:**
   ```
   Key: Content-Type
   Value: application/json
   ```

3. **Body (raw JSON):**
   ```json
   {
     "email": "alice@example.com",
     "password": "S3cureP@ss"
   }
   ```

4. **Tests (JavaScript):**
   ```javascript
   // Store tokens in environment variables
   pm.test("Status code is 200", function () {
       pm.response.to.have.status(200);
   });

   pm.test("Response has access token", function () {
       var jsonData = pm.response.json();
       pm.expect(jsonData.accessToken).to.be.a('string');
       pm.expect(jsonData.accessToken.length).to.be.greaterThan(10);
   });

   // Save tokens for later use
   var jsonData = pm.response.json();
   pm.environment.set("accessToken", jsonData.accessToken);
   pm.environment.set("refreshToken", jsonData.refreshToken);
   ```

## Using the Access Token

Once you have the access token, include it in subsequent API requests:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### cURL Example with Token:
```bash
# Get user's cart (protected endpoint)
curl -X GET "http://localhost:8000/api/cart" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### JavaScript Example with Token:
```javascript
async function getCart() {
  const accessToken = localStorage.getItem('accessToken');
  
  const response = await fetch('http://localhost:8000/api/cart', {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
  
  if (response.status === 401) {
    // Token expired, refresh it
    await refreshAccessToken();
    return getCart(); // Retry
  }
  
  return response.json();
}
```

## Token Management

### Access Token
- Short-lived (typically 15-60 minutes)
- Used for API authorization
- Sent in `Authorization: Bearer <token>` header
- Contains user claims (ID, email, role, permissions)

### Refresh Token
- Long-lived (typically 7-30 days)
- Used to obtain new access tokens
- Stored securely (HTTP-only cookies recommended)
- Can be revoked via logout

### Token Refresh Flow
1. Access token expires
2. Client calls `/auth/refresh-token` with refresh token
3. Server returns new access token
4. Client continues using new access token

## Security Best Practices

### Client-Side
- Store refresh tokens in HTTP-only cookies (not localStorage)
- Implement automatic token refresh before expiration
- Clear tokens on logout
- Implement session timeout

### Server-Side
- Use strong JWT signing algorithm (HS256/RS256)
- Implement token blacklisting/revocation
- Set appropriate token expiration times
- Use secure, HttpOnly, SameSite cookies for web apps

### Rate Limiting
Consider implementing rate limiting:
- Failed login attempts: 5-10 per hour per IP
- Successful logins: 100 per hour per user

---

## Related Endpoints
- [POST /auth/register](./register.md) - Create new account
- [POST /auth/refresh-token](./refresh-token.md) - Refresh access token
- [POST /auth/logout](./logout.md) - Logout and revoke tokens
- [GET /cart](../cart/get-cart.md) - Example protected endpoint
- [Error Responses](../../errors.md) - Error handling details

## Notes
- Always use HTTPS in production
- Implement proper error handling for expired tokens
- Consider adding 2FA/MFA for enhanced security
- Monitor login attempts for suspicious activity