from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import json
from typing import Any, Dict, Optional

from app.core.config import Settings
from app.core.errors import BadRequestError, ConfigError, UpstreamServiceError
from app.models.persistence import SecondMeConnectionEntry
from app.repositories.persistence import PersistenceRepository
from app.services.secondme_oauth_client import SecondMeAvatar, SecondMeOAuthClient


@dataclass(frozen=True)
class SecondMeOAuthSyncResult:
  interviewer_id: str
  secondme_user_id: Optional[str]
  avatar_id: str
  avatar_name: str


@dataclass(frozen=True)
class SecondMeOAuthInspectResult:
  interviewer_id: str
  granted_scopes: list[str]
  token_response_keys: list[str]
  token_key_like_paths: list[str]
  user_info_shape: str
  user_info_candidates: str
  user_info_key_like_paths: list[str]


class SecondMeOAuthService:
  def __init__(
    self,
    settings: Settings,
    client: SecondMeOAuthClient,
    persistence: PersistenceRepository,
  ) -> None:
    self._settings = settings
    self._client = client
    self._persistence = persistence

  def build_login_url(self, interviewer_id: Optional[str] = None) -> str:
    target_interviewer_id = interviewer_id or self._settings.avatar_interviewer_id
    state = self._sign_state({"interviewerId": target_interviewer_id})
    return self._client.build_authorization_url(state)

  def build_inspect_login_url(self, interviewer_id: Optional[str] = None) -> str:
    target_interviewer_id = interviewer_id or self._settings.avatar_interviewer_id
    state = self._sign_state({"interviewerId": target_interviewer_id, "mode": "inspect"})
    return self._client.build_authorization_url(state)

  def is_inspect_state(self, state: str) -> bool:
    return self._verify_state(state).get("mode") == "inspect"

  async def inspect_callback(self, code: str, state: str) -> SecondMeOAuthInspectResult:
    if not code.strip():
      raise BadRequestError("SecondMe OAuth callback 缺少 code。")

    state_payload = self._verify_state(state)
    interviewer_id = str(state_payload.get("interviewerId") or self._settings.avatar_interviewer_id)
    token_set = await self._client.exchange_code(code.strip())
    user_info = await self._client.get_user_info(token_set.access_token)
    return SecondMeOAuthInspectResult(
      interviewer_id=interviewer_id,
      granted_scopes=token_set.scope,
      token_response_keys=token_set.response_keys,
      token_key_like_paths=token_set.key_like_paths,
      user_info_shape=self._summarize_user_info_shape(user_info),
      user_info_candidates=self._summarize_user_info_candidates(user_info),
      user_info_key_like_paths=self._client.find_key_like_paths(user_info),
    )

  async def handle_callback(self, code: str, state: str) -> SecondMeOAuthSyncResult:
    if not code.strip():
      raise BadRequestError("SecondMe OAuth callback 缺少 code。")

    state_payload = self._verify_state(state)
    interviewer_id = str(state_payload.get("interviewerId") or self._settings.avatar_interviewer_id)
    token_set = await self._client.exchange_code(code.strip())
    user_info = await self._client.get_user_info(token_set.access_token)
    avatar = await self._resolve_avatar(token_set.access_token, token_set.scope, user_info)
    api_key = await self._client.create_avatar_api_key(
      access_token=token_set.access_token,
      avatar_id=avatar.avatar_id,
      name=self._settings.secondme_avatar_api_key_name,
    )

    now = datetime.now(timezone.utc).isoformat()
    connection = SecondMeConnectionEntry(
      interviewer_id=interviewer_id,
      secondme_user_id=self._extract_user_id(user_info),
      avatar_id=api_key.avatar_id,
      avatar_name=avatar.name,
      access_token=token_set.access_token,
      refresh_token=token_set.refresh_token,
      token_expires_at=token_set.expires_at,
      scope=token_set.scope,
      avatar_api_key=api_key.secret_key,
      created_at=now,
      updated_at=now,
    )
    self._persistence.save_secondme_connection(connection)
    self._persistence.upsert_interviewer_secret(interviewer_id, api_key.secret_key)

    return SecondMeOAuthSyncResult(
      interviewer_id=interviewer_id,
      secondme_user_id=connection.secondme_user_id,
      avatar_id=api_key.avatar_id,
      avatar_name=avatar.name,
    )

  async def _resolve_avatar(
    self,
    access_token: str,
    granted_scopes: list[str],
    user_info: Dict[str, Any],
  ) -> SecondMeAvatar:
    avatar = self._extract_avatar_from_user_info(user_info)
    if avatar:
      return avatar

    self._assert_required_scopes(granted_scopes, ["avatar.read"], user_info)
    avatars = await self._client.list_avatars(access_token)
    return self._select_avatar(avatars)

  def _select_avatar(self, avatars: list[SecondMeAvatar]) -> SecondMeAvatar:
    if not avatars:
      raise UpstreamServiceError("当前 SecondMe 用户没有可用分身，无法创建分身 API Key。", code="SECONDME_AVATAR_NOT_FOUND")
    return avatars[0]

  def _extract_avatar_from_user_info(self, user_info: Dict[str, Any]) -> Optional[SecondMeAvatar]:
    for key in ("avatarId", "avatar_id", "defaultAvatarId", "default_avatar_id"):
      value = user_info.get(key)
      if value is not None and value != "":
        return SecondMeAvatar(avatar_id=str(value), name=self._extract_avatar_name(user_info, value))

    for key in ("avatar", "avatarInfo", "avatar_info", "defaultAvatar", "default_avatar"):
      value = user_info.get(key)
      if isinstance(value, dict):
        avatar_id = value.get("avatarId") or value.get("avatar_id") or value.get("id")
        if avatar_id is not None and avatar_id != "":
          return SecondMeAvatar(avatar_id=str(avatar_id), name=self._extract_avatar_name(value, avatar_id))

    avatars = user_info.get("avatars")
    if isinstance(avatars, list):
      for item in avatars:
        if not isinstance(item, dict):
          continue
        avatar_id = item.get("avatarId") or item.get("avatar_id") or item.get("id")
        if avatar_id is not None and avatar_id != "":
          return SecondMeAvatar(avatar_id=str(avatar_id), name=self._extract_avatar_name(item, avatar_id))

    return None

  def _extract_avatar_name(self, payload: Dict[str, Any], avatar_id: object) -> str:
    for key in ("avatarName", "avatar_name", "name", "nickname"):
      value = payload.get(key)
      if value is not None and value != "":
        return str(value)
    return f"Avatar {avatar_id}"

  def _extract_user_id(self, user_info: Dict[str, Any]) -> Optional[str]:
    for key in ("id", "userId", "oauthId", "oauth_id", "sub"):
      value = user_info.get(key)
      if value is not None and value != "":
        return str(value)
    return None

  def _assert_required_scopes(
    self,
    granted_scopes: list[str],
    required_scopes: list[str],
    user_info: Optional[Dict[str, Any]] = None,
  ) -> None:
    if not granted_scopes:
      return

    granted = set(granted_scopes)
    missing = [scope for scope in required_scopes if scope not in granted]
    if missing:
      raise UpstreamServiceError(
        "SecondMe 授权成功了，但 user/info 未返回可用于创建 API Key 的分身 ID，且 Access Token 缺少 avatar.read，无法回退查询分身列表。",
        code="SECONDME_OAUTH_SCOPE_MISSING",
        details=[
          {"field": "missingScopes", "message": ", ".join(missing)},
          {"field": "grantedScopes", "message": ", ".join(granted_scopes)},
          {"field": "userInfoShape", "message": self._summarize_user_info_shape(user_info or {})},
          {"field": "userInfoCandidates", "message": self._summarize_user_info_candidates(user_info or {})},
        ],
      )

  def _summarize_user_info_shape(self, user_info: Dict[str, Any]) -> str:
    if not user_info:
      return "empty"

    parts = [f"root keys: {', '.join(sorted(user_info.keys()))}"]
    for key in ("avatar", "avatarInfo", "avatar_info", "defaultAvatar", "default_avatar"):
      value = user_info.get(key)
      if isinstance(value, dict):
        parts.append(f"{key} keys: {', '.join(sorted(value.keys()))}")
    avatars = user_info.get("avatars")
    if isinstance(avatars, list):
      if avatars and isinstance(avatars[0], dict):
        parts.append(f"avatars[0] keys: {', '.join(sorted(avatars[0].keys()))}")
      else:
        parts.append(f"avatars length: {len(avatars)}")
    return "; ".join(parts)

  def _summarize_user_info_candidates(self, user_info: Dict[str, Any]) -> str:
    if not user_info:
      return "empty"

    candidate_keys = (
      "avatar",
      "route",
      "userId",
      "accountStatus",
      "hasVoice",
      "profileCompleteness",
    )
    parts = []
    for key in candidate_keys:
      if key in user_info:
        parts.append(f"{key}: {self._describe_safe_value(user_info.get(key))}")
    return "; ".join(parts) if parts else "none"

  def _describe_safe_value(self, value: Any) -> str:
    if value is None:
      return "null"
    if isinstance(value, bool):
      return "boolean"
    if isinstance(value, int):
      return "integer"
    if isinstance(value, float):
      return "number"
    if isinstance(value, str):
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

  def _sign_state(self, payload: Dict[str, str]) -> str:
    raw_payload = {
      **payload,
      "ts": str(int(datetime.now(timezone.utc).timestamp())),
    }
    encoded_payload = self._b64encode(json.dumps(raw_payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8"))
    signature = hmac.new(
      self._state_secret().encode("utf-8"),
      encoded_payload.encode("utf-8"),
      hashlib.sha256,
    ).hexdigest()
    return f"{encoded_payload}.{signature}"

  def _verify_state(self, state: str) -> Dict[str, Any]:
    if not state or "." not in state:
      raise BadRequestError("SecondMe OAuth callback 缺少有效 state。")

    encoded_payload, signature = state.split(".", 1)
    expected_signature = hmac.new(
      self._state_secret().encode("utf-8"),
      encoded_payload.encode("utf-8"),
      hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
      raise BadRequestError("SecondMe OAuth state 校验失败。")

    try:
      payload = json.loads(base64.urlsafe_b64decode(self._pad_b64(encoded_payload)).decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
      raise BadRequestError("SecondMe OAuth state 无法解析。") from exc
    if not isinstance(payload, dict):
      raise BadRequestError("SecondMe OAuth state 格式异常。")
    return payload

  def _state_secret(self) -> str:
    secret = self._settings.secondme_oauth_state_secret or self._settings.secondme_app_client_secret
    if not secret:
      raise ConfigError("SecondMe OAuth state secret 缺失，请配置 SECONDME_OAUTH_STATE_SECRET 或 SECONDME_APP_CLIENT_SECRET。")
    return secret

  def _b64encode(self, raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")

  def _pad_b64(self, value: str) -> bytes:
    return f"{value}{'=' * (-len(value) % 4)}".encode("utf-8")
