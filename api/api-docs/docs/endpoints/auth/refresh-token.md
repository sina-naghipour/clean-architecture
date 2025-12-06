# POST /auth/refresh-token

**Refresh Access Token** - Obtain new access token using refresh token

**Tags:** Auth

---

## Description
Exchange a valid refresh token for a new access token. This endpoint allows users to continue accessing protected resources without re-authenticating with email/password.

## Authentication
None required (refresh token is sent in request body)

## Request

### Headers
```
Content-Type: application/json
```

### Body
**Schema:** RefreshTokenRequest

```json
{
  "refreshToken": "rft_abcdef1234567890"
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `refreshToken` | string | ✓ | Valid refresh token obtained from login |

## Responses

### 200 OK - New access token issued
**Body:**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `accessToken` | string | New JWT for API authorization |

**Note:** The refresh token remains valid and unchanged.

### 400 Bad Request - Invalid input
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/bad-request",
  "title": "Bad Request",
  "status": 400,
  "detail": "Malformed JSON body or missing refreshToken.",
  "instance": "/auth/refresh-token"
}
```

### 401 Unauthorized - Invalid refresh token
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/unauthorized",
  "title": "Unauthorized",
  "status": 401,
  "detail": "Invalid or expired refresh token.",
  "instance": "/auth/refresh-token"
}
```

**Causes:**
- Refresh token expired
- Refresh token revoked (user logged out)
- Invalid token format
- Token belongs to different user/device

### 500 Internal Server Error
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/internal",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "Unexpected server error.",
  "instance": "/auth/refresh-token"
}
```

## Examples

### cURL
```bash
curl -X POST "http://localhost:8000/api/auth/refresh-token" \
  -H "Content-Type: application/json" \
  -d '{
    "refreshToken": "rft_abcdef1234567890"
  }'
```

### JavaScript (Fetch)
```javascript
async function refreshAccessToken() {
  const refreshToken = localStorage.getItem('refreshToken');
  
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }
  
  try {
    const response = await fetch('http://localhost:8000/api/auth/refresh-token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        refreshToken: refreshToken
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      
      // Update stored access token
      localStorage.setItem('accessToken', data.accessToken);
      
      console.log('Access token refreshed');
      return data.accessToken;
    } else {
      const error = await response.json();
      
      // Refresh token invalid - force re-login
      if (response.status === 401) {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
      }
      
      throw new Error(error.detail || 'Token refresh failed');
    }
  } catch (error) {
    console.error('Refresh error:', error);
    throw error;
  }
}

// Usage with automatic retry
async function makeAuthenticatedRequest(url, options = {}) {
  let accessToken = localStorage.getItem('accessToken');
  
  const requestOptions = {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${accessToken}`
    }
  };
  
  let response = await fetch(url, requestOptions);
  
  // Token expired - try to refresh
  if (response.status === 401) {
    try {
      const newToken = await refreshAccessToken();
      
      // Retry with new token
      requestOptions.headers.Authorization = `Bearer ${newToken}`;
      response = await fetch(url, requestOptions);
    } catch (refreshError) {
      // Refresh failed - redirect to login
      window.location.href = '/login';
      return null;
    }
  }
  
  return response;
}
```

### Python
```python
import requests
import json

def refresh_access_token(refresh_token):
    """Refresh access token using refresh token."""
    url = "http://localhost:8000/api/auth/refresh-token"
    payload = {
        "refreshToken": refresh_token
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        new_access_token = data['accessToken']
        
        print("Access token refreshed successfully")
        return new_access_token
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("Error: Invalid or expired refresh token")
            # Clear stored tokens and require re-login
            return None
        else:
            print(f"Error: {e.response.status_code} - {e.response.text}")
            return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def make_authenticated_request(url, method='GET', data=None, access_token=None):
    """Make request with automatic token refresh."""
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data)
        # Add other methods as needed
        
        # If token expired, try to refresh
        if response.status_code == 401:
            # Load refresh token from secure storage
            with open('tokens.json', 'r') as f:
                tokens = json.load(f)
            
            new_access_token = refresh_access_token(tokens['refreshToken'])
            if new_access_token:
                # Update token and retry
                tokens['accessToken'] = new_access_token
                with open('tokens.json', 'w') as f:
                    json.dump(tokens, f)
                
                headers['Authorization'] = f'Bearer {new_access_token}'
                if method.upper() == 'GET':
                    response = requests.get(url, headers=headers)
                elif method.upper() == 'POST':
                    response = requests.post(url, headers=headers, json=data)
        
        return response
        
    except Exception as e:
        print(f"Request error: {str(e)}")
        return None
```

### Postman
1. **Create Request:**
   - **Method:** POST
   - **URL:** `http://localhost:8000/api/auth/refresh-token`

2. **Headers:**
   ```
   Key: Content-Type
   Value: application/json
   ```

3. **Body (raw JSON):**
   ```json
   {
     "refreshToken": "{{refreshToken}}"
   }
   ```
   *Note: Store refresh token as Postman variable*

4. **Tests:**
   ```javascript
   pm.test("Status code is 200", function () {
       pm.response.to.have.status(200);
   });

   pm.test("Response has new access token", function () {
       var jsonData = pm.response.json();
       pm.expect(jsonData.accessToken).to.be.a('string');
       pm.expect(jsonData.accessToken.length).to.be.greaterThan(10);
       
       // Update environment variable with new token
       pm.environment.set("accessToken", jsonData.accessToken);
   });
   ```

## Token Refresh Flow Diagram

```
┌─────────┐     Invalid/Expired     ┌─────────────┐
│ Client  │ ───────────────────────▶│ API Server  │
│         │      Access Token       │             │
└─────────┘                         └─────────────┘
       │                                  │
       │       401 Unauthorized           │
       │◀─────────────────────────────────│
       │                                  │
       │ POST /auth/refresh-token         │
       │ with refresh token               │
       │─────────────────────────────────▶│
       │                                  │
       │     200 OK with new              │
       │     access token                 │
       │◀─────────────────────────────────│
       │                                  │
       │ Retry original request           │
       │ with new token                   │
       │─────────────────────────────────▶│
```

## Best Practices

### When to Refresh
- **Proactive Refresh:** Refresh token 5-10 minutes before expiration
- **Reactive Refresh:** When receiving 401 Unauthorized response
- **Scheduled Refresh:** Implement background timer for long sessions

### Storage Security
```javascript
// Web: Use HttpOnly cookies for refresh tokens
document.cookie = `refreshToken=${refreshToken}; HttpOnly; Secure; SameSite=Strict; Max-Age=${30*24*60*60}`;

// Mobile: Use secure storage (Keychain/Keystore)
```

### Implementation Pattern
```javascript
class AuthService {
  constructor() {
    this.accessToken = null;
    this.refreshToken = null;
    this.refreshPromise = null; // Prevent duplicate refresh requests
  }
  
  async refresh() {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }
    
    this.refreshPromise = this.performRefresh();
    const token = await this.refreshPromise;
    this.refreshPromise = null;
    return token;
  }
  
  async performRefresh() {
    // Call refresh-token endpoint
    // Handle errors
    // Return new access token
  }
}
```

### Error Handling
```javascript
// Example comprehensive error handling
async function handleApiError(error, originalRequest) {
  if (error.status === 401 && !originalRequest._retry) {
    originalRequest._retry = true;
    
    try {
      const newToken = await refreshAccessToken();
      originalRequest.headers.Authorization = `Bearer ${newToken}`;
      return fetch(originalRequest.url, originalRequest);
    } catch (refreshError) {
      // Redirect to login
      clearAuthData();
      redirectToLogin();
      throw new Error('Session expired. Please login again.');
    }
  }
  
  throw error;
}
```

## Security Considerations

### Refresh Token Protection
- Store refresh tokens securely (HttpOnly cookies, secure storage)
- Implement token rotation (issue new refresh token on each refresh)
- Set reasonable expiration (7-30 days)
- Allow revocation via logout

### Prevention Strategies
- **Reuse Detection:** Reject used refresh tokens
- **Device Binding:** Associate tokens with device fingerprint
- **IP Validation:** Optionally validate request IP matches original
- **Rate Limiting:** Limit refresh attempts per token

### Revocation Scenarios
Refresh tokens should be revoked when:
1. User explicitly logs out
2. Password changed
3. Suspicious activity detected
4. Account deactivated
5. Token reported as compromised

---

## Related Endpoints
- [POST /auth/login](./login.md) - Initial authentication
- [POST /auth/logout](./logout.md) - Revoke refresh token
- [POST /auth/register](./register.md) - Create new account
- [Error Responses](../../errors.md) - Error handling details

## Notes
- Refresh tokens have longer lifespan than access tokens
- Implement proper error handling for network failures
- Consider implementing sliding sessions
- Monitor refresh patterns for security analysis