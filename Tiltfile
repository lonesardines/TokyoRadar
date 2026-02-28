# ============================================================
# TokyoRadar — 日潮情报雷达 Tilt 开发环境
# ============================================================
# 启动: tilt up
# 面板: http://localhost:10350
# 前端: http://localhost:5173
# API:  http://localhost:8000
# ============================================================
#
# Hot-reload strategy:
#   docker-compose.dev.yml volume-mounts source into every container.
#   uvicorn --reload / Celery / Vite HMR handle live code reloading.
#   Tilt uses fall_back_on so ONLY Dockerfile/requirements trigger a
#   full image rebuild. All other file changes are absorbed by
#   live_update (no-op since volumes already sync the files).
# ============================================================

docker_compose(
    ['./docker-compose.yml', './docker-compose.dev.yml'],
    env_file='.env',
    project_name='tokyoradar',
)

# Artifacts that should never enter the build context
_build_ignore = [
    '**/__pycache__', '**/*.pyc', '**/*.egg-info',
    'sessions/', '.git/', '**/.DS_Store',
]

# ----------------------------------------------------------
# Backend: FastAPI + uvicorn --reload
# ----------------------------------------------------------
docker_build(
    'tokyoradar-backend',
    context='.',
    dockerfile='./backend/Dockerfile',
    only=['./backend/', './shared/', './scraper/'],
    ignore=_build_ignore,
    live_update=[
        fall_back_on(['./backend/Dockerfile', './backend/requirements.txt', './shared/pyproject.toml']),
        run('true'),  # no-op — volume mounts handle file syncing
    ],
)

dc_resource('backend',
    labels=['app'],
    resource_deps=['db', 'redis'],
    links=[
        link('http://localhost:8000/docs', 'Swagger UI'),
        link('http://localhost:8000/redoc', 'ReDoc'),
        link('http://localhost:8000/health', 'Health'),
    ],
)

# ----------------------------------------------------------
# Scraper Worker + MCP
# ----------------------------------------------------------
docker_build(
    'tokyoradar-scraper',
    context='.',
    dockerfile='./scraper/Dockerfile',
    only=['./scraper/', './shared/'],
    ignore=_build_ignore,
    live_update=[
        fall_back_on(['./scraper/Dockerfile', './scraper/requirements.txt', './shared/pyproject.toml']),
        run('true'),  # no-op — volume mounts handle file syncing
    ],
)

dc_resource('scraper-worker',
    labels=['workers'],
    resource_deps=['db', 'redis'],
)

dc_resource('scraper-mcp',
    labels=['workers'],
    resource_deps=['db', 'redis'],
    links=[link('http://localhost:8001/mcp', 'Scraper MCP')],
)

# ----------------------------------------------------------
# Agent Worker
# ----------------------------------------------------------
docker_build(
    'tokyoradar-agent',
    context='.',
    dockerfile='./agent/Dockerfile',
    only=['./agent/', './shared/'],
    ignore=_build_ignore,
    live_update=[
        fall_back_on(['./agent/Dockerfile', './agent/requirements.txt', './shared/pyproject.toml']),
        run('true'),  # no-op — volume mounts handle file syncing
    ],
)

dc_resource('agent-worker',
    labels=['workers'],
    resource_deps=['db', 'redis', 'scraper-mcp'],
)

# ----------------------------------------------------------
# Frontend: Vite HMR
# ----------------------------------------------------------
docker_build(
    'tokyoradar-frontend-dev',
    context='./frontend',
    dockerfile='./frontend/Dockerfile.dev',
    ignore=['node_modules/', 'dist/', '.vite/'],
    live_update=[
        fall_back_on(['./frontend/Dockerfile.dev', './frontend/package.json', './frontend/package-lock.json']),
        run('true'),  # no-op — volume mounts handle file syncing
    ],
)

dc_resource('frontend',
    labels=['app'],
    resource_deps=['backend'],
    links=[link('http://localhost:5173', 'TokyoRadar 前端')],
)

# ----------------------------------------------------------
# Infrastructure
# ----------------------------------------------------------
dc_resource('db', labels=['infra'])
dc_resource('redis', labels=['infra'])

# ----------------------------------------------------------
# Manual tasks
# ----------------------------------------------------------
local_resource('migrate',
    cmd='docker compose -p tokyoradar exec -T backend sh -c "cd /migrations && alembic upgrade head"',
    resource_deps=['backend'],
    labels=['tasks'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
)

local_resource('autogenerate-migration',
    cmd='docker compose -p tokyoradar exec -T backend sh -c "cd /migrations && alembic revision --autogenerate -m \'auto\'"',
    resource_deps=['backend'],
    labels=['tasks'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
)

local_resource('seed',
    cmd='docker compose -p tokyoradar exec -T backend python -m scripts.seed_db',
    resource_deps=['backend'],
    labels=['tasks'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
)

local_resource('scrape-nanamica',
    cmd='docker compose -p tokyoradar exec -T backend python -c "from celery import Celery; c = Celery(broker=\'redis://redis:6379/0\'); c.send_task(\'scraper.tasks.trigger_brand_scrape\', args=[\'nanamica\'], queue=\'scraper\')"',
    resource_deps=['scraper-worker'],
    labels=['tasks'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
)

local_resource('agent-research-nanamica',
    cmd='docker compose -p tokyoradar exec -T agent-worker python -c "from celery import Celery; c = Celery(broker=\'redis://redis:6379/0\'); c.send_task(\'agent.tasks.research_brand\', args=[\'nanamica\'], queue=\'agent\')"',
    resource_deps=['agent-worker'],
    labels=['tasks'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
)
