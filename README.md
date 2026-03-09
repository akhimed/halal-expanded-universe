# Faith + Dietary Discovery

This repo now contains **two tracks**:

1. **Legacy MVP track (preserved):** `src/dietary_app` (engine + CLI + basic HTTP server)
2. **Production track (new foundation):** `backend/` (FastAPI), `frontend/` (Nuxt 3), `docker-compose.yml` (Postgres + services)

---

## Legacy MVP (still working)

Use this while production backend/frontend are being built.

### Run tests

```bash
python -m unittest discover -s tests -v
```

### CLI search

```bash
python -m src.dietary_app.cli search --required vegan,hindu_vegetarian --exclude shellfish --profile balanced
```

### MVP local server

```bash
python -m src.dietary_app.cli serve --port 8000
```

---

## Production foundation (new)

### Added structure

- `backend/` — FastAPI app scaffold with:
  - `GET /health`
  - `POST /api/v1/search` (currently proxies MVP engine semantics)
- `frontend/` — Nuxt 3 app scaffold with health check button
- `docker-compose.yml` — orchestrates:
  - `postgres` (PostgreSQL + PostGIS)
  - `backend`
  - `frontend`

### Local development with Docker

1. Copy env file:

```bash
cp .env.example .env
```

2. Start stack:

```bash
docker compose up --build
```

3. Open apps:

- Frontend: `http://localhost:3000`
- Backend health: `http://localhost:8000/health`

4. Test backend search endpoint:

```bash
curl -s -X POST http://localhost:8000/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"required_tags": ["vegan", "hindu_vegetarian"], "excluded_allergens": ["shellfish"], "profile": "balanced"}'
```

---

## Helpful commands

```bash
make test
make mvp-search
make mvp-serve
make compose-up
make compose-down
```

---

## Planning docs

- `ARCHITECTURE.md` — target architecture and migration path
- `TODO_ROADMAP.md` — phased milestones from MVP to production
