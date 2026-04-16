from __future__ import annotations

from dataclasses import dataclass


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
class SessionRuntime:
  secondme_session_id: str
  auth: SecondMeAuthContext
  chat: SecondMeChatContext
  socket: SecondMeSocketInfo
  next_index: int = 1
