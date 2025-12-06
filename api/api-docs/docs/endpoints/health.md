# Health Endpoints

## Overview
The Ecommerce API provides health-check endpoints to monitor service status and readiness. These endpoints are essential for monitoring, load balancing, and ensuring service reliability.

---

## GET /health
**Health Check** - Returns comprehensive service health status

**Tags:** Health

### Description
This endpoint checks if the service is running and healthy. It returns detailed information about the service's current state including its environment and timestamp.

### Response
**200 OK - Service health status**

```json
{
  "status": "healthy",
  "service": "ecommerce-api",
  "timestamp": "2023-10-01T12:00:00Z",
  "environment": "development"
}
```

**Response Fields:**

| Field | Type | Description | Possible Values |
|-------|------|-------------|-----------------|
| `status` | string | Current health status | `healthy`, `unhealthy` |
| `service` | string | Service identifier | ecommerce-api |
| `timestamp` | string | Current UTC timestamp in ISO 8601 format | - |
| `environment` | string | Deployment environment | `development`, `staging`, `production` |

### Example Request

**cURL:**
```bash
curl -X GET "http://localhost:8000/api/health"
```

**JavaScript (Fetch):**
```javascript
const response = await fetch('http://localhost:8000/api/health');
const health = await response.json();
console.log(health);
```

**Python:**
```python
import requests
response = requests.get("http://localhost:8000/api/health")
print(response.json())
```

### Use Cases
- Load balancer health checks
- Service monitoring and alerting
- Infrastructure health dashboards
- Automated recovery systems

---

## GET /ready
**Readiness Check** - Verifies service is ready to accept requests

**Tags:** Health

### Description
This endpoint checks if the service is ready to handle traffic. It verifies that all required dependencies (database, cache, etc.) are available and the service is fully initialized.

### Response
**200 OK - Service readiness status**

```json
{
  "status": "ready",
  "service": "ecommerce-api",
  "timestamp": "2023-10-01T12:00:00Z"
}
```

**Response Fields:**

| Field | Type | Description | Possible Values |
|-------|------|-------------|-----------------|
| `status` | string | Readiness status | `ready`, `not ready` |
| `service` | string | Service identifier | ecommerce-api |
| `timestamp` | string | Current UTC timestamp in ISO 8601 format | - |

### Example Request

**cURL:**
```bash
curl -X GET "http://localhost:8000/api/ready"
```

**Postman:**
1. Create new GET request
2. URL: `http://localhost:8000/api/ready`
3. Send request

### Use Cases
- Kubernetes readiness probes
- Service startup verification
- Traffic routing decisions
- Blue-green deployment checks

---

## GET /info
**Service Information** - Returns basic service metadata

**Tags:** Root

### Description
This endpoint provides general information about the API service, including version, documentation links, and related endpoints.

### Response
**200 OK - Service information**

```json
{
  "message": "Ecommerce API Service",
  "version": "1.1.0",
  "environment": "development",
  "docs": "https://api.example.com/docs",
  "health": "/health",
  "ready": "/ready"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | Service name or greeting |
| `version` | string | API version number |
| `environment` | string | Current environment |
| `docs` | string | URL to API documentation |
| `health` | string | Path to health endpoint |
| `ready` | string | Path to readiness endpoint |

### Example Request

```bash
curl -X GET "http://localhost:8000/api/info"
```

---

## Implementation Notes

### Health vs Readiness
- **Health (`/health`)**: Is the service running? (liveness)
- **Readiness (`/ready`)**: Can the service handle requests? (readiness)

### Best Practices
1. **Monitoring**: Set up alerts based on health status changes
2. **Frequency**: Check health every 30-60 seconds for monitoring
3. **Timeout**: Configure appropriate timeout values (5-10 seconds)
4. **Dependencies**: Extend readiness checks to verify database, cache, etc.

### Security Considerations
- These endpoints are typically public and don't require authentication
- Consider rate limiting to prevent abuse
- Be cautious about exposing sensitive information in responses

---

## Related Endpoints
- [Authentication](../auth/login.md) - Secure API access
- [Products](../products/list-products.md) - Product catalog
- [Errors](../../errors.md) - Error handling and status codes