from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.repositories.in_memory import InMemorySessionRepository
from app.services.catalog import InterviewerCatalog
from app.services.feedback import FeedbackService
from app.services.interview import InterviewService
from app.services.secondme_client import SecondMeClient


@lru_cache(maxsize=1)
def get_session_repository() -> InMemorySessionRepository:
  return InMemorySessionRepository()


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
def get_interview_service() -> InterviewService:
  return InterviewService(
    settings=get_settings(),
    repository=get_session_repository(),
    catalog=get_interviewer_catalog(),
    secondme_client=get_secondme_client(),
    feedback_service=get_feedback_service(),
  )
