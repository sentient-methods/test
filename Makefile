.PHONY: install dev backend frontend test clean

# Install everything
install:
	pip install -e ".[dev]"
	cd frontend && npm install

# Run both backend and frontend
dev: backend frontend

# Backend only
backend:
	python -m backend.main

# Frontend only
frontend:
	cd frontend && npm run dev

# Run tests
test:
	python -m pytest tests/ -v

# Clean build artifacts
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist build *.egg-info .pytest_cache
	cd frontend && rm -rf node_modules dist

# Setup from scratch
setup: install
	@echo ""
	@echo "Setup complete. Next steps:"
	@echo "  1. cp .env.example .env"
	@echo "  2. Edit .env with your ANTHROPIC_API_KEY"
	@echo "  3. make dev"
	@echo ""
	@echo "As you wish, CEO."
