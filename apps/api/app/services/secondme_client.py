from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import uuid4
import time

import httpx

from app.core.config import Settings
from app.core.errors import UpstreamServiceError
from app.models.runtime import SecondMeAuthContext, SecondMeChatContext, SecondMeSocketInfo


class SecondMeClient:
  def __init__(self, settings: Settings) -> None:
    self._base_url = settings.secondme_base_url.rstrip("/")
    self._timeout = settings.request_timeout_seconds
    self._channel = settings.secondme_channel

  async def authenticate(
    self,
    api_key: str,
    visitor_id: str,
    visitor_name: str,
  ) -> SecondMeAuthContext:
    payload = {
      "visitorId": visitor_id,
      "visitorName": visitor_name,
      "channel": self._channel,
    }
    response = await self._request(
      "POST",
      "/rest/open/avatar/auth",
      headers={"Authorization": f"Bearer {api_key}"},
      json=payload,
    )
    return SecondMeAuthContext(
      visitor_id=visitor_id,
      visitor_token=self._require_field(response, "visitorToken"),
      visitor_user_id=self._require_field(response, "visitorUserId"),
      visitor_mind_id=self._require_field(response, "visitorMindId"),
      avatar_share_code=self._require_field(response, "avatarShareCode"),
      avatar_name=self._require_field(response, "avatarName"),
      owner_user_id=self._require_field(response, "ownerUserId"),
    )

  async def initialize_chat(
    self,
    visitor_token: str,
    visitor_id: str,
    share_code: str,
  ) -> SecondMeChatContext:
    response = await self._request(
      "POST",
      "/rest/os/avatar/chat/init",
      headers=self._visitor_headers(visitor_token, visitor_id),
      json={"shareCode": share_code},
    )
    return SecondMeChatContext(
      mind_id=self._require_field(response, "mindId"),
      avatar_name=self._require_field(response, "avatarName"),
      owner_user_id=self._require_field(response, "ownerUserId"),
      opening=response.get("opening", ""),
    )

  async def create_websocket(
    self,
    visitor_token: str,
    visitor_id: str,
    visitor_user_id: str,
  ) -> SecondMeSocketInfo:
    response = await self._request(
      "POST",
      "/rest/general/ws/create",
      headers=self._visitor_headers(visitor_token, visitor_id),
      json={
        "userId": visitor_user_id,
        "channel": ["ALL"],
        "apiVersion": "1.3.0",
        "sdkVersion": "1.0.0",
      },
    )

    address = response.get("address") or response.get("wsAddress") or response.get("url")
    ws_id = response.get("wsId") or response.get("id")
    if not address or not ws_id:
      raise UpstreamServiceError("SecondMe WebSocket 初始化返回缺少 address 或 wsId。")

    return SecondMeSocketInfo(address=address, ws_id=ws_id)

  async def create_session(
    self,
    visitor_token: str,
    visitor_id: str,
    visitor_mind_id: str,
    owner_user_id: str,
  ) -> str:
    payload = {
      "mindId": self._normalize_mind_id(visitor_mind_id),
      "mindType": "shadow",
      "mode": "PERSONAL",
      "sessionType": "SHARE",
      "memberUserIds": [owner_user_id],
    }
    response = await self._request(
      "POST",
      "/rest/general/session/create",
      headers=self._visitor_headers(visitor_token, visitor_id),
      json=payload,
    )
    return str(response.get("sessionId") or response.get("id") or self._require_field(response, "sessionId"))

  async def get_avatar_id(
    self,
    visitor_token: str,
    share_code: str,
  ) -> int:
    response = await self._request(
      "GET",
      f"/rest/os/avatar/public/{share_code}",
      headers={"token": visitor_token},
    )
    avatar_id = response.get("id")
    if avatar_id is None:
      raise UpstreamServiceError("SecondMe 分身详情返回缺少 avatarId。")
    return int(avatar_id)

  async def bind_session(
    self,
    visitor_token: str,
    visitor_id: str,
    avatar_id: int,
    session_id: str,
  ) -> None:
    await self._request(
      "POST",
      "/rest/os/avatar/chat/start",
      headers=self._visitor_headers(visitor_token, visitor_id),
      json={"avatarId": avatar_id, "sessionId": session_id},
      allow_empty_data=True,
    )

  async def send_message(
    self,
    visitor_token: str,
    visitor_id: str,
    session_id: str,
    visitor_user_id: str,
    mind_id: str,
    ws_id: str,
    content: str,
    index: int,
  ) -> None:
    timestamp = int(time.time() * 1000)
    message_id = f"{uuid4().hex}_____{timestamp}"
    payload = {
      "timestamp": timestamp,
      "seqId": message_id,
      "sessionId": session_id,
      "userId": visitor_user_id,
      "messageId": message_id,
      "mindId": mind_id,
      "index": index,
      "sendUserId": visitor_user_id,
      "dataType": "text",
      "sender": "client",
      "type": "msg",
      "wsId": ws_id,
      "data": {"content": content},
    }
    await self._request(
      "POST",
      "/rest/general/message/send",
      headers=self._visitor_headers(visitor_token, visitor_id),
      json=payload,
      allow_empty_data=True,
    )

  async def _request(
    self,
    method: str,
    path: str,
    headers: Dict[str, str],
    json: Optional[Dict[str, Any]] = None,
    allow_empty_data: bool = False,
  ) -> Dict[str, Any]:
    url = f"{self._base_url}{path}"
    try:
      async with httpx.AsyncClient(timeout=self._timeout, trust_env=False) as client:
        response = await client.request(method, url, headers=headers, json=json)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPStatusError as exc:
      raise UpstreamServiceError(
        message=f"SecondMe 请求失败，HTTP {exc.response.status_code}",
        code="SECONDME_HTTP_ERROR",
      ) from exc
    except httpx.HTTPError as exc:
      raise UpstreamServiceError(
        message="当前无法连接 SecondMe 服务，请稍后重试。",
        code="SECONDME_CONNECT_ERROR",
      ) from exc
    except ValueError as exc:
      raise UpstreamServiceError(
        message="SecondMe 返回了无法解析的响应内容。",
        code="SECONDME_RESPONSE_PARSE_ERROR",
      ) from exc

    if payload.get("code") != 0:
      raise UpstreamServiceError(
        message=str(payload.get("msg") or payload.get("message") or "SecondMe 服务返回异常。"),
        code=str(payload.get("code")),
      )

    data = payload.get("data")
    if allow_empty_data and data is None:
      return {}
    if not isinstance(data, dict):
      raise UpstreamServiceError("SecondMe 响应格式异常，缺少 data 对象。")
    return data

  def _visitor_headers(self, visitor_token: str, visitor_id: str) -> Dict[str, str]:
    return {
      "token": visitor_token,
      "Fp": visitor_id,
      "Content-Type": "application/json",
    }

  def _require_field(self, payload: Dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if value is None or value == "":
      raise UpstreamServiceError(f"SecondMe 响应缺少必需字段：{field}")
    return str(value)

  def _normalize_mind_id(self, visitor_mind_id: str) -> Any:
    return int(visitor_mind_id) if visitor_mind_id.isdigit() else visitor_mind_id
