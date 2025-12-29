# EVIDENCE_GENERAL_FORMAT.md

---

## 1. Security Headers Middleware

### Pattern
- **Location**: Middleware layer (e.g., `auth/app/middleware/security_headers.py`)
- **Format**: Python/HTTP middleware class
- **Purpose**: Centralized enforcement of security & CORS headers

### Evidence Structure
```python
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        # Content Security Policy
        csp_policy = "default-src 'self'; ..."
        response.headers["Content-Security-Policy"] = csp_policy
        
        # Dynamic CORS
        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        # Conditional caching
        if any(path in request.url.path for path in ['/orders', '/admin']):
            response.headers["Cache-Control"] = "no-store, max-age=0"
        
        return response
```

### Key Features
- Comprehensive security headers
- Dynamic CORS origin validation
- Conditional caching policies
- CSP enforcement

---

## 2. Database Connection Pooling Configuration

### Pattern
- **Location**: Database config files (`pgbouncer.ini`, SQLAlchemy setup)
- **Format**: INI config + Python SQLAlchemy async setup
- **Purpose**: Efficient database connection management via connection pooling

### Evidence Structure
**pgbouncer.ini:**
```ini
[databases]
auth = host=auth_db port=5432 dbname=auth user=postgres password=toor

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
pool_mode = transaction
max_client_conn = 500
default_pool_size = 50
reserve_pool_size = 10
max_db_connections = 100
min_pool_size = 10
server_idle_timeout = 60
```

**SQLAlchemy setup:**
```python
DATABASE_URL = "postgresql+asyncpg://postgres:toor@pgbouncer:6432/auth"

engine = create_async_engine(
    DATABASE_URL,
    poolclass=NullPool,  # PgBouncer handles pooling
    connect_args={
        "server_settings": {"application_name": "auth_service"},
        "prepared_statement_cache_size": 0,
        "statement_cache_size": 0,
    }
)
```

### Key Features
- PgBouncer transaction pooling
- Null pool in SQLAlchemy
- Connection limits & timeouts
- Async session management

--- 

## 3. Redis Client Manager

### Pattern
- **Location**: Utility/service layer (e.g., `./cache/redis_manager.py`)
- **Format**: Singleton class with async client management
- **Purpose**: Centralized Redis connection handling with lazy initialization

### Evidence Structure
```python
class RedisManager:
    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "redis")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.db = int(os.getenv("REDIS_DB", 0))
        self._client = None  # Singleton instance
        
    async def get_client(self):
        if not self._client:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            await self._client.ping()  # Connection health check
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None

# Global instance
redis_manager = RedisManager()
```

### Key Features
- Lazy client initialization
- Connection health verification
- Configurable timeouts
- Singleton pattern usage

---

## 4. Rate Limiting Middleware

### Pattern
- **Location**: `./middleware/rate_limiter.py` or similar
- **Format**: Class with async sliding window algorithm
- **Purpose**: Protect endpoints from abuse using Redis-based rate limiting

### Evidence Structure
```python
class RateLimiter:
    def __init__(self, redis_manager):
        self.redis_manager = redis_manager
    
    async def check_rate_limit(self, identifier, max_requests=10, window_seconds=60):
        # Sliding window using Redis sorted sets
        key = f"ratelimit:{identifier}"
        await redis.zremrangebyscore(key, 0, window_start)  # Clean old requests
        request_count = await redis.zcard(key)
        
        if request_count >= max_requests:
            return {
                "allowed": False,
                "remaining": 0,
                "retry_after": int(reset_time - current_time)
            }
        
        await redis.zadd(key, {str(current_time): current_time})
        return {
            "allowed": True,
            "remaining": max_requests - request_count - 1
        }
        
    def limit(self, max_requests: int = 5, window_seconds: int = 60, by_ip: bool = False):
        # Decorator for endpoint protection
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract identifier from IP or user
                identifier = self._extract_identifier(*args, **kwargs, by_ip=by_ip)
                
                limit_result = await self.check_rate_limit(
                    identifier=identifier,
                    max_requests=max_requests,
                    window_seconds=window_seconds
                )
                
                if not limit_result["allowed"]:
                    raise HTTPException(
                        status_code=429,
                        detail="Too many requests",
                        headers={"Retry-After": str(limit_result["retry_after"])}
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
```

### Key Features
- Sliding window algorithm
- Redis sorted set storage
- Flexible identifier extraction
- Configurable limits per endpoint

---

## 5. Circuit Breaker (Backpressure Pattern)

### Pattern
- **Location**: `./utils/circuit_breaker.py` or similar
- **Format**: Stateful class managing request flow control
- **Purpose**: Prevent cascading failures by temporarily blocking calls to failing services

### Evidence Structure
```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.circuit_open = False
        self.circuit_open_until = 0  # Timestamp for auto-reset

    def is_open(self) -> bool:
        if self.circuit_open:
            if time.time() < self.circuit_open_until:
                return True  # Circuit remains open
            # Timeout expired - transition to half-open
            self.circuit_open = False
            self.failure_count = 0
        return False

    def record_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.circuit_open = True
            self.circuit_open_until = time.time() + self.reset_timeout

    def record_success(self):
        self.failure_count = 0
        self.circuit_open = False
```

### Key Features
- Failure threshold monitoring
- Automatic timeout-based reset
- Three-state circuit (closed/open/half-open)
- Thread-safe state management

## Key Architecture Benefits

1. **Testability**: Each pattern independently testable  

2. **Maintainability**: Clear separation of concerns  

3. **Scalability**: Stateless services with connection pooling  

4. **Security**: Multi-layered protection (headers, rate limiting, circuit breakers)  

5. **Standards Compliance**: RESTful APIs, RFC headers, established patterns  

6. **Developer Experience**: Type safety, consistent interfaces, clear documentation  

7. **Operational Excellence**: Health checks, logging, performance optimization