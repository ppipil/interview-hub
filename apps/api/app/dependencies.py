from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.core.errors import ConfigError
from app.repositories.in_memory import InMemorySessionRepository
from app.repositories.persistence import NullPersistenceRepository, PersistenceRepository
from app.repositories.postgres_persistence import PostgresPersistenceRepository
from app.repositories.sqlite_persistence import SqlitePersistenceRepository
from app.services.catalog import InterviewerCatalog
from app.services.admin_interviewers import AdminInterviewerService
from app.services.doubao_client import DoubaoClient
from app.services.feedback import FeedbackService
from app.services.interview import InterviewService
from app.services.interview_provider import (
  DoubaoInterviewProvider,
  InterviewProviderRegistry,
  LegacySecondMeInterviewProvider,
  SecondMeVisitorInterviewProvider,
)
from app.services.secondme_client import SecondMeClient
from app.services.secondme_oauth import SecondMeOAuthService
from app.services.secondme_oauth_client import SecondMeOAuthClient
from app.services.secondme_visitor_client import SecondMeVisitorChatClient


@lru_cache(maxsize=1)
def get_session_repository() -> InMemorySessionRepository:
  return InMemorySessionRepository()


@lru_cache(maxsize=1)
def get_persistence_repository() -> PersistenceRepository:
  settings = get_settings()
  if not settings.database_enabled:
    return NullPersistenceRepository()

  database_url = settings.database_url.strip()
  if database_url.startswith(("postgresql://", "postgres://", "jdbc:postgresql://")):
    return PostgresPersistenceRepository(database_url)
  if "://" in database_url and not database_url.startswith("sqlite:///"):
    raise ConfigError("DATABASE_URL 仅支持 sqlite:///...、postgresql://... 或 jdbc:postgresql://...。")
  return SqlitePersistenceRepository(database_url)


@lru_cache(maxsize=1)
def get_interviewer_catalog() -> InterviewerCatalog:
  return InterviewerCatalog(get_settings())


@lru_cache(maxsize=1)
def get_feedback_service() -> FeedbackService:
  return FeedbackService()


@lru_cache(maxsize=1)
def get_secondme_client() -> SecondMeClient:
  return SecondMeClient(get_settings())


@lru_cache(maxsize=1)
def get_secondme_visitor_client() -> SecondMeVisitorChatClient:
  return SecondMeVisitorChatClient(get_settings())


@lru_cache(maxsize=1)
def get_secondme_oauth_client() -> SecondMeOAuthClient:
  return SecondMeOAuthClient(get_settings())


@lru_cache(maxsize=1)
def get_secondme_oauth_service() -> SecondMeOAuthService:
  return SecondMeOAuthService(
    settings=get_settings(),
    client=get_secondme_oauth_client(),
    persistence=get_persistence_repository(),
  )


@lru_cache(maxsize=1)
def get_doubao_client() -> DoubaoClient:
  return DoubaoClient(get_settings())


@lru_cache(maxsize=1)
def get_interview_provider_registry() -> InterviewProviderRegistry:
  settings = get_settings()
  feedback_service = get_feedback_service()
  return InterviewProviderRegistry(
    [
      LegacySecondMeInterviewProvider(
        secondme_client=get_secondme_client(),
        feedback_service=feedback_service,
        secondme_api_key=settings.secondme_api_key,
        secondme_avatar_share_code=settings.secondme_avatar_share_code,
        secondme_channel=settings.secondme_channel,
        secondme_ws_origin=settings.secondme_ws_origin,
        heartbeat_interval_seconds=settings.heartbeat_interval_seconds,
        websocket_reply_timeout_seconds=settings.websocket_reply_timeout_seconds,
      ),
      SecondMeVisitorInterviewProvider(
        visitor_client=get_secondme_visitor_client(),
        feedback_service=feedback_service,
        persistence=get_persistence_repository(),
        websocket_reply_timeout_seconds=settings.websocket_reply_timeout_seconds,
      ),
      DoubaoInterviewProvider(
        doubao_client=get_doubao_client(),
        feedback_service=feedback_service,
      ),
    ]
  )


@lru_cache(maxsize=1)
def get_interview_service() -> InterviewService:
  service = InterviewService(
    settings=get_settings(),
    repository=get_session_repository(),
    persistence=get_persistence_repository(),
    catalog=get_interviewer_catalog(),
    providers=get_interview_provider_registry(),
  )
  service.sync_catalog()
  return service


@lru_cache(maxsize=1)
def get_admin_interviewer_service() -> AdminInterviewerService:
  return AdminInterviewerService(
    settings=get_settings(),
    catalog=get_interviewer_catalog(),
    persistence=get_persistence_repository(),
  )
