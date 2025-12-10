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

COPY . .

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

