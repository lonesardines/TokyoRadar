# ============================================================
# TokyoRadar — 日潮情报雷达 Tilt 开发环境
# ============================================================
# 启动: tilt up
# 面板: http://localhost:10350
# 前端: http://localhost:5173
# API:  http://localhost:8000
# ============================================================

# 加载 docker-compose (base + dev 覆盖)
docker_compose(
    ['./docker-compose.yml', './docker-compose.dev.yml'],
    env_file='.env',
    project_name='tokyoradar',
)

# ----------------------------------------------------------
# Backend: FastAPI + uvicorn --reload
# ----------------------------------------------------------
docker_build(
    'tokyoradar-backend',
    context='.',
    dockerfile='./backend/Dockerfile',
    only=['./backend/', './shared/'],
    live_update=[
        sync('./backend/', '/app/'),
        sync('./shared/', '/shared/'),
        run(
            'pip install /shared && pip install -r requirements.txt',
            trigger=['./backend/requirements.txt', './shared/pyproject.toml'],
        ),
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
# Frontend: Vite dev server + HMR
# ----------------------------------------------------------
docker_build(
    'tokyoradar-frontend-dev',
    context='./frontend',
    dockerfile='./frontend/Dockerfile.dev',
    only=['./'],
    live_update=[
        sync('./frontend/src/', '/app/src/'),
        sync('./frontend/public/', '/app/public/'),
        sync('./frontend/index.html', '/app/index.html'),
        run('npm install', trigger=['./frontend/package.json']),
    ],
)

dc_resource('frontend',
    labels=['app'],
    resource_deps=['backend'],
    links=[link('http://localhost:5173', 'TokyoRadar 前端')],
)

# ----------------------------------------------------------
# 基础设施
# ----------------------------------------------------------
dc_resource('db', labels=['infra'])
dc_resource('redis', labels=['infra'])

# ----------------------------------------------------------
# 手动任务 (Tilt 面板中点击按钮触发)
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
