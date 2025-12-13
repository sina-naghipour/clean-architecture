# EVIDENCE_GENERAL_FORMAT.md

## 1. Non-root, Slim Images, Healthchecks for Docker.

### Pattern
- **Location**: `{service}/Dockerfile`
- **Technology**: docker
- **Purpose**: create an isolated environment for our service.

### Evidence Structure
```Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY app/ .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8003

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
```

```yaml
    healthcheck:
      test: ["CMD-SHELL", "python -c 'import urllib.request; urllib.request.urlopen(\"http://localhost:8001/health\")' || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 5s
```

### Key Features
- **Security-first containerization with non-root execution**
- **Production resilience through comprehensive healthchecks**
- **Deterministic deployments with optimized layer caching**

---

## 2. routing, timeouts, buffering, rate limits, gzip, basic caching.
### Pattern
- **Location**: `nginx/nginx.conf`
- **Technology**: nginx
- **Purpose**: act as api gateway and a proxy.

```conf
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
gzip_min_length 256;
gzip_comp_level 5;
gzip_vary on;
```

```conf
proxy_buffering on;
proxy_buffer_size 4k;
proxy_buffers 8 4k;
proxy_max_temp_file_size 0;
```

```conf
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=200r/s;
```
### Key Features
- **Performance optimization with gzip and buffering**
- **Traffic management through rate limiting**
- **Resource protection with connection controls**

---

## 3. K6
### Pattern
- **Location**: `services/k6/slo-test.js`
- **Technology**: k6
- **Purpose**: test server's performance.

```javascript
export default function () {
  const endpoints = [
    '/health',
    '/api/auth/health',
    '/api/products/health',
    '/api/orders/health',
    '/api/static/health',
    '/api/profile/health',
    '/api/cart/health',
  ];
```

```javascript
export const options = {
  scenarios: {
    smoke: {
      executor: 'constant-vus',
      vus: 5,
      duration: '1m',
      startTime: '0s',
      tags: { test_type: 'smoke' },
    },
    load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 20 },
        { duration: '2m', target: 100 },
        { duration: '1m', target: 0 },
      ],
      startTime: '20s',
      tags: { test_type: 'load' },
    },
  },
```
### Key Features
- **Multi-scenario load testing with varied execution strategies**
- **Real-world simulation through gradual user ramp-up**
- **Performance benchmarking with structured testing stages**

---



## Key Architecture Benefits

1. **Testability**: Each Docker container, nginx configuration, and K6 test scenario can be validated independently
2. **Maintainability**: Clear separation between gateway configuration, service containers, and performance testing
3. **Scalability**: Stateless containers with proper healthchecks enable horizontal scaling
4. **Security**: Non-root containers, rate limiting, and buffering controls provide layered protection
5. **Standards Compliance**: Docker best practices, nginx optimization standards, and K6 testing methodologies
6. **Developer Experience**: Consistent containerization, clear gateway rules, and performance benchmarking tools
7. **Operational Excellence**: Health monitoring, traffic management, and performance validation through comprehensive testing