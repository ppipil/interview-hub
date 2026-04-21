from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from app.models.api import InterviewerProvider


@dataclass
class SecondMeAuthContext:
  visitor_id: str
  visitor_token: str
  visitor_user_id: str
  visitor_mind_id: str
  avatar_share_code: str
  avatar_name: str
  owner_user_id: str


@dataclass
class SecondMeChatContext:
  mind_id: str
  avatar_name: str
  owner_user_id: str
  opening: str


@dataclass
class SecondMeSocketInfo:
  address: str
  ws_id: str


@dataclass
class SecondMeLegacyRuntime:
  provider: InterviewerProvider
  secondme_session_id: str
  auth: SecondMeAuthContext
  chat: SecondMeChatContext
  socket: SecondMeSocketInfo
  next_index: int = 1


@dataclass
class SecondMeVisitorChatRuntime:
  provider: InterviewerProvider
  session_id: str
  access_token: str
  api_key: str
  visitor_id: str
  visitor_name: str


@dataclass
class DoubaoRuntime:
  provider: InterviewerProvider
  model: str


SessionRuntime = Union[SecondMeLegacyRuntime, SecondMeVisitorChatRuntime, DoubaoRuntime]
