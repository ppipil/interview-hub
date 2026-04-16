from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.dependencies import get_interview_service

settings = get_settings()

app = FastAPI(
  title=settings.app_name,
  version=settings.app_version,
  description="SecondMe-backed Interview Hub MVP backend",
)
if settings.cors_origins:
  app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_origin_regex=settings.cors_origin_regex or None,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
  )
register_exception_handlers(app)
app.include_router(api_router)


@app.get("/health")
def healthcheck() -> dict:
  return {"status": "ok", "service": settings.app_name}


@app.on_event("shutdown")
async def shutdown_event() -> None:
  await get_interview_service().close()
