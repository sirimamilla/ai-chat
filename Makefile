.PHONY: help install install-dev test lint format clean run-cli run-api docker-build docker-up init-db check-config

help:
	@echo "AI Chat - Available Commands"
	@echo "=============================="
	@echo "install          Install production dependencies"
	@echo "install-dev      Install development dependencies"
	@echo "test             Run tests"
	@echo "test-cov         Run tests with coverage"
	@echo "lint             Run linting checks"
	@echo "format           Format code with black"
	@echo "clean            Clean up temporary files"
	@echo "run-cli          Start CLI chat interface"
	@echo "run-api          Start API server"
	@echo "init-db          Initialize database schema"
	@echo "check-config     Check configuration"
	@echo "docker-build     Build Docker image"
	@echo "docker-up        Start with docker-compose"
	@echo "docker-down      Stop docker-compose"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	pytest

test-cov:
	pytest --cov=src/ai_chat --cov-report=html --cov-report=term

lint:
	pylint src/ai_chat
	flake8 src/ai_chat

format:
	black src/ tests/ examples/
	isort src/ tests/ examples/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov/ dist/ build/

run-cli:
	python main.py chat

run-api:
	python main.py serve

init-db:
	python main.py init-database

check-config:
	python main.py check-config

docker-build:
	docker build -t ai-chat:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Development helpers
dev-setup: install-dev init-db
	@echo "Development environment ready!"

dev-reset: docker-down clean
	@echo "Development environment reset!"
