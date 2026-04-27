from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.models.api import (
  InterviewMode,
  InterviewRole,
  InterviewStageKey,
  InterviewerProvider,
  InterviewerType,
  QuestionBankScopeType,
)


@dataclass(frozen=True)
class InterviewerSecretEntry:
  interviewer_id: str
  avatar_api_key: str
  created_at: str
  updated_at: str


@dataclass(frozen=True)
class InterviewerProfileEntry:
  interviewer_id: str
  skill_prompt: Optional[str]
  avatar_api_key: Optional[str]
  enabled: bool
  created_at: str
  updated_at: str
  type: Optional[InterviewerType] = None
  provider: Optional[InterviewerProvider] = None
  name: Optional[str] = None
  title: Optional[str] = None
  description: Optional[str] = None
  avatar_url: Optional[str] = None
  tags: Optional[List[str]] = None
  supported_roles: Optional[List[InterviewRole]] = None
  supported_modes: Optional[List[InterviewMode]] = None
  persona: Optional[str] = None
  prompt_strategy: Optional[str] = None
  interview_flow: Optional[str] = None


@dataclass(frozen=True)
class SecondMeConnectionEntry:
  interviewer_id: str
  secondme_user_id: Optional[str]
  avatar_id: str
  avatar_name: str
  access_token: str
  refresh_token: Optional[str]
  token_expires_at: Optional[str]
  scope: List[str]
  avatar_api_key: str
  created_at: str
  updated_at: str


@dataclass(frozen=True)
class QuestionBankEntry:
  id: str
  role: InterviewRole
  mode: Optional[InterviewMode]
  interviewer_type: InterviewerType
  provider: InterviewerProvider
  prompt_strategy: str
  question: str
  source_session_id: Optional[str]
  created_at: str


@dataclass(frozen=True)
class FormalQuestionBankWrite:
  scope_type: QuestionBankScopeType
  interviewer_id: Optional[str]
  role: InterviewRole
  stage_key: InterviewStageKey
  question: str
  reference_answer: Optional[str]
  tags: List[str]
  enabled: bool
  sort_order: int


@dataclass(frozen=True)
class FormalQuestionBankEntry:
  id: str
  scope_type: QuestionBankScopeType
  interviewer_id: Optional[str]
  role: InterviewRole
  stage_key: InterviewStageKey
  question: str
  reference_answer: Optional[str]
  tags: List[str]
  enabled: bool
  sort_order: int
  created_at: str
  updated_at: str


@dataclass(frozen=True)
class FormalQuestionUsageEntry:
  message_id: str
  session_id: str
  question_id: str
  interviewer_id: str
  role: InterviewRole
  round_number: int
  stage_key: InterviewStageKey
  source_scope: QuestionBankScopeType
  used_at: str
