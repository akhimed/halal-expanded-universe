# TODO Roadmap

## Phase 0 — Stabilize foundation (now)
- [x] Preserve existing MVP engine, CLI, and tests
- [x] Add architecture and roadmap docs
- [x] Scaffold backend/frontend folders
- [x] Add docker-compose with postgres + backend + frontend services
- [x] Add `.env.example` files

## Phase 1 — Backend API baseline
- [x] Implement Pydantic request/response schemas
- [x] Add `/search` endpoint calling existing engine behavior
- [x] Add config management for env variables
- [x] Add backend test coverage for API routes

## Phase 2 — Persistence and geo
- [ ] Add SQLAlchemy models for venues, tags, trust signals
- [ ] Add Alembic migrations
- [ ] Enable PostGIS and location-based querying
- [ ] Replace sample in-memory data with DB-backed repository layer

## Phase 3 — Frontend product shell
- [ ] Build search form with dietary and allergen filters
- [ ] Connect Nuxt UI to backend `/api/v1/search`
- [ ] Add result cards with explainability output
- [ ] Add environment-based API base URL config

## Phase 4 — Trust and verification workflows
- [ ] Add certificate upload/metadata model
- [ ] Add admin moderation workflow
- [ ] Add audit trail for verification actions
- [ ] Add role-based access controls

## Phase 5 — Production readiness
- [ ] Add structured logging and tracing
- [ ] Add CI checks for tests/linting
- [ ] Add load-testing baseline for search endpoint
- [ ] Add deployment manifests (cloud target TBD)
