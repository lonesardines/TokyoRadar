from fastapi import APIRouter

from app.api.v1 import admin, agent, brands, categories, items, proxy_services, retailers

api_router = APIRouter()

api_router.include_router(brands.router, prefix="/brands", tags=["brands"])
api_router.include_router(retailers.router, prefix="/retailers", tags=["retailers"])
api_router.include_router(
    proxy_services.router, prefix="/proxy-services", tags=["proxy-services"]
)
api_router.include_router(
    categories.router, prefix="/categories", tags=["categories"]
)
api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(agent.router, prefix="/admin", tags=["agent"])


@api_router.get("", tags=["root"])
def api_root() -> dict[str, str]:
    return {"message": "TokyoRadar API v1"}
