# Faith + Dietary Discovery

This repo has two tracks:

1. **Legacy MVP (preserved):** `src/dietary_app` engine + CLI + basic server
2. **Production backend foundation:** `backend/` FastAPI + SQLAlchemy + Alembic + PostgreSQL-ready models

## Local development

### Prerequisites

- Docker Engine/Desktop with Docker Compose plugin
- Python 3.11+ (for running tests outside containers)
- Node.js 20+ (for frontend checks outside containers)

### Quick start (fresh clone)

1) Copy env files:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

2) Build and start services:

```bash
docker compose up --build -d
```

3) Apply migrations and seed data:

```bash
docker compose exec backend alembic -c backend/alembic.ini upgrade head
docker compose exec backend python -m backend.scripts.seed_dev_data
```

4) Verify locally:

```bash
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:3000 >/dev/null
```

5) Stop when done:

```bash
docker compose down
```

### One-command smoke test

Use the smoke script to validate compose startup + backend health + migrations + seed + basic endpoint checks:

```bash
bash scripts/smoke_local.sh --bootstrap-env
```

Or via Makefile:

```bash
make smoke-local
```

### Backend/frontend URLs

- Backend API: `http://localhost:8000`
- Frontend app: `http://localhost:3000`
- Backend health: `http://localhost:8000/health`

### Demo accounts

Running `python -m backend.scripts.seed_dev_data` creates/updates these demo users for local testing:
- `demo@example.com` (admin)
- `community_mod@example.com` (moderator)

Default password for both users: `DemoPass123`.

## Migrations and seed flow

### Docker workflow (recommended)

```bash
docker compose exec backend alembic -c backend/alembic.ini upgrade head
docker compose exec backend python -m backend.scripts.seed_dev_data
```

### Local (non-docker) workflow

```bash
python -m pip install -r backend/requirements.txt
alembic -c backend/alembic.ini upgrade head
python -m backend.scripts.seed_dev_data
```

Notes:
- Run migrations before seeding.
- Seed script is safe to rerun for local development bootstrapping (idempotent upsert by email/name; no duplicate demo rows).
- Seed data now includes halal, kosher, vegan, vegetarian, hindu_vegetarian, mixed-concept, and low-trust edge-case listings for realistic local demos.

## Running tests/checks

### Full backend API suite

```bash
pytest backend/tests -q
```

### Legacy MVP tests

```bash
python -m unittest discover -s tests -v
```

### Frontend build smoke

```bash
cd frontend
npm ci
npm run test
npm run build
```

## Legacy MVP (still available)

```bash
python -m unittest discover -s tests -v
python -m src.dietary_app.cli search --required vegan,hindu_vegetarian --exclude shellfish --profile balanced
python -m src.dietary_app.cli serve --port 8000
```

## Backend foundation (FastAPI + DB)

### Data model tables

- users
- restaurants
- restaurant_tags
- restaurant_allergen_info
- reports
- favorites
- owner_claims
- audit_logs

### Local backend setup

1. Install dependencies:

```bash
python -m pip install -r backend/requirements.txt
```

2. Configure env:

```bash
cp backend/.env.example backend/.env
# edit DATABASE_URL as needed
```

3. Run DB migrations:

```bash
alembic -c backend/alembic.ini upgrade head
```

4. Seed dev data:

```bash
python -m backend.scripts.seed_dev_data
```

5. Start API server:

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Backend API endpoints

- `GET /health`
- `GET /restaurants`
- `GET /restaurants/{id}`
- `POST /search`
- `GET /favorites` (auth)
- `POST /favorites/{restaurant_id}` (auth)
- `DELETE /favorites/{restaurant_id}` (auth)
- `POST /restaurants/{restaurant_id}/reports` (auth)
- `POST /restaurants/{restaurant_id}/claims` (auth)
- `GET /owner/dashboard` (auth)
- `GET /moderation/reports` (moderator/admin)
- `PATCH /moderation/reports/{report_id}` (moderator/admin)
- `GET /moderation/owner-claims` (moderator/admin)
- `PATCH /moderation/owner-claims/{claim_id}` (moderator/admin)
- `GET /owner/verification-documents` (auth)
- `POST /owner/claims/{claim_id}/verification-documents` (auth)
- `GET /moderation/verification-documents` (moderator/admin)
- `PATCH /moderation/verification-documents/{document_id}` (moderator/admin)
- `GET /restaurants/{id}/trust-events`

Search example:

```bash
curl -s -X POST http://localhost:8000/search \
  -H 'Content-Type: application/json' \
  -d '{"required_tags": ["vegan", "hindu_vegetarian"], "excluded_allergens": ["shellfish"], "profile": "balanced"}'
```

### Group matching search

`POST /search` now supports group mode with multiple participant profiles.

Example:

```bash
curl -s -X POST http://localhost:8000/search \
  -H 'Content-Type: application/json' \
  -d '{
    "group_mode": true,
    "participants": [
      {"participant_name":"Aisha","required_tags":["halal"],"excluded_allergens":["dairy"],"profile":"balanced"},
      {"participant_name":"Eli","required_tags":["vegan"],"excluded_allergens":[],"profile":"balanced"}
    ],
    "profile": "balanced"
  }'
```

Results include `group_fit_score` and `participant_satisfaction` so each participant's constraints are explainable.

### `/search` response schema

`POST /search` returns:

```json
{
  "results": [
    {
      "restaurant": {
        "id": 1,
        "name": "Saffron Garden",
        "description": "...",
        "address": "...",
        "latitude": null,
        "longitude": null
      },
      "matched_tags": ["halal", "vegetarian"],
      "excluded_allergen_status": [
        {"allergen": "nuts", "present": false},
        {"allergen": "dairy", "present": true}
      ],
      "trust_score": 0.905,
      "explanation": "Saffron Garden matched required tags ..."
    }
  ]
}
```

Matching/ranking is deterministic with supported tags (`halal`, `kosher`, `hindu_vegetarian`, `vegan`, `vegetarian`), supported allergens (`shellfish`, `nuts`, `dairy`, `gluten`, `soy`, `egg`, `sesame`), and profiles (`balanced`, `strict`, `community_first`).

### Auth (email/password + roles)

This MVP auth uses **JWT bearer tokens** for simplicity:
- easy local development and frontend integration
- stateless API requests
- deterministic role checks

Supported roles:
- `user`
- `owner`
- `moderator`
- `admin`

Endpoints:
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me` (requires `Authorization: Bearer <token>`)

Example register:

```bash
curl -s -X POST http://localhost:8000/auth/register   -H 'Content-Type: application/json'   -d '{"email":"you@example.com","display_name":"You","password":"StrongPass123"}'
```

Example login:

```bash
curl -s -X POST http://localhost:8000/auth/login   -H 'Content-Type: application/json'   -d '{"email":"you@example.com","password":"StrongPass123"}'
```

Then call current-user:

```bash
curl -s http://localhost:8000/auth/me -H "Authorization: Bearer <token>"
```

### Favorites API

Use bearer token from login/register:

```bash
curl -s http://localhost:8000/favorites -H "Authorization: Bearer <token>"
```
