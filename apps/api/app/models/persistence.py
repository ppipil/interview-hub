from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.models.api import InterviewMode, InterviewRole, InterviewerProvider, InterviewerType


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
