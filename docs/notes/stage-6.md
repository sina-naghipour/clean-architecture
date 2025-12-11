# Stage 6 - Containers & Deployment

## before status

**Quick Stage 6 validation – what passes vs what will get you rejected**

| Area                       | Status   | Comment (short & brutal)                                                                 |
|----------------------------|----------|-------------------------------------------------------------------------------------------|
| Slim images                | Pass     | All use `python:3.11-slim` → good                                                        |
| Non-root user              | Fail     | Only **statics** has `USER appuser`. The other 5 services still run as root → instant fail |
| Multi-stage builds         | Fail     | Zero multi-stage → you’re shipping build tools & source leaks → fail                      |
| HEALTHCHECK instruction    | Fail     | None of the Dockerfiles have `HEALTHCHECK` → NGINX/Swarm can’t know if app is dead        |
| Pin exact base image tag   | Fail     | `python:3.11-slim` (no tag) is moving target → use `python:3.11.10-slim-bookworm`        |
| Dev volume mounts          | Fail     | `./services/*/app:/app` in production-like stage → code is mutable at runtime → fail     |
| Image size                 | Fail     | Current images are ~350–450 MB each. Expected < 120 MB after proper multi-stage + non-root|
| Zero-downtime / replicas   | Fail     | No `deploy: replicas:` or Swarm mode used → no blue/green or rolling swap shown           |
| NGINX config               | Fail  | no rate limits, no healthchecks  |

## non root:

why should we not use root for our container? -> because if an attacker escapes the container, they become root on the host.

a container breakout + root inside = full host takeover.

an important note in this section is that : `Non-root users should not be creating system directories.`

```Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

RUN mkdir -p static/img && chmod 755 static/img

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8005

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
```

look at the order of building the docker image.

run `apt`, `pip` and system wide installations as root, use `--no-cache-dir`, and run `mkdir` as root. lastly switch to user and run the service.

### Good note.

my approach before applying non root user, was to use root for everything. upon migrating to a user, i got hit with a permission denied error.

`the issue` : i am mounting host directories into my container, as `/app` but my container is running as non-root `appuser`.

`the solution` : a solution that would work on windows and linux, was to use named docker volumes instead of host bind mounts for `/app`.

```yaml
  auth:
    build: ./services/auth
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - DATABASE_URL=postgresql+asyncpg://postgres:toor@auth_db:5432/auth
    volumes:
      - auth_app_data:/app
    depends_on:
      - auth_db
    networks:
      - app-network

#at the buttom 
volumes:
  auth_app_data:

```

## slim images:

what is slim image? a stripped down to include only the essential packages needed for your application to run.

it excludes unnecessary tools, documentation and dev libraries, that you do not need in production.

smaller size, better security, faster builds, production focus.

## health check:

added health checks to `docker-compose`.

sample code for database:

```yaml
  auth_db:
    image: postgres:15
    environment:
      POSTGRES_DB: auth
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: toor
    ports:
      - "5432:5432"
    volumes:
      - auth_db_data:/var/lib/postgresql/data
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d auth"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 5s
```

sample code for service:

```yaml
  products:
    build: ./services/products
    ports:
      - "8003:8003"
    environment:
      - ENVIRONMENT=production
      - MONGODB_URI=mongodb://mongodb:27017/
      - MONGODB_DB_NAME=product_db
      - STATIC_SERVICE_URL=http://statics:8005
    depends_on:
      mongodb:
        condition: service_healthy
      statics:
        condition: service_started
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "python -c 'import urllib.request; urllib.request.urlopen(\"http://localhost:8003/health\")' || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 5s
```

**Note:** we use `python` not `curl`, to keep our container as `slim` as possible.

## a time wasting mistake:

the fucking app directory was being built inside the app directory, i was being stupid and not checking it, it wasted huge amount of time.

do
```Dockerfile
WORKDIR /app
# this is right
COPY app/ .
# the below is wrong
COPY . .
```

## Nginx -> timeouts:

```text
location /api/profile/ {
    proxy_pass http://profile_backend/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    #----------- HERE -------------
    proxy_connect_timeout 30s;
    proxy_send_timeout 30s;
    proxy_read_timeout 30s;
    #----------- HERE -------------
    limit_req zone=api_limit burst=20 nodelay;
}
```
## Nginx -> Buffering:



```text
location /api/static/ {
    proxy_pass http://static_backend/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    #----------- HERE -------------
    proxy_buffering on;
    proxy_buffer_size 4k;
    proxy_buffers 8 4k;
    proxy_max_temp_file_size 0;
    #----------- HERE -------------

    expires 1y;
    add_header Cache-Control "public, immutable";

    limit_req zone=api_limit burst=20 nodelay;
}
```

## Nginx -> Rate Limits:

```text
    # rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
```


## Nginx -> gzip:

```text
  gzip on;
  gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
  gzip_min_length 256;
  gzip_comp_level 5;
  gzip_vary on;
```

## Nginx -> Basic Caching:

```text
  expires 1y;
  add_header Cache-Control "public, immutable";
```

## Deployment Strategies:

### Blue/Green Deployment (A `zero downtime` Strategy)

overview: two identical production environments running simultaneously, instant traffc switching between environments.

complete rollback capability.

Blue Environment and Green Environment.

In essence (how the fuck do you spell this :((( ) one environment is only actively responding to traffic.

while the other remains idle.

when the new version of the application is ready it is deployed to the inactive environment.

after thorough testing, traffic is switched from the old application to the newly updated one(6 coffees down, 6 hours of sleep, spelling fucked.)

this approach minimizes downtime, and represent an easy way to revert to the old version, if new errors arise.

```yaml
services:
  app-blue:
    image: myapp:v1.0
    ports: ["8080:80"]
  app-green:
    image: myapp:v2.0
    ports: ["8081:80"]
```

deployment steps :

1. Deploy to inactive environment.

2. run health checks.

3. switch to load balancer.

4. monitor new version.

## Rolling Deployment:

Gradual replacement of instances.

maintains service availability.

resource-efficient approach.

here is kubernetes implementation.

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  replicas: 4
```

## Blue/Green Deployment in Action:

while the service is running, i added the code below to my `docker-compose`.

```yaml
  products_green:
    build: ./services/products
    ports:
      - "8013:8003"
    environment:
      - ENVIRONMENT=production
      - MONGODB_URI=mongodb://mongodb:27017/
      - MONGODB_DB_NAME=product_db
      - STATIC_SERVICE_URL=http://statics:8005
    depends_on:
      mongodb:
        condition: service_healthy
      statics:
        condition: service_started
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "python -c 'import urllib.request; urllib.request.urlopen(\"http://localhost:8003/health\")' || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 5s
```

now:

- Products Blue → http://localhost:8003

- Products Green → http://localhost:8013

to run this container without any downtime we run:

```bash
docker compose up -d products_green
```

to `re-up` a container we do:

```bash
docker compose up -d --build products_green
```
 
we run tests.

we made green container pass all tests and fixed it.

a weird issue was that statics seem to be restarting everytime we up'ed the green container.

to ensure whether it is being restarted or not we do:

```bash
# Get statics container ID before
docker-compose ps -q statics

docker-compose up -d products_green

docker-compose ps -q statics
# If same ID: no restart
# If different ID: restarted
```

## K6:

k6 is a performance testing tool.

 