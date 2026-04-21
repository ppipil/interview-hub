from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import Settings
from app.core.errors import ConfigError, UpstreamServiceError


@dataclass(frozen=True)
class SecondMeTokenSet:
  access_token: str
  refresh_token: Optional[str]
  expires_at: Optional[str]
  scope: List[str]
  response_keys: List[str]
  key_like_paths: List[str]


@dataclass(frozen=True)
class SecondMeAvatar:
  avatar_id: str
  name: str


@dataclass(frozen=True)
class SecondMeAvatarApiKey:
  key_id: Optional[str]
  avatar_id: str
  name: str
  secret_key: str
  enabled: bool


class SecondMeOAuthClient:
  def __init__(self, settings: Settings, transport: Optional[httpx.AsyncBaseTransport] = None) -> None:
    self._base_url = settings.secondme_visitor_base_url.rstrip("/")
    self._authorize_url = settings.secondme_oauth_authorize_url
    self._token_url = settings.secondme_oauth_token_url
    self._client_id = settings.secondme_app_client_id
    self._client_secret = settings.secondme_app_client_secret
    self._redirect_uri = settings.secondme_oauth_redirect_uri
    self._scopes = settings.secondme_oauth_scopes
    self._timeout = settings.request_timeout_seconds
    self._transport = transport

  @property
  def configured(self) -> bool:
    return bool(self._client_id and self._client_secret and self._redirect_uri)

  def build_authorization_url(self, state: str) -> str:
    self._require_configured()
    params = {
      "response_type": "code",
      "client_id": self._client_id,
      "redirect_uri": self._redirect_uri,
      "scope": self._scopes,
      "state": state,
    }
    return str(httpx.URL(self._authorize_url, params=params))

  async def exchange_code(self, code: str) -> SecondMeTokenSet:
    self._require_configured()
    payload = await self._form_request(
      self._token_url,
      data={
        "grant_type": "authorization_code",
        "client_id": self._client_id,
        "client_secret": self._client_secret,
        "redirect_uri": self._redirect_uri,
        "code": code,
      },
      error_code="SECONDME_OAUTH_TOKEN_ERROR",
    )
    data = self._data_object(payload, "SecondMe OAuth token 响应缺少 data。")
    access_token = self._require_field(data, "accessToken")
    refresh_token = data.get("refreshToken")
    expires_in = data.get("expiresIn")
    expires_at = None
    if expires_in:
      expires_at = (datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))).isoformat()
    return SecondMeTokenSet(
      access_token=access_token,
      refresh_token=str(refresh_token) if refresh_token else None,
      expires_at=expires_at,
      scope=self._normalize_scope(data.get("scope")),
      response_keys=sorted(data.keys()),
      key_like_paths=self.find_key_like_paths(data),
    )

  async def get_user_info(self, access_token: str) -> Dict[str, Any]:
    payload = await self._json_request(
      "GET",
      "/api/secondme/user/info",
      access_token=access_token,
      error_code="SECONDME_USER_INFO_ERROR",
    )
    return self._data_object(payload, "SecondMe 用户信息响应缺少 data。")

  async def list_avatars(self, access_token: str) -> List[SecondMeAvatar]:
    payload = await self._json_request(
      "GET",
      "/api/secondme/avatar/list?pageNo=1&pageSize=20",
      access_token=access_token,
      error_code="SECONDME_AVATAR_LIST_ERROR",
    )
    data = payload.get("data")
    items = self._extract_items(data)
    avatars: List[SecondMeAvatar] = []
    for item in items:
      if not isinstance(item, dict):
        continue
      avatar_id = item.get("avatarId") or item.get("id")
      if avatar_id is None:
        continue
      name = item.get("avatarName") or item.get("name") or item.get("nickname") or f"Avatar {avatar_id}"
      avatars.append(SecondMeAvatar(avatar_id=str(avatar_id), name=str(name)))
    return avatars

  async def create_avatar_api_key(
    self,
    *,
    access_token: str,
    avatar_id: str,
    name: str,
  ) -> SecondMeAvatarApiKey:
    payload = await self._json_request(
      "POST",
      "/api/secondme/avatar/api-key/create",
      access_token=access_token,
      json={
        "avatarId": int(avatar_id) if str(avatar_id).isdigit() else avatar_id,
        "name": name,
      },
      error_code="SECONDME_AVATAR_API_KEY_CREATE_ERROR",
    )
    data = self._data_object(payload, "SecondMe 分身 API Key 创建响应缺少 data。")
    secret_key = self._require_field(data, "secretKey")
    return SecondMeAvatarApiKey(
      key_id=str(data.get("keyId")) if data.get("keyId") is not None else None,
      avatar_id=str(data.get("avatarId") or avatar_id),
      name=str(data.get("name") or name),
      secret_key=secret_key,
      enabled=bool(data.get("enabled", True)),
    )

  async def _form_request(self, url: str, data: Dict[str, str], error_code: str) -> Dict[str, Any]:
    try:
      async with httpx.AsyncClient(timeout=self._timeout, trust_env=False, transport=self._transport) as client:
        response = await client.post(
          url,
          headers={"Content-Type": "application/x-www-form-urlencoded"},
          data=data,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPStatusError as exc:
      raise UpstreamServiceError(
        f"SecondMe OAuth 请求失败，HTTP {exc.response.status_code}",
        code=error_code,
      ) from exc
    except httpx.HTTPError as exc:
      raise UpstreamServiceError("当前无法连接 SecondMe OAuth 服务。", code=error_code) from exc
    except ValueError as exc:
      raise UpstreamServiceError("SecondMe OAuth 响应无法解析。", code=error_code) from exc
    self._ensure_success(payload, error_code)
    return payload

  async def _json_request(
    self,
    method: str,
    path: str,
    *,
    access_token: str,
    error_code: str,
    json: Optional[Dict[str, Any]] = None,
  ) -> Dict[str, Any]:
    try:
      async with httpx.AsyncClient(timeout=self._timeout, trust_env=False, transport=self._transport) as client:
        response = await client.request(
          method,
          f"{self._base_url}{path}",
          headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
          },
          json=json,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPStatusError as exc:
      raise UpstreamServiceError(
        f"SecondMe API 请求失败，HTTP {exc.response.status_code}",
        code=error_code,
      ) from exc
    except httpx.HTTPError as exc:
      raise UpstreamServiceError("当前无法连接 SecondMe API 服务。", code=error_code) from exc
    except ValueError as exc:
      raise UpstreamServiceError("SecondMe API 响应无法解析。", code=error_code) from exc
    self._ensure_success(payload, error_code)
    return payload

  def _require_configured(self) -> None:
    if not self.configured:
      raise ConfigError(
        "SecondMe OAuth 配置缺失，请先补齐 SECONDME_APP_CLIENT_ID、SECONDME_APP_CLIENT_SECRET 和 SECONDME_OAUTH_REDIRECT_URI。",
      )

  def _ensure_success(self, payload: Dict[str, Any], error_code: str) -> None:
    if payload.get("code") != 0:
      raise UpstreamServiceError(
        str(payload.get("msg") or payload.get("message") or "SecondMe API 请求失败。"),
        code=error_code,
      )

  def _data_object(self, payload: Dict[str, Any], message: str) -> Dict[str, Any]:
    data = payload.get("data")
    if not isinstance(data, dict):
      raise UpstreamServiceError(message, code="SECONDME_RESPONSE_FORMAT_ERROR")
    return data

  def _extract_items(self, data: Any) -> List[Any]:
    if isinstance(data, list):
      return data
    if isinstance(data, dict):
      for key in ("records", "list", "items", "rows", "data"):
        value = data.get(key)
        if isinstance(value, list):
          return value
    return []

  def _require_field(self, payload: Dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if value is None or value == "":
      raise UpstreamServiceError(f"SecondMe 响应缺少必需字段：{field}", code="SECONDME_RESPONSE_FORMAT_ERROR")
    return str(value)

  def _normalize_scope(self, raw_scope: Any) -> List[str]:
    if isinstance(raw_scope, list):
      return [str(item) for item in raw_scope]
    if isinstance(raw_scope, str):
      return [item for item in raw_scope.replace(",", " ").split(" ") if item]
    return []

  def find_key_like_paths(self, payload: Any, prefix: str = "") -> List[str]:
    paths: List[str] = []
    if isinstance(payload, dict):
      for key, value in payload.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        normalized_key = str(key).lower()
        if any(marker in normalized_key for marker in ("sk", "key", "secret", "apikey", "api_key")):
          paths.append(f"{path}: {self.describe_safe_value(value)}")
        paths.extend(self.find_key_like_paths(value, path))
    elif isinstance(payload, list):
      for index, item in enumerate(payload[:3]):
        paths.extend(self.find_key_like_paths(item, f"{prefix}[{index}]"))
    elif isinstance(payload, str) and payload.startswith("sk-"):
      paths.append(f"{prefix}: string(sk-like,len={len(payload)})")
    return list(dict.fromkeys(paths))

  def describe_safe_value(self, value: Any) -> str:
    if value is None:
      return "null"
    if isinstance(value, bool):
      return "boolean"
    if isinstance(value, int):
      return "integer"
    if isinstance(value, float):
      return "number"
    if isinstance(value, str):
      if value.startswith("sk-"):
        return f"string(sk-like,len={len(value)})"
      if value.startswith(("http://", "https://")):
        return "string(url)"
      if value.isdigit():
        return f"string(digits,len={len(value)})"
      return f"string(len={len(value)})"
    if isinstance(value, list):
      return f"list(len={len(value)})"
    if isinstance(value, dict):
      return f"object(keys={','.join(sorted(value.keys()))})"
    return type(value).__name__
