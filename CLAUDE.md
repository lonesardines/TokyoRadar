# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

TokyoRadar (日潮情报雷达) — Japanese fashion intelligence platform. Multi-service monorepo: scrapes Japanese brand stores, translates/summarizes with AI, serves via API + React frontend.

## Development Commands

All services run via Docker Compose. Primary workflow uses `tilt up` (dashboard at localhost:10350) or Make:

```bash
tilt up                    # Start all services with hot-reload (preferred)
make dev                   # Alternative: docker-compose with dev overrides
make up                    # Production-like (detached)
make down                  # Stop everything
```

### Database
```bash
make migrate                           # Run migrations
make makemigrations msg="description"  # Autogenerate migration
make seed                              # Seed brands/retailers/proxies/categories
make db-shell                          # psql into PostgreSQL
```

Migrations live at `migrations/` (project root, not backend/). Inside containers: `cd /migrations && alembic upgrade head`.

### Testing & Linting
```bash
make test                              # Backend pytest (in container)
make lint                              # Backend ruff check (in container)
cd frontend && npm run lint            # Frontend ESLint
cd frontend && npm run test:e2e        # Playwright E2E (47+ tests)
cd frontend && npx playwright test --ui # Playwright UI mode
```

### Frontend Standalone
```bash
cd frontend && npm install
VITE_API_PROXY_TARGET=http://localhost:8000 npm run dev
```

## Architecture

### Service Layout
- **`shared/`** — `tokyoradar-shared` installable Python package. All SQLAlchemy models, config (Pydantic Settings), database engine/session. Every other Python service installs this first.
- **`backend/`** — FastAPI API only. Does NOT define its own models — uses re-export shims (`app.config`, `app.database`, `app.models.*` each one-line import from `tokyoradar_shared`).
- **`scraper/`** — Celery worker. Shopify scraper implemented, Fashion Press / ZOZOTOWN stubbed. Registry pattern maps brand slugs to scraper classes.
- **`ai_pipeline/`** — Celery worker for Qwen translation/summarization via DashScope SDK. Skeleton only.
- **`migrations/`** — Alembic at project root (not inside backend). `env.py` imports all models from shared.
- **`frontend/`** — React 19 + TypeScript + Vite + Tailwind v3 + TanStack Query + Zustand. `@` path alias → `src/`.

### Re-export Shim Pattern (Critical)
Backend routes import from `app.models`, `app.config`, `app.database` — but these are one-line re-exports from `tokyoradar_shared`. When adding models or config, edit `shared/tokyoradar_shared/`, then update the re-export in `backend/app/`. Never duplicate model definitions.

### Docker Build Context
All Dockerfiles use project root as build context (`context: .`). Each copies `shared/` and runs `pip install /shared` before copying its own code.

### Celery Task Routing
- `scraper.tasks.*` → `scraper` queue
- `ai_pipeline.tasks.*` → `ai` queue
- Broker + backend: Redis

### Database Models (9 total, all in `shared/tokyoradar_shared/models/`)
Brand, Item, Category, Collection, Media, PriceListing, ProxyService, Retailer, ScrapeJob. Uses SQLAlchemy 2.0 `mapped_column` style, PostgreSQL ARRAY and JSONB columns.

### Scraper Architecture
Abstract `BrandScraper` base class → concrete scrapers (e.g. `ShopifyBrandScraper`). `SCRAPER_REGISTRY` in `scraper/sources/registry.py` maps brand slugs to `ScraperConfig(scraper_class, domain, source)`. Adding a brand = adding an entry to the registry dict.

### Frontend Patterns
- React Router for routing, admin routes under `/admin/`
- Zustand stores: `filterStore`, `localeStore`
- TanStack Query for server state
- i18n with en/zh locale switching
- API client in `src/api/` (axios), proxied via Vite `/api` → backend
- Icons: Lucide React

## Key Conventions

- Brand `slug` is the primary lookup key for user-facing URLs, not integer ID
- `shipping_tier` enum values: `green` (direct), `yellow` (proxy needed), `red` (agent needed)
- Seed data JSON field names differ from model columns (e.g. `name` → `name_en`, `founder` → `designer`)
- `ai_pipeline` uses underscore, not hyphen — Python package name constraint
- Environment loaded from `.env` via Pydantic `BaseSettings`; see `.env.example` for required vars

## Service URLs (Local Dev)
- Frontend: http://localhost:5173
- API + Swagger: http://localhost:8000/docs
- Tilt dashboard: http://localhost:10350
- PostgreSQL: localhost:5432
- Redis: localhost:6379
