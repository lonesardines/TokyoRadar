# TOKYORADAR

Private intelligence system for navigating Japanese fashion. Brands, retailers, and buying guides — curated for international buyers.

## Tech Stack

**Backend:** Python 3.12 / FastAPI / SQLAlchemy 2.0 / Alembic / PostgreSQL 16
**Frontend:** React 18 / TypeScript / Vite / Tailwind CSS / Zustand / TanStack Query
**Infrastructure:** Docker Compose / Caddy / Redis / Celery
**Testing:** Playwright E2E (47 tests)

## Features

- 50+ Japanese fashion brands with detailed profiles
- 12 retailers organized by shipping accessibility (direct / proxy / agent)
- 5 proxy service comparisons with fee structures, pros & cons
- Style-based browsing (streetwear, avant-garde, workwear, denim, outdoor, luxury)
- Search and multi-filter brand directory
- Chinese / English UI switching (i18n)

## Quick Start

```bash
# 1. Clone
git clone https://github.com/lonesardines/TokyoRadar.git
cd TokyoRadar

# 2. Environment
cp .env.example .env

# 3. Start all services
make dev

# 4. Run migrations & seed data
make migrate
make seed
```

The app will be available at `http://localhost`.

## Development

```bash
make dev              # Start with hot-reload (docker-compose dev override)
make up               # Start in detached mode
make down             # Stop all services
make logs             # Tail logs
make migrate          # Run Alembic migrations
make seed             # Seed brands, retailers, proxy services
make db-shell         # PostgreSQL interactive shell
make shell            # Backend container shell
```

### Frontend Only

```bash
cd frontend
npm install
VITE_API_PROXY_TARGET=http://localhost:8000 npm run dev
```

### E2E Tests

```bash
cd frontend
npx playwright install --with-deps chromium
npx playwright test
```

## Project Structure

```
TokyoRadar/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # FastAPI routes
│   │   ├── models/          # SQLAlchemy models
│   │   └── schemas/         # Pydantic schemas
│   └── alembic/             # Database migrations
├── frontend/
│   ├── src/
│   │   ├── pages/           # Route pages
│   │   ├── components/      # React components
│   │   ├── store/           # Zustand stores
│   │   ├── i18n/            # Translation files (en/zh)
│   │   └── api/             # API client
│   └── e2e/                 # Playwright tests
├── data/                    # Seed data JSON
├── scripts/                 # Utility scripts
├── docker-compose.yml
└── Caddyfile
```

## Roadmap

- [x] **Phase 1:** Brand Archive — core data, CRUD APIs, editorial frontend
- [ ] **Phase 2:** Scrapers + AI Translation (Fashion Press, ZOZOTOWN, Claude pipeline)
- [ ] **Phase 3:** Season Tracker (collections, lookbooks)
- [ ] **Phase 4:** Price Comparison + Landed Cost Calculator
- [ ] **Phase 5:** Notifications + Personalization (Discord webhooks)
