.PHONY: help install install-backend install-frontend install-desktop dev dev-backend dev-frontend dev-desktop build build-backend build-frontend build-desktop test test-backend test-frontend lint lint-backend lint-frontend format format-backend format-frontend clean clean-backend clean-frontend clean-desktop db-init db-reset db-migrate setup check-env

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
NPM := npm
UV := uv
BACKEND_DIR := .
FRONTEND_DIR := frontend
ELECTRON_DIR := electron
DB_PATH := ./data/pocket_musec.db
VENV_DIR := .venv

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

##@ Help

help: ## Display this help message
	@echo "$(BLUE)PocketMusec Make Commands$(NC)"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

##@ Installation

install: install-backend install-frontend ## Install all dependencies (backend + frontend)
	@echo "$(GREEN)✓ All dependencies installed$(NC)"

install-backend: ## Install Python backend dependencies
	@echo "$(BLUE)Installing backend dependencies...$(NC)"
	@if command -v $(UV) >/dev/null 2>&1; then \
		$(UV) pip install -e .; \
	else \
		$(PYTHON) -m pip install -e .; \
	fi
	@echo "$(GREEN)✓ Backend dependencies installed$(NC)"

install-frontend: ## Install frontend dependencies
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) install
	@echo "$(GREEN)✓ Frontend dependencies installed$(NC)"

install-desktop: ## Install Electron desktop app dependencies
	@echo "$(BLUE)Installing desktop app dependencies...$(NC)"
	cd $(ELECTRON_DIR) && $(NPM) install
	@echo "$(GREEN)✓ Desktop app dependencies installed$(NC)"

##@ Development

dev: dev-backend dev-frontend ## Run both backend and frontend in development mode
	@echo "$(GREEN)✓ Development servers started$(NC)"

dev-backend: ## Run backend API server
	@echo "$(BLUE)Starting backend server...$(NC)"
	$(PYTHON) run_api.py

dev-frontend: ## Run frontend development server
	@echo "$(BLUE)Starting frontend dev server...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) run dev

dev-desktop: ## Run Electron desktop app in development mode
	@echo "$(BLUE)Starting desktop app...$(NC)"
	cd $(ELECTRON_DIR) && $(NPM) run dev

##@ Building

build: build-backend build-frontend ## Build both backend and frontend for production
	@echo "$(GREEN)✓ Build complete$(NC)"

build-backend: ## Build backend executable
	@echo "$(BLUE)Building backend...$(NC)"
	pyinstaller --onefile --name=pocketmusec-backend run_api.py
	@echo "$(GREEN)✓ Backend built$(NC)"

build-frontend: ## Build frontend for production
	@echo "$(BLUE)Building frontend...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) run build
	@echo "$(GREEN)✓ Frontend built$(NC)"

build-desktop: ## Build Electron desktop app
	@echo "$(BLUE)Building desktop app...$(NC)"
	cd $(ELECTRON_DIR) && $(NPM) run build
	@echo "$(GREEN)✓ Desktop app built$(NC)"

dist-desktop: build-desktop ## Create distributable desktop app package
	@echo "$(BLUE)Creating desktop distribution...$(NC)"
	cd $(ELECTRON_DIR) && $(NPM) run dist
	@echo "$(GREEN)✓ Desktop distribution created$(NC)"

dist-desktop-mac: build-desktop ## Create macOS distributable
	@echo "$(BLUE)Creating macOS distribution...$(NC)"
	cd $(ELECTRON_DIR) && $(NPM) run dist:mac
	@echo "$(GREEN)✓ macOS distribution created$(NC)"

##@ Testing

test: test-backend ## Run all tests
	@echo "$(GREEN)✓ All tests complete$(NC)"

test-backend: ## Run backend tests
	@echo "$(BLUE)Running backend tests...$(NC)"
	pytest tests/ -v --cov=backend --cov=cli
	@echo "$(GREEN)✓ Backend tests complete$(NC)"

test-frontend: ## Run frontend tests (if configured)
	@echo "$(BLUE)Running frontend tests...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) test || echo "$(YELLOW)⚠ Frontend tests not configured$(NC)"

test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	pytest tests/test_integration/ -v
	@echo "$(GREEN)✓ Integration tests complete$(NC)"

##@ Code Quality

lint: lint-backend lint-frontend ## Lint all code
	@echo "$(GREEN)✓ Linting complete$(NC)"

lint-backend: ## Lint Python code with ruff
	@echo "$(BLUE)Linting backend code...$(NC)"
	ruff check backend/ cli/ tests/
	@echo "$(GREEN)✓ Backend linting complete$(NC)"

lint-frontend: ## Lint frontend code with ESLint
	@echo "$(BLUE)Linting frontend code...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) run lint || echo "$(YELLOW)⚠ Linting issues found$(NC)"

format: format-backend format-frontend ## Format all code
	@echo "$(GREEN)✓ Formatting complete$(NC)"

format-backend: ## Format Python code with black and ruff
	@echo "$(BLUE)Formatting backend code...$(NC)"
	black backend/ cli/ tests/
	ruff check --fix backend/ cli/ tests/
	@echo "$(GREEN)✓ Backend formatting complete$(NC)"

format-frontend: ## Format frontend code (if configured)
	@echo "$(BLUE)Formatting frontend code...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) run format || echo "$(YELLOW)⚠ Format script not configured$(NC)"

type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checks...$(NC)"
	mypy backend/ cli/
	@echo "$(GREEN)✓ Type checking complete$(NC)"

##@ Database

db-init: ## Initialize database with migrations
	@echo "$(BLUE)Initializing database...$(NC)"
	$(PYTHON) -c "from backend.repositories.migrations import DatabaseMigrator; m = DatabaseMigrator('$(DB_PATH)'); m.migrate()"
	@echo "$(GREEN)✓ Database initialized$(NC)"

db-reset: ## Reset database (WARNING: deletes all data)
	@echo "$(YELLOW)⚠ WARNING: This will delete all database data!$(NC)"
	@echo -n "Are you sure? [y/N] "; \
	read REPLY; \
	if [ "$$REPLY" = "y" ] || [ "$$REPLY" = "Y" ]; then \
		rm -f $(DB_PATH); \
		$(MAKE) db-init; \
		echo "$(GREEN)✓ Database reset$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled$(NC)"; \
	fi

db-migrate: db-init ## Alias for db-init

##@ Setup & Configuration

setup: check-env install db-init ## Complete project setup (install deps + init DB)
	@echo "$(GREEN)✓ Project setup complete!$(NC)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Configure .env file with your API keys"
	@echo "  2. Run 'make dev' to start development servers"
	@echo "  3. Visit http://localhost:5173 in your browser"

check-env: ## Check if .env file exists
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)⚠ .env file not found$(NC)"; \
		if [ -f .env.example ]; then \
			echo "$(BLUE)Copying .env.example to .env...$(NC)"; \
			cp .env.example .env; \
			echo "$(GREEN)✓ .env file created. Please edit it with your configuration.$(NC)"; \
		else \
			echo "$(YELLOW)⚠ .env.example not found. Please create .env manually.$(NC)"; \
		fi; \
	else \
		echo "$(GREEN)✓ .env file exists$(NC)"; \
	fi

##@ Cleanup

clean: clean-backend clean-frontend clean-desktop ## Clean all build artifacts
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-backend: ## Clean backend build artifacts
	@echo "$(BLUE)Cleaning backend artifacts...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.spec
	rm -rf __pycache__/
	rm -rf */__pycache__/
	rm -rf */*/__pycache__/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	rm -rf *.egg-info/
	rm -rf .venv/
	@echo "$(GREEN)✓ Backend cleaned$(NC)"

clean-frontend: ## Clean frontend build artifacts
	@echo "$(BLUE)Cleaning frontend artifacts...$(NC)"
	cd $(FRONTEND_DIR) && rm -rf dist/ node_modules/.vite/
	@echo "$(GREEN)✓ Frontend cleaned$(NC)"

clean-desktop: ## Clean desktop app build artifacts
	@echo "$(BLUE)Cleaning desktop artifacts...$(NC)"
	cd $(ELECTRON_DIR) && rm -rf dist/ node_modules/.cache/
	rm -rf dist-electron/
	@echo "$(GREEN)✓ Desktop cleaned$(NC)"

clean-all: clean ## Clean everything including node_modules and venv
	@echo "$(BLUE)Cleaning all dependencies...$(NC)"
	cd $(FRONTEND_DIR) && rm -rf node_modules/
	cd $(ELECTRON_DIR) && rm -rf node_modules/
	rm -rf node_modules/
	rm -rf $(VENV_DIR)
	@echo "$(GREEN)✓ Complete cleanup done$(NC)"

##@ Utilities

logs: ## Show recent log files
	@echo "$(BLUE)Recent log files:$(NC)"
	@ls -lht logs/*.log 2>/dev/null | head -10 || echo "$(YELLOW)No log files found$(NC)"

check: lint type-check test ## Run all checks (lint, type-check, test)
	@echo "$(GREEN)✓ All checks passed$(NC)"

ci: install check ## Run CI pipeline (install + check)
	@echo "$(GREEN)✓ CI pipeline complete$(NC)"

