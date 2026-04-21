from fastapi import APIRouter

from app.api.routes.auth import legacy_router as legacy_auth_router
from app.api.routes.auth import router as auth_router
from app.api.routes.admin import router as admin_router
from app.api.routes.interviews import router as interviews_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(legacy_auth_router)
api_router.include_router(admin_router)
api_router.include_router(interviews_router)
