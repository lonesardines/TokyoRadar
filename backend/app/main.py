from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.routing import Route

from app.api.v1.router import api_router
from app.config import settings
from app.mcp_server import mcp

# Trigger lazy creation of session manager and get ASGI handler
_mcp_app = mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title="TokyoRadar API",
    description="Japanese Fashion Intelligence Radar",
    version="0.1.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

# Mount MCP as raw ASGI route — handles GET (SSE), POST, DELETE
from mcp.server.fastmcp.server import StreamableHTTPASGIApp
_mcp_asgi = StreamableHTTPASGIApp(mcp.session_manager)
app.router.routes.insert(0, Route("/mcp", endpoint=_mcp_asgi))


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/api/v1")
