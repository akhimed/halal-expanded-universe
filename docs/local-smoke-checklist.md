# Local smoke checklist

Use this checklist after a fresh clone or when troubleshooting local startup.

## Automated path (preferred)

```bash
bash scripts/smoke_local.sh --bootstrap-env
```

This validates:
- Compose services build and start
- Backend health endpoint responds
- Alembic migrations apply
- Seed script runs
- Search endpoint accepts a basic request
- Frontend responds on port 3000

## Manual path

1. Copy env files.

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

2. Start stack.

```bash
docker compose up --build -d
```

3. Apply migrations and seed.

```bash
docker compose exec backend alembic -c backend/alembic.ini upgrade head
docker compose exec backend python -m backend.scripts.seed_dev_data
```

Tip: the seed command is idempotent and can be rerun to refresh demo users/restaurants (16 restaurant templates including trust/allergen edge cases) without creating duplicates.

4. Verify endpoints.

```bash
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:8000/restaurants >/dev/null
curl -fsS -X POST http://localhost:8000/search \
  -H 'Content-Type: application/json' \
  -d '{"required_tags":["halal"],"excluded_allergens":["shellfish"],"profile":"balanced"}' >/dev/null
curl -fsS http://localhost:3000 >/dev/null
```

5. Shut down when done.

```bash
docker compose down
```
