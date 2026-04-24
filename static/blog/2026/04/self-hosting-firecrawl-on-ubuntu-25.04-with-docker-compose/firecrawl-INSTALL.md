# Firecrawl Self-Hosted Install — Agentic Task File

> **For AI agents (Claude Code, Codex, etc.):** This file is a structured installation task. Execute each phase in order. Validate each success criterion before proceeding. If a step fails, follow the recovery instructions before continuing — do not skip ahead. All commands target Ubuntu 25.04.

---

## Context

You are installing Firecrawl, an open-source web scraping and crawling API, on the local Ubuntu host using Docker Compose. You will use pre-built GHCR images rather than building from source. The install requires creating exactly two files (`docker-compose.yaml` and `.env`), then starting the stack and validating it.

**Working directory:** `~/firecrawl`  
**API port:** 3002  
**Total services:** 5 containers

---

## Phase 1 — Verify Prerequisites

```bash
# Check OS
lsb_release -rs   # must be 25.04 or compatible Ubuntu

# Check available memory — minimum 6 GB free recommended
free -h

# Check Docker
docker --version
docker compose version

# If Docker is not installed:
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
```

**Success criteria:**
- `docker --version` returns without error
- `docker compose version` returns v2.x or higher
- Host has at least 6 GB RAM available

---

## Phase 2 — Create Working Directory

```bash
mkdir -p ~/firecrawl
cd ~/firecrawl
```

**Success criteria:** `pwd` returns `~/firecrawl` or its absolute equivalent.

---

## Phase 3 — Write `docker-compose.yaml`

Write the following content exactly to `~/firecrawl/docker-compose.yaml`. Do not modify it — all deviations from the upstream file are intentional fixes for known runtime failures documented in the comments.

```yaml
name: firecrawl

x-common-service: &common-service
  image: ghcr.io/firecrawl/firecrawl:latest
  ulimits:
    nofile:
      soft: 65535
      hard: 65535
  networks:
    - backend
  extra_hosts:
    - "host.docker.internal:host-gateway"
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
      compress: "true"

x-common-env: &common-env
  PORT: ${INTERNAL_PORT:-3002}
  HOST: ${HOST:-0.0.0.0}
  REDIS_URL: ${REDIS_URL:-redis://redis:6379}
  REDIS_RATE_LIMIT_URL: ${REDIS_RATE_LIMIT_URL:-redis://redis:6379}
  PLAYWRIGHT_MICROSERVICE_URL: ${PLAYWRIGHT_MICROSERVICE_URL:-http://playwright-service:3000/scrape}
  USE_DB_AUTHENTICATION: ${USE_DB_AUTHENTICATION:-false}
  OPENAI_API_KEY: ${OPENAI_API_KEY:-}
  OLLAMA_BASE_URL: ${OLLAMA_BASE_URL:-}
  MODEL_NAME: ${MODEL_NAME:-}
  MODEL_EMBEDDING_NAME: ${MODEL_EMBEDDING_NAME:-}
  BULL_AUTH_KEY: ${BULL_AUTH_KEY:-}
  LOGGING_LEVEL: ${LOGGING_LEVEL:-info}
  PROXY_SERVER: ${PROXY_SERVER:-}
  PROXY_USERNAME: ${PROXY_USERNAME:-}
  PROXY_PASSWORD: ${PROXY_PASSWORD:-}
  BLOCK_MEDIA: ${BLOCK_MEDIA:-false}
  ALLOW_LOCAL_WEBHOOKS: ${ALLOW_LOCAL_WEBHOOKS:-false}
  SEARXNG_ENDPOINT: ${SEARXNG_ENDPOINT:-}
  POSTHOG_API_KEY: ${POSTHOG_API_KEY:-}
  POSTHOG_HOST: ${POSTHOG_HOST:-}
  SLACK_WEBHOOK_URL: ${SLACK_WEBHOOK_URL:-}
  LLAMAPARSE_API_KEY: ${LLAMAPARSE_API_KEY:-}
  MAX_CPU: ${MAX_CPU:-0.8}
  MAX_RAM: ${MAX_RAM:-0.8}
  POSTGRES_HOST: nuq-postgres
  POSTGRES_PORT: 5432
  POSTGRES_DB: ${POSTGRES_DB:-firecrawl}
  POSTGRES_USER: ${POSTGRES_USER:-firecrawl}
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-firecrawl}
  NUQ_RABBITMQ_URL: amqp://${RABBITMQ_USER:-firecrawl}:${RABBITMQ_PASSWORD:-firecrawl}@rabbitmq:5672

services:
  playwright-service:
    image: ghcr.io/firecrawl/playwright-service:latest
    environment:
      PORT: 3000
      PROXY_SERVER: ${PROXY_SERVER:-}
      PROXY_USERNAME: ${PROXY_USERNAME:-}
      PROXY_PASSWORD: ${PROXY_PASSWORD:-}
      ALLOW_LOCAL_WEBHOOKS: ${ALLOW_LOCAL_WEBHOOKS:-false}
      BLOCK_MEDIA: ${BLOCK_MEDIA:-false}
      MAX_CONCURRENT_PAGES: ${CRAWL_CONCURRENT_REQUESTS:-10}
    networks:
      - backend
    cpus: 2.0
    mem_limit: 4G
    memswap_limit: 4G
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        compress: "true"
    tmpfs:
      - /tmp/.cache:noexec,nosuid,size=512m

  api:
    <<: *common-service
    environment:
      <<: *common-env
    depends_on:
      redis:
        condition: service_started
      playwright-service:
        condition: service_started
      nuq-postgres:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
    ports:
      - "${PORT:-3002}:${INTERNAL_PORT:-3002}"
    command: ["node", "dist/src/harness.js", "--start-docker"]
    cpus: 4.0
    mem_limit: 8G
    memswap_limit: 8G

  redis:
    image: redis:alpine
    networks:
      - backend
    volumes:
      - redis-data:/data
    cpus: 0.25
    mem_limit: 256M
    memswap_limit: 256M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        compress: "true"

  rabbitmq:
    image: rabbitmq:3-management
    networks:
      - backend
    volumes:
      - rabbitmq-data:/var/lib/rabbitmq
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER:-firecrawl}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD:-firecrawl}
    cpus: 0.5
    mem_limit: 512M
    memswap_limit: 512M
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 5s
      timeout: 10s
      retries: 10
      start_period: 30s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        compress: "true"

  nuq-postgres:
    image: ghcr.io/firecrawl/nuq-postgres:latest
    command: postgres -c cron.database_name=${POSTGRES_DB:-firecrawl}
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-firecrawl}
      POSTGRES_USER: ${POSTGRES_USER:-firecrawl}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-firecrawl}
    networks:
      - backend
    volumes:
      - postgres-data:/var/lib/postgresql/data
    cpus: 0.5
    mem_limit: 512M
    memswap_limit: 512M
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-firecrawl} -d ${POSTGRES_DB:-firecrawl}"]
      interval: 5s
      timeout: 5s
      retries: 10
      start_period: 30s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        compress: "true"

networks:
  backend:
    driver: bridge

volumes:
  redis-data:
  postgres-data:
  rabbitmq-data:
```

**Success criteria:** `test -f ~/firecrawl/docker-compose.yaml && echo OK`

---

## Phase 4 — Write `.env`

Generate secure random values for the three passwords, then write `~/firecrawl/.env`:

```bash
BULL_KEY=$(openssl rand -hex 32)
PG_PASS=$(openssl rand -hex 32)
RMQ_PASS=$(openssl rand -hex 32)

cat > ~/firecrawl/.env << EOF
PORT=3002
HOST=0.0.0.0
INTERNAL_PORT=3002
USE_DB_AUTHENTICATION=false
LOGGING_LEVEL=info

BULL_AUTH_KEY=${BULL_KEY}

POSTGRES_DB=firecrawl
POSTGRES_USER=firecrawl
POSTGRES_PASSWORD=${PG_PASS}

RABBITMQ_USER=firecrawl
RABBITMQ_PASSWORD=${RMQ_PASS}

BLOCK_MEDIA=false
ALLOW_LOCAL_WEBHOOKS=false
EOF
```

**Success criteria:**
- `test -f ~/firecrawl/.env && echo OK`
- `grep -c 'change-this' ~/firecrawl/.env` returns `0` (no placeholder passwords remain)

---

## Phase 5 — Apply Host Kernel Setting

Redis requires memory overcommit to be enabled for reliable background saves:

```bash
sudo sysctl vm.overcommit_memory=1
echo 'vm.overcommit_memory = 1' | sudo tee -a /etc/sysctl.conf
```

**Success criteria:** `sysctl vm.overcommit_memory` returns `vm.overcommit_memory = 1`

---

## Phase 6 — Pull Images

```bash
cd ~/firecrawl
docker compose pull
```

If this fails with `401 Unauthorized`:

```bash
# Requires a GitHub PAT with read:packages scope
# Set GITHUB_TOKEN and GITHUB_USER before running
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USER --password-stdin
docker compose pull
```

**Success criteria:** `docker compose pull` exits 0 with no `ERROR` lines in output.

---

## Phase 7 — Start the Stack

```bash
cd ~/firecrawl
docker compose up -d
```

Wait for health checks to pass (up to 90 seconds on first boot with initdb):

```bash
# Poll until all 5 containers are running
for i in $(seq 1 18); do
  COUNT=$(docker ps --filter "name=firecrawl" --filter "status=running" -q | wc -l)
  echo "Running containers: $COUNT/5 (attempt $i/18)"
  if [ "$COUNT" -eq 5 ]; then break; fi
  sleep 5
done
```

**Success criteria:**

```bash
# All 5 containers running
docker ps --filter "name=firecrawl" --filter "status=running" -q | wc -l
# Must return: 5

# Both health-checked services are healthy
docker inspect firecrawl-nuq-postgres-1 --format='{{.State.Health.Status}}'
# Must return: healthy

docker inspect firecrawl-rabbitmq-1 --format='{{.State.Health.Status}}'
# Must return: healthy

# No containers in exited state
docker ps -a --filter "name=firecrawl" --filter "status=exited" -q | wc -l
# Must return: 0
```

### Failure recovery

**If `nuq-postgres` exited with code 3:**
The pg_cron init error — verify the compose file has `command: postgres -c cron.database_name=...` then:
```bash
docker compose down -v && docker compose up -d
```

**If `api` exited with code 137:**
OOM kill — host has insufficient RAM. Reduce `mem_limit` on `api` to `4G` and `playwright-service` to `2G`, then restart.

**If `api` exited with code 1 and logs show `NUQ_RABBITMQ_URL is not configured`:**
The variable is missing from `x-common-env` in the compose file. Verify it is present, then:
```bash
docker compose down -v && docker compose up -d
```

**If any container shows `EAI_AGAIN` or `ECONNREFUSED` in logs:**
Health checks should prevent this — verify `condition: service_healthy` is set for both `nuq-postgres` and `rabbitmq` in the `api` `depends_on` block.

---

## Phase 8 — Validate the API

```bash
# Test scrape endpoint
RESPONSE=$(curl -s -X POST http://localhost:3002/v1/scrape \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://stevescargall.com", "formats": ["markdown"]}')

echo $RESPONSE | jq .success
```

**Success criteria:** Output is `true`

```bash
# Test async crawl
JOB_ID=$(curl -s -X POST http://localhost:3002/v1/crawl \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://stevescargall.com", "limit": 3}' | jq -r .id)

echo "Crawl job ID: $JOB_ID"

# Must be a non-empty UUID
test -n "$JOB_ID" && echo "Job submitted successfully"
```

---

## Phase 9 — Report Installation Summary

Output a summary of the completed installation:

```bash
echo "=== Firecrawl Installation Summary ==="
echo ""
echo "Working directory: ~/firecrawl"
echo ""
echo "Container status:"
docker ps --filter "name=firecrawl" --format "  {{.Names}}: {{.Status}}"
echo ""
echo "API endpoint:      http://$(hostname -I | awk '{print $1}'):3002"
BULL_KEY=$(grep BULL_AUTH_KEY ~/firecrawl/.env | cut -d= -f2)
echo "Queue admin UI:    http://$(hostname -I | awk '{print $1}'):3002/admin/${BULL_KEY}/queues"
echo ""
echo "To stop:           cd ~/firecrawl && docker compose down"
echo "To restart:        cd ~/firecrawl && docker compose up -d"
echo "To view logs:      cd ~/firecrawl && docker compose logs -f --tail=100"
echo "To wipe data:      cd ~/firecrawl && docker compose down -v"
echo ""
echo "=== Installation complete ==="
```

---

## Known Issues Reference

| Symptom | Cause | Fix |
|---|---|---|
| `nuq-postgres` exits code 3 | `pg_cron` can't install without `cron.database_name` set | Verify `command:` override in compose file; `down -v && up -d` |
| `NUQ_RABBITMQ_URL is not configured` | Missing env var in `x-common-env` | Verify compose file; `down -v && up -d` |
| `ECONNREFUSED :5672` | RabbitMQ not ready when workers started | Verify `condition: service_healthy` on rabbitmq in `depends_on` |
| `EAI_AGAIN nuq-postgres` | Postgres not ready when API started | Verify `condition: service_healthy` on nuq-postgres in `depends_on` |
| Exit code 137 on `extract-worker` | OOM kill — insufficient RAM | Increase VM RAM or reduce `mem_limit` on api service |
| ZodError on `ALLOW_LOCAL_WEBHOOKS` | Boolean env var passed as empty string | Set explicit `false` in `.env` or `:-false` default in compose |
| `401` on `docker compose pull` | GHCR rate limit or auth required | `docker login ghcr.io` with GitHub PAT (read:packages) |
