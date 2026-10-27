.PHONY: install test lint run docker-build docker-up clean generate-data

install:
	pip install -r requirements.txt

test:
	PYTHONPATH=. pytest tests/ -v --tb=short

lint:
	flake8 src/ tests/ --max-line-length=120 --ignore=E501,W503

run:
	PYTHONPATH=. uvicorn src.api.app:app --reload --port 8000

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

generate-data:
	python data/sample/generate_sample_data.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov

init-db:
	PYTHONPATH=. python -c "from src.utils import DatabaseManager; db = DatabaseManager(); db.execute_query(open('sql/star_schema.sql').read())"

all: install lint test
