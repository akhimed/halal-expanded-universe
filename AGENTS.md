# Project instructions

This repository is a faith + dietary restaurant discovery platform.

Current status:
- Dockerized frontend/backend/postgres stack runs locally
- Alembic migrations work
- Seed script works
- CORS is configured for local frontend/backend
- Nuxt frontend and FastAPI backend communicate successfully
- Do not revert any launch-stability fixes already present

Core product priorities:
1. Trustworthy religious + dietary matching
2. Explainable results
3. Stable local development
4. Small, reviewable PRs
5. Incremental improvement over large rewrites

Hard rules:
- Do not break docker-compose local startup
- Frontend must remain compatible with browser-side API calls to localhost in local dev
- Preserve deterministic matching logic
- Do not remove or regress CORS middleware
- Do not reintroduce invalid Alembic revision lengths
- Do not introduce LLM-dependent matching logic
- Do not invent fake integrations
- Update tests for changed behavior
- Update docs for anything affecting setup/run flow

PR requirements:
- Keep changes scoped
- Include summary of changed files
- Include exact commands run
- Include known limitations