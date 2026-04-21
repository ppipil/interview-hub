from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import httpx

from app.core.config import Settings
from app.core.errors import UpstreamServiceError


@dataclass
class VisitorChatSession:
  access_token: str
  session_id: str
  ws_url: str
  avatar_name: str
  opening: str


@dataclass
class CachedAppToken:
  access_token: str
  expires_at: datetime


class SecondMeVisitorChatClient:
  def __init__(self, settings: Settings) -> None:
    self._base_url = settings.secondme_visitor_base_url.rstrip("/")
    self._client_id = settings.secondme_app_client_id
    self._client_secret = settings.secondme_app_client_secret
    self._avatar_api_key = settings.secondme_avatar_api_key
    self._timeout = settings.request_timeout_seconds
    self._cached_token: Optional[CachedAppToken] = None

  @property
  def configured(self) -> bool:
    return bool(self._client_id and self._client_secret)

  @property
  def avatar_api_key(self) -> str:
    return self._avatar_api_key

  async def initialize_chat(
    self,
    visitor_id: str,
    visitor_name: str,
    avatar_api_key: Optional[str] = None,
  ) -> VisitorChatSession:
    access_token = await self._get_app_token()
    resolved_avatar_api_key = self._resolve_avatar_api_key(avatar_api_key)
    payload = await self._request(
      "POST",
      "/api/secondme/visitor-chat/init",
      headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
      },
      json={
        "apiKey": resolved_avatar_api_key,
        "visitorId": visitor_id,
        "visitorName": visitor_name,
      },
    )
    return VisitorChatSession(
      access_token=access_token,
      session_id=self._require_field(payload, "sessionId"),
      ws_url=self._require_field(payload, "wsUrl"),
      avatar_name=str(payload.get("avatarName") or "SecondMe Avatar"),
      opening=str(payload.get("opening") or ""),
    )

  async def send_message(
    self,
    access_token: str,
    session_id: str,
    message: str,
    avatar_api_key: Optional[str] = None,
  ) -> None:
    resolved_avatar_api_key = self._resolve_avatar_api_key(avatar_api_key)
    await self._request(
      "POST",
      "/api/secondme/visitor-chat/send",
      headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
      },
      json={
        "sessionId": session_id,
        "apiKey": resolved_avatar_api_key,
        "message": message,
      },
      allow_empty_data=True,
    )

  async def _get_app_token(self) -> str:
    if not self.configured:
      raise UpstreamServiceError(
        "SecondMe Visitor Chat 配置缺失，请先补齐 SECONDME_APP_CLIENT_ID 和 SECONDME_APP_CLIENT_SECRET。",
        code="SECONDME_VISITOR_NOT_CONFIGURED",
      )

    cached = self._cached_token
    now = datetime.now(timezone.utc)
    if cached and cached.expires_at > now + timedelta(minutes=5):
      return cached.access_token

    try:
      async with httpx.AsyncClient(timeout=self._timeout, trust_env=False) as client:
        response = await client.post(
          f"{self._base_url}/api/oauth/token/client",
          headers={"Content-Type": "application/x-www-form-urlencoded"},
          data={
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "scope": "chat.write",
          },
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPStatusError as exc:
      raise UpstreamServiceError(
        f"SecondMe Visitor Chat 换取 app token 失败，HTTP {exc.response.status_code}",
        code="SECONDME_VISITOR_HTTP_ERROR",
      ) from exc
    except httpx.HTTPError as exc:
      raise UpstreamServiceError(
        "当前无法连接 SecondMe Visitor Chat 服务，请稍后重试。",
        code="SECONDME_VISITOR_CONNECT_ERROR",
      ) from exc
    except ValueError as exc:
      raise UpstreamServiceError(
        "SecondMe Visitor Chat token 响应无法解析。",
        code="SECONDME_VISITOR_RESPONSE_PARSE_ERROR",
      ) from exc

    if payload.get("code") != 0:
      raise UpstreamServiceError(
        str(payload.get("msg") or payload.get("message") or "SecondMe Visitor Chat token 请求失败。"),
        code=str(payload.get("code") or "SECONDME_VISITOR_TOKEN_ERROR"),
      )

    data = payload.get("data")
    if not isinstance(data, dict):
      raise UpstreamServiceError("SecondMe Visitor Chat token 响应缺少 data。", code="SECONDME_VISITOR_TOKEN_ERROR")

    access_token = self._require_field(data, "accessToken")
    expires_in = int(data.get("expiresIn") or 0)
    if expires_in <= 0:
      raise UpstreamServiceError("SecondMe Visitor Chat token 响应缺少 expiresIn。", code="SECONDME_VISITOR_TOKEN_ERROR")

    self._cached_token = CachedAppToken(
      access_token=access_token,
      expires_at=now + timedelta(seconds=expires_in),
    )
    return access_token

  def _resolve_avatar_api_key(self, avatar_api_key: Optional[str]) -> str:
    resolved = str(avatar_api_key or self._avatar_api_key).strip()
    if not resolved:
      raise UpstreamServiceError(
        "SecondMe Visitor Chat 缺少分身 API Key。",
        code="SECONDME_VISITOR_AVATAR_API_KEY_MISSING",
      )
    return resolved

  async def _request(
    self,
    method: str,
    path: str,
    headers: Dict[str, str],
    json: Optional[Dict[str, Any]] = None,
    allow_empty_data: bool = False,
  ) -> Dict[str, Any]:
    try:
      async with httpx.AsyncClient(timeout=self._timeout, trust_env=False) as client:
        response = await client.request(
          method,
          f"{self._base_url}{path}",
          headers=headers,
          json=json,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPStatusError as exc:
      raise UpstreamServiceError(
        f"SecondMe Visitor Chat 请求失败，HTTP {exc.response.status_code}",
        code="SECONDME_VISITOR_HTTP_ERROR",
      ) from exc
    except httpx.HTTPError as exc:
      raise UpstreamServiceError(
        "当前无法连接 SecondMe Visitor Chat 服务，请稍后重试。",
        code="SECONDME_VISITOR_CONNECT_ERROR",
      ) from exc
    except ValueError as exc:
      raise UpstreamServiceError(
        "SecondMe Visitor Chat 返回了无法解析的响应内容。",
        code="SECONDME_VISITOR_RESPONSE_PARSE_ERROR",
      ) from exc

    if payload.get("code") != 0:
      raise UpstreamServiceError(
        str(payload.get("msg") or payload.get("message") or "SecondMe Visitor Chat 服务返回异常。"),
        code=str(payload.get("code") or "SECONDME_VISITOR_ERROR"),
      )

    data = payload.get("data")
    if allow_empty_data and data is None:
      return {}
    if not isinstance(data, dict):
      raise UpstreamServiceError("SecondMe Visitor Chat 响应格式异常，缺少 data 对象。", code="SECONDME_VISITOR_ERROR")
    return data

  def _require_field(self, payload: Dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if value is None or value == "":
      raise UpstreamServiceError(f"SecondMe Visitor Chat 响应缺少必需字段：{field}", code="SECONDME_VISITOR_ERROR")
    return str(value)
