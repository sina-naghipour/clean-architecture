# POST /auth/logout

**Logout User** - Revoke refresh token and end session

**Tags:** Auth

---

## Description
Invalidate the current user's refresh token, effectively logging them out from all devices or the current session. This endpoint prevents the refresh token from being used to obtain new access tokens.

## Authentication
**Required:** Bearer Token (Access Token)

### Headers
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

## Request
No request body required.

## Responses

### 204 No Content - Successfully logged out
**Response Body:** None

**Description:** Refresh token has been revoked. The client should clear all stored tokens.

### 400 Bad Request - Invalid request
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/bad-request",
  "title": "Bad Request",
  "status": 400,
  "detail": "Invalid authorization header.",
  "instance": "/auth/logout"
}
```

### 401 Unauthorized - Invalid or missing token
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/unauthorized",
  "title": "Unauthorized",
  "status": 401,
  "detail": "Missing or invalid Authorization header.",
  "instance": "/auth/logout"
}
```

**Causes:**
- No Authorization header provided
- Invalid access token format
- Expired access token
- Malformed JWT

### 500 Internal Server Error
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/internal",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "Unexpected server error.",
  "instance": "/auth/logout"
}
```

## Examples

### cURL
```bash
# Logout with valid access token
curl -X POST "http://localhost:8000/api/auth/logout" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json"
```

### JavaScript (Fetch)
```javascript
async function logout() {
  const accessToken = localStorage.getItem('accessToken');
  
  if (!accessToken) {
    console.log('No access token found - already logged out');
    clearLocalAuthData();
    return;
  }
  
  try {
    const response = await fetch('http://localhost:8000/api/auth/logout', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (response.status === 204) {
      console.log('Successfully logged out from server');
    } else if (response.status === 401) {
      console.log('Token already expired or invalid');
    } else {
      console.warn('Logout response:', response.status);
    }
  } catch (error) {
    console.error('Network error during logout:', error);
  } finally {
    // Always clear local data even if server request fails
    clearLocalAuthData();
    redirectToLogin();
  }
}

function clearLocalAuthData() {
  // Clear tokens from storage
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
  localStorage.removeItem('user');
  
  // Clear cookies if used
  document.cookie = 'refreshToken=; Max-Age=0; path=/;';
  
  // Clear any application state
  // appState.user = null;
  // appState.isAuthenticated = false;
}

function redirectToLogin() {
  // Redirect to login page
  window.location.href = '/login';
}

// Usage
document.getElementById('logout-btn').addEventListener('click', logout);
```

### React Example
```jsx
import { useAuth } from '../contexts/AuthContext';

function LogoutButton() {
  const { logout, isAuthenticated } = useAuth();
  
  if (!isAuthenticated) {
    return null;
  }
  
  return (
    <button 
      onClick={logout}
      className="logout-button"
    >
      Logout
    </button>
  );
}

// Auth Context Example
const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [accessToken, setAccessToken] = useState(null);
  
  const logout = async () => {
    if (accessToken) {
      try {
        await fetch('http://localhost:8000/api/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
          }
        });
      } catch (error) {
        console.error('Logout error:', error);
      }
    }
    
    // Clear local state
    setUser(null);
    setAccessToken(null);
    localStorage.clear();
    sessionStorage.clear();
    
    // Redirect
    window.location.href = '/login';
  };
  
  return (
    <AuthContext.Provider value={{ user, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
```

### Python
```python
import requests
import json

class AuthClient:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        
    def logout(self):
        """Logout user and clear tokens."""
        if not self.access_token:
            print("No active session")
            self.clear_tokens()
            return True
            
        url = "http://localhost:8000/api/auth/logout"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, headers=headers)
            
            if response.status_code == 204:
                print("Successfully logged out")
            elif response.status_code == 401:
                print("Token already expired")
            else:
                print(f"Unexpected response: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
        finally:
            # Always clear local tokens
            self.clear_tokens()
            return True
            
    def clear_tokens(self):
        """Clear all stored authentication tokens."""
        self.access_token = None
        self.refresh_token = None
        
        # Clear from file storage
        try:
            with open('tokens.json', 'w') as f:
                json.dump({}, f)
        except:
            pass
            
        print("Local tokens cleared")
        
    def is_logged_in(self):
        """Check if user is logged in."""
        return self.access_token is not None

# Usage
client = AuthClient()
# ... after login ...
client.logout()
```

### Postman
1. **Create Request:**
   - **Method:** POST
   - **URL:** `http://localhost:8000/api/auth/logout`

2. **Headers:**
   ```
   Key: Authorization
   Value: Bearer {{accessToken}}
   
   Key: Content-Type
   Value: application/json
   ```

3. **Pre-request Script:**
   ```javascript
   // Ensure access token is available
   if (!pm.environment.get("accessToken")) {
       console.warn("No access token found. Login first.");
   }
   ```

4. **Tests:**
   ```javascript
   pm.test("Logout successful", function () {
       pm.response.to.have.status(204);
   });
   
   pm.test("Clear environment variables", function () {
       pm.environment.unset("accessToken");
       pm.environment.unset("refreshToken");
       pm.environment.unset("userId");
       
       console.log("Tokens cleared from environment");
   });
   ```

## Logout Scenarios

### 1. User-Initiated Logout
```javascript
// User clicks logout button
// → Call /auth/logout endpoint
// → Clear local tokens
// → Redirect to login page
```

### 2. Token Expiration
```javascript
// Access token expires
// → API returns 401
// → Attempt token refresh
// → If refresh fails → auto-logout
// → Clear tokens and redirect
```

### 3. Multi-Device Logout
```javascript
// Logout from all devices
async function logoutAllDevices(userId) {
  // Call enhanced logout endpoint if available
  // Or implement token invalidation list
  // Clear all refresh tokens for user
}
```

### 4. Session Timeout
```javascript
// Implement session timeout
const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes
let lastActivity = Date.now();

function resetSessionTimer() {
  lastActivity = Date.now();
}

function checkSession() {
  if (Date.now() - lastActivity > SESSION_TIMEOUT) {
    logout();
  }
}

// Reset on user activity
document.addEventListener('click', resetSessionTimer);
document.addEventListener('keypress', resetSessionTimer);
setInterval(checkSession, 60000); // Check every minute
```

## Security Best Practices

### Client-Side
1. **Always Clear Tokens:**
   ```javascript
   // Comprehensive cleanup
   function secureLogout() {
     // HTTP-only cookies (server clears)
     document.cookie = 'refreshToken=; Max-Age=0; path=/; Secure; SameSite=Strict';
     
     // Local storage
     localStorage.removeItem('accessToken');
     localStorage.removeItem('refreshToken');
     localStorage.removeItem('userData');
     
     // Session storage
     sessionStorage.clear();
     
     // Service worker caches
     if ('caches' in window) {
       caches.keys().then(cacheNames => {
         cacheNames.forEach(cacheName => caches.delete(cacheName));
       });
     }
     
     // Redirect with cache busting
     window.location.href = '/login?logout=true&t=' + Date.now();
   }
   ```

2. **Prevent Token Leakage:**
   ```javascript
   // Clear from memory
   let accessToken = null; // Allow garbage collection
   ```

### Server-Side
1. **Token Revocation:**
   ```javascript
   // Store revoked tokens in Redis with TTL
   await redis.set(`revoked:${refreshTokenId}`, '1', 'EX', 30 * 24 * 60 * 60);
   ```

2. **Security Headers:**
   ```javascript
   // Add security headers on logout
   res.setHeader('Clear-Site-Data', '"cookies", "storage"');
   ```

3. **Audit Logging:**
   ```sql
   -- Log logout events
   INSERT INTO audit_logs (user_id, action, ip_address, user_agent)
   VALUES (?, 'logout', ?, ?);
   ```

## Implementation Considerations

### Single vs All Device Logout
```javascript
// Option 1: Logout current device only (default)
POST /auth/logout
Authorization: Bearer <access_token>

// Option 2: Logout all devices (enhanced)
POST /auth/logout/all
Authorization: Bearer <access_token>
```

### Concurrent Session Management
```javascript
// Track active sessions
class SessionManager {
  constructor() {
    this.activeSessions = new Map(); // userId → [sessionIds]
  }
  
  async logoutUser(userId, sessionId = null) {
    if (sessionId) {
      // Logout specific session
      this.revokeSession(sessionId);
    } else {
      // Logout all sessions for user
      this.revokeAllSessions(userId);
    }
  }
}
```

## Error Recovery

### Network Issues During Logout
```javascript
async function logoutWithRetry(maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      await logout();
      return; // Success
    } catch (error) {
      if (i === maxRetries - 1) {
        console.error('Logout failed after retries:', error);
        // Fallback: Clear local data anyway
        clearLocalAuthData();
      }
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
}
```

### Graceful Degradation
```javascript
// If server unavailable, still clear local data
function gracefulLogout() {
  const serverAvailable = navigator.onLine;
  
  if (serverAvailable) {
    // Try server logout first
    logout().catch(() => {
      console.warn('Server logout failed, clearing local data');
      clearLocalAuthData();
    });
  } else {
    // Offline - clear local data
    clearLocalAuthData();
    showMessage('Logged out locally. Server sync will occur when online.');
  }
}
```

---

## Related Endpoints
- [POST /auth/login](./login.md) - Authenticate and get tokens
- [POST /auth/refresh-token](./refresh-token.md) - Refresh access token
- [POST /auth/register](./register.md) - Create new account
- [Error Responses](../../errors.md) - Error handling details

## Notes
- Logout should be idempotent (calling multiple times is safe)
- Always clear client-side tokens even if server request fails
- Consider implementing "Remember Me" functionality with longer-lived tokens
- For enhanced security, implement logout from all devices endpoint
- Log logout events for security monitoring

## Browser Compatibility
For clearing cookies across browsers:
```javascript
// Standard method
document.cookie = 'token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';

// For older browsers
function clearAllCookies() {
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    const eqPos = cookie.indexOf('=');
    const name = eqPos > -1 ? cookie.substr(0, eqPos) : cookie;
    document.cookie = name + '=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/';
  }
}
```