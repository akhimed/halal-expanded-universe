.PHONY: test mvp-search mvp-serve backend-dev compose-up compose-down

test:
	python -m unittest discover -s tests -v

mvp-search:
	python -m src.dietary_app.cli search --required vegan,hindu_vegetarian --exclude shellfish --profile balanced

mvp-serve:
	python -m src.dietary_app.cli serve --port 8000

backend-dev:
	uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

compose-up:
	docker compose up --build

compose-down:
	docker compose down
