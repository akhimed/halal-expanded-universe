# Faith + Dietary Discovery

This repo has two tracks:

1. **Legacy MVP (preserved):** `src/dietary_app` engine + CLI + basic server
2. **Production backend foundation:** `backend/` FastAPI + SQLAlchemy + Alembic + PostgreSQL-ready models

## Local development

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker + Docker Compose plugin

### 1) Environment configuration

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 2) Run with Docker Compose (recommended)

```bash
docker compose up --build -d
```

Run migrations and seed data inside the backend container:

```bash
docker compose exec backend alembic -c backend/alembic.ini upgrade head
docker compose exec backend python -m backend.scripts.seed_dev_data
```

Stop stack:

```bash
docker compose down
```

### Backend/frontend URLs

- Backend API: `http://localhost:8000`
- Frontend app: `http://localhost:3000`
- Backend health: `http://localhost:8000/health`

### Demo accounts

No demo users are auto-created by default. Create users via `POST /auth/register`, then set roles in DB for moderator/admin local testing.

## Running tests

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
npm run build
```

## Seeding data

```bash
alembic -c backend/alembic.ini upgrade head
python -m backend.scripts.seed_dev_data
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
curl -s -X POST http://localhost:8000/favorites/1 -H "Authorization: Bearer <token>"
curl -s -X DELETE http://localhost:8000/favorites/1 -H "Authorization: Bearer <token>"
```


### Reporting inaccurate listings

Authenticated users can submit listing reports with deterministic types:
- `inaccurate_halal_status`
- `inaccurate_kosher_status`
- `allergen_risk`
- `alcohol_served`
- `outdated_info`
- `other`

`description` and `evidence_url` are optional (URL is a placeholder until file uploads are implemented).

```bash
curl -s -X POST http://localhost:8000/restaurants/1/reports \
  -H "Authorization: Bearer <token>" \
  -H 'Content-Type: application/json' \
  -d '{"report_type":"outdated_info","description":"Hours changed"}'
```

Each submission creates both a `reports` record and an `audit_logs` entry.


### Owner claim flow

Authenticated users can submit a listing ownership claim:

```bash
curl -s -X POST http://localhost:8000/restaurants/1/claims \
  -H "Authorization: Bearer <token>" \
  -H 'Content-Type: application/json' \
  -d '{"notes":"I am the current manager for this location."}'
```

Claim statuses are moderation-ready and deterministic:
- `pending`
- `approved`
- `rejected`

Owner dashboard data:

```bash
curl -s http://localhost:8000/owner/dashboard -H "Authorization: Bearer <token>"
```

Each claim submission records an `audit_logs` entry with action `submitted`.


### Moderation tools (moderator/admin)

Moderators and admins can triage reports and owner claims:

```bash
curl -s http://localhost:8000/moderation/reports -H "Authorization: Bearer <moderator_or_admin_token>"
curl -s -X PATCH http://localhost:8000/moderation/reports/1 \
  -H "Authorization: Bearer <moderator_or_admin_token>" \
  -H 'Content-Type: application/json' \
  -d '{"status":"resolved","note":"Verified and fixed"}'

curl -s http://localhost:8000/moderation/owner-claims -H "Authorization: Bearer <moderator_or_admin_token>"
curl -s -X PATCH http://localhost:8000/moderation/owner-claims/1 \
  -H "Authorization: Bearer <moderator_or_admin_token>" \
  -H 'Content-Type: application/json' \
  -d '{"status":"approved","note":"Ownership docs verified"}'
```

Each moderation status change records an `audit_logs` entry with action `status_updated`.


### Verification documents + trust events

Owners can submit verification document metadata (and optional file upload in local filesystem dev mode):

```bash
curl -s -X POST http://localhost:8000/owner/claims/1/verification-documents \
  -H "Authorization: Bearer <token>" \
  -F document_type=business_license \
  -F notes='License attached' \
  -F metadata_filename=license.pdf \
  -F metadata_mime_type=application/pdf
```

Moderators/admins can review documents:

```bash
curl -s http://localhost:8000/moderation/verification-documents -H "Authorization: Bearer <moderator_or_admin_token>"
curl -s -X PATCH http://localhost:8000/moderation/verification-documents/1 \
  -H "Authorization: Bearer <moderator_or_admin_token>" \
  -H 'Content-Type: application/json' \
  -d '{"status":"approved","note":"Valid docs"}'
```

Restaurant detail now includes a trust breakdown and trust events can be queried via `/restaurants/{id}/trust-events`.

### Backend tests

```bash
pytest backend/tests -q
```

## Developer helpers

```bash
make test
make mvp-search
make backend-migrate
make backend-seed
make backend-test
```

## Planning docs

- `ARCHITECTURE.md`
- `TODO_ROADMAP.md`


## Frontend (Nuxt 3 + Tailwind)

### Run frontend locally

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

### Frontend pages

- `/` — landing + backend health check
- `/search` — filters + search results
- `/restaurants/[id]` — detail page
- `/favorites` — saved places
- `/owner/dashboard` — owner claim tracking
- `/admin/dashboard` — moderation queues and status actions

The frontend API client is in `frontend/composables/useApiClient.ts` and uses `NUXT_PUBLIC_API_BASE_URL`.


### Map discovery

- `/search` includes MapLibre-based result markers synced with selected result cards.
- Desktop uses split list/map layout; mobile defaults to list with a map toggle.
- `/restaurants/[id]` includes a simple location map when coordinates are available.
- If coordinates are missing, map components show a graceful fallback message.
