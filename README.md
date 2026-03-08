# Faith + Dietary Discovery Engine (MVP)

This repository runs as an **end-to-end local MVP** with:

- A matching/ranking domain engine
- A CLI for quick searches
- A local HTTP API (`/search`) you can call from frontend/mobile apps
- Profile variants (“other versions”) so you can compare strict vs flexible behavior

## What this is

You can search restaurants with combined constraints like:

- religious (`halal`, `kosher`, `hindu_vegetarian`)
- lifestyle (`vegan`, `vegetarian`)
- safety (`excluded_allergens`)

Then rank by trust (certification + community + recency).

---

## Quick answer: yes, run this in Command Prompt

If you are on Windows, open **Command Prompt** and run these commands from the project folder.

### 0) Go to project folder

```bat
cd C:\path\to\halal-expanded-universe
```

### 1) Check Python works

```bat
py --version
```

(If `py` doesn’t work, use `python --version`.)

### 2) Run tests

```bat
py -m unittest discover -s tests -v
```

### 3) Run a search from CLI

```bat
py -m src.dietary_app.cli search --required vegan,hindu_vegetarian --exclude shellfish --profile balanced
```

### 4) Run API server

```bat
py -m src.dietary_app.cli serve --port 8000
```

Keep that window open.

### 5) Test API in another Command Prompt window

Health check:

```bat
curl http://localhost:8000/health
```

Search request:

```bat
curl -X POST http://localhost:8000/search ^
  -H "Content-Type: application/json" ^
  -d "{\"required_tags\":[\"vegan\",\"hindu_vegetarian\"],\"excluded_allergens\":[\"shellfish\"],\"profile\":\"balanced\"}"
```

If your Windows machine has no `curl`, use PowerShell:

```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/search" -ContentType "application/json" -Body '{"required_tags":["vegan","hindu_vegetarian"],"excluded_allergens":["shellfish"],"profile":"balanced"}'
```

---

## macOS / Linux commands

```bash
python -m unittest discover -s tests -v
python -m src.dietary_app.cli search --required vegan,hindu_vegetarian --exclude shellfish --profile balanced
python -m src.dietary_app.cli serve --port 8000
```

Then in another terminal:

```bash
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/search \
  -H 'Content-Type: application/json' \
  -d '{
    "required_tags": ["vegan", "hindu_vegetarian"],
    "excluded_allergens": ["shellfish"],
    "profile": "balanced"
  }'
```

---

## How to test different “versions” (profiles)

Use the `--profile` option in CLI or `"profile"` in API payload.

1. `balanced` (default)
   - Weights: cert 45%, community 35%, recency 20%
   - No minimum thresholds

2. `strict`
   - Weights: cert 60%, community 25%, recency 15%
   - Minimum trust thresholds enforced

3. `community_first`
   - Weights: cert 25%, community 55%, recency 20%
   - Emphasizes crowd validation

Example comparisons:

```bat
py -m src.dietary_app.cli search --required vegetarian --profile balanced --format json
py -m src.dietary_app.cli search --required vegetarian --profile strict --format json
py -m src.dietary_app.cli search --required vegetarian --profile community_first --format json
```

---

## Project structure

- `src/dietary_app/models.py` — domain models
- `src/dietary_app/policies.py` — profile variants and thresholds
- `src/dietary_app/engine.py` — filtering + ranking logic
- `src/dietary_app/cli.py` — executable CLI entrypoint
- `src/dietary_app/server.py` — local HTTP API
- `src/dietary_app/sample_data.py` — seed/demo dataset
- `tests/test_engine.py` — unit tests

## Next step to make this a product

1. Replace `SAMPLE_VENUES` with a real DB (Postgres)
2. Add auth + account profiles
3. Add restaurant onboarding + certificate upload
4. Add moderation panel for certifier/admin workflows
5. Add geolocation/radius filtering for nearby discovery
