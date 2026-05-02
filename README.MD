# Blog API

A Django REST API with JWT authentication, Celery tasks, WebSocket support via Django Channels, and nginx as a reverse proxy.

---

## Architecture

```
Browser / curl  │  localhost
                ▼
        ┌─────────────┐
        │    nginx    │  :80  published to host
        └──────┬──────┘
               │  proxy_pass http://django_backend (web:8000)
               ▼
        ┌─────────────┐
        │   daphne    │  :8000, NOT published to host
        │  (web svc)  │
        └─────────────┘
               │
        redis, db, celery_worker, celery_beat, flower (unchanged)
```

---

## Running

1. Copy the env file and fill in the required values:
   ```bash
   cp settings/.env.example settings/.env
   # Set BLOG_ENV_ID=prod and BLOG_SECRET_KEY to a real secret
   ```

2. Start all services:
   ```bash
   docker compose up --build
   ```

---

## HW4 Verification Steps

All commands run against `localhost` (nginx on port 80). Port 8000 must not be reachable from the host.

### 1. Admin login returns 200 with nginx Server header

```bash
curl -I http://localhost/admin/login/
```

Expected: `HTTP/1.1 200 OK` and a `Server: nginx/...` header in the response.

### 2. Static file served by nginx with long Cache-Control header

```bash
curl -I http://localhost/static/admin/css/base.css
```

Expected: `HTTP/1.1 200 OK` and `Cache-Control: max-age=2592000` (30 days) in the response.

### 3. API returns JSON list of posts

```bash
curl http://localhost/api/posts/
```

Expected: a JSON object with a `results` array of blog posts.

### 4. Stopping the web service produces 502 from nginx (not connection refused)

```bash
docker compose stop web
curl -I http://localhost/api/posts/
# Expected: HTTP/1.1 502 Bad Gateway
docker compose start web
```

nginx stays up and returns `502 Bad Gateway` instead of a connection-refused error,
proving that nginx is in the path and owns port 80.

### 5. Port 8000 is not reachable from the host

```bash
curl http://localhost:8000/
```

Expected: `curl: (7) Failed to connect to localhost port 8000: Connection refused`

### 6. WebSocket upgrades with 101 Switching Protocols

First obtain a JWT token:

```bash
TOKEN=$(curl -s -X POST http://localhost/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"<user>","password":"<pass>"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access'])")
```

Then connect (requires `wscat` — install with `npm i -g wscat`):

```bash
wscat -c "ws://localhost/ws/posts/<existing-slug>/comments/?token=$TOKEN"
```

Expected: the handshake completes with `101 Switching Protocols`. Post a comment via the REST API
in another terminal and the WebSocket message should arrive in the wscat session.

```bash
# Post a comment while wscat is connected
curl -X POST http://localhost/api/posts/<existing-slug>/comments/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"body":"hello from hw4"}'
```

---

## Project Structure (hw4 additions)

```
nginx/
  default.conf        ← nginx site config (written from scratch)
docker-compose.yml    ← nginx service added; web no longer publishes :8000
README.md             ← this file
```