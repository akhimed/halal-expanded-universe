# Architecture: MVP to Production

This repository started with a local Python MVP (`src/dietary_app`) that provides:
- matching logic
- CLI
- minimal HTTP server
- tests

That path remains intact as a **reference and fallback** while we migrate to a production web stack.

## Target architecture

```text
┌──────────────┐      HTTP/JSON      ┌─────────────────────┐
│  Nuxt 3 Web  │  <----------------> │  FastAPI Backend    │
│  (frontend/) │                     │  (backend/app/)     │
└──────────────┘                     └──────────┬──────────┘
                                                │
                                                │ SQL + PostGIS
                                                ▼
                                        ┌─────────────────────┐
                                        │ PostgreSQL +PostGIS │
                                        │ (docker compose)    │
                                        └─────────────────────┘
```

## Repository layout

- `src/dietary_app/` — existing MVP engine + CLI/API (preserved)
- `backend/` — production API service (FastAPI)
- `frontend/` — production web UI (Nuxt 3 + Vue 3)
- `docker-compose.yml` — local orchestration for backend/frontend/postgres

## Migration path

1. **Phase 0 (current):** Keep MVP logic as source of truth for matching behavior.
2. **Phase 1:** Add FastAPI app and expose health + search endpoints while internally calling MVP engine.
3. **Phase 2:** Add persistence with PostgreSQL/PostGIS (venues, trust signals, certifications).
4. **Phase 3:** Move frontend from static scaffold to searchable UI that calls FastAPI.
5. **Phase 4:** Add auth, moderation workflows, restaurant onboarding, and observability.

## Design principles

- Do not break the existing MVP commands/tests.
- Keep business logic reusable and decoupled from transport layers.
- Add production concerns incrementally (config, DB, migrations, auth, monitoring).
- Prefer practical defaults and local-dev friendliness via Docker Compose.

## Initial production API contract (starter)

- `GET /health` -> readiness
- `POST /api/v1/search` -> request payload with dietary tags/allergens/profile

This is intentionally aligned with the MVP semantics to reduce migration risk.
