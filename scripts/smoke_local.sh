#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

usage() {
  cat <<'USAGE'
Usage: scripts/smoke_local.sh [--bootstrap-env] [--keep-running]

Runs a local smoke test for docker-compose startup, backend health, migrations, seed flow, and key search integrations.

Options:
  --bootstrap-env  Copy .env files from examples if they do not exist.
  --keep-running   Leave containers up after checks complete.
  -h, --help       Show this help message.
USAGE
}

bootstrap_env=false
keep_running=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bootstrap-env)
      bootstrap_env=true
      shift
      ;;
    --keep-running)
      keep_running=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required for this smoke test. Install Docker Desktop or Docker Engine + Compose plugin." >&2
  exit 1
fi

if [[ "$bootstrap_env" == true ]]; then
  [[ -f .env ]] || cp .env.example .env
  [[ -f backend/.env ]] || cp backend/.env.example backend/.env
  [[ -f frontend/.env ]] || cp frontend/.env.example frontend/.env
fi

for env_file in .env backend/.env frontend/.env; do
  if [[ ! -f "$env_file" ]]; then
    echo "Missing $env_file. Run: cp .env.example .env && cp backend/.env.example backend/.env && cp frontend/.env.example frontend/.env" >&2
    exit 1
  fi
done

cleanup() {
  if [[ "$keep_running" == false ]]; then
    docker compose down
  fi
}
trap cleanup EXIT

echo "==> Starting stack"
docker compose up --build -d

echo "==> Waiting for backend health"
for _ in {1..60}; do
  if curl -fsS http://localhost:8000/health >/dev/null; then
    break
  fi
  sleep 2
done

curl -fsS http://localhost:8000/health >/dev/null

echo "==> Running migrations + seed"
docker compose exec -T backend alembic -c backend/alembic.ini upgrade head
docker compose exec -T backend python -m backend.scripts.seed_dev_data

echo "==> Running smoke assertions"
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:8000/restaurants >/dev/null
curl -fsS -X POST http://localhost:8000/search \
  -H 'Content-Type: application/json' \
  -d '{"required_tags":["halal"],"excluded_allergens":["shellfish"],"profile":"balanced"}' >/dev/null
curl -fsS -X POST http://localhost:8000/search \
  -H 'Content-Type: application/json' \
  -d '{"group_mode":true,"participants":[{"participant_name":"A","required_tags":["halal"],"excluded_allergens":["dairy"],"profile":"balanced"}],"profile":"balanced","location_latitude":43.651,"location_longitude":-79.347}' >/dev/null
curl -fsS http://localhost:3000 >/dev/null

echo "✅ Local smoke test passed"
