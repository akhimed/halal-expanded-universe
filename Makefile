.PHONY: test mvp-search mvp-serve backend-dev backend-migrate backend-seed backend-test compose-up compose-down

test:
	python -m unittest discover -s tests -v

mvp-search:
	python -m src.dietary_app.cli search --required vegan,hindu_vegetarian --exclude shellfish --profile balanced

mvp-serve:
	python -m src.dietary_app.cli serve --port 8000

backend-dev:
	uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

backend-migrate:
	alembic -c backend/alembic.ini upgrade head

backend-seed:
	python -m backend.scripts.seed_dev_data

backend-test:
	pytest backend/tests -q

compose-up:
	docker compose up --build

compose-down:
	docker compose down
