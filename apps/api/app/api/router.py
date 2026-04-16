from fastapi import APIRouter

from app.api.routes.interviews import router as interviews_router

api_router = APIRouter()
api_router.include_router(interviews_router)
