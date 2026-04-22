from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import os


def _load_dotenv() -> None:
  env_path = Path(__file__).resolve().parents[2] / ".env"
  if not env_path.exists():
    return

  for raw_line in env_path.read_text(encoding="utf-8").splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#") or "=" not in line:
      continue

    key, value = line.split("=", 1)
    os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def _read_env(name: str, default: str = "") -> str:
  return os.getenv(name, default).strip()


def _read_env_list(name: str, default: tuple[str, ...] = ()) -> tuple[str, ...]:
  raw = os.getenv(name, "").strip()
  if not raw:
    return default

  return tuple(item.strip() for item in raw.split(",") if item.strip())


def _read_regex_env(name: str, default: str = "") -> str:
  raw = _read_env(name, default)
  if not raw:
    return raw

  # Our local dotenv loader reads backslashes literally, so a copy-pasted
  # regex like `\\.` should be normalized back to `\.` before FastAPI uses it.
  return raw.replace("\\\\", "\\")


@dataclass(frozen=True)
class Settings:
  app_name: str
  app_version: str
  cors_origins: tuple[str, ...]
  cors_origin_regex: str
  database_url: str
  secondme_base_url: str
  secondme_visitor_base_url: str
  secondme_api_key: str
  secondme_avatar_share_code: str
  secondme_app_client_id: str
  secondme_app_client_secret: str
  secondme_avatar_api_key: str
  secondme_oauth_authorize_url: str
  secondme_oauth_token_url: str
  secondme_oauth_redirect_uri: str
  secondme_oauth_scopes: str
  secondme_oauth_state_secret: str
  secondme_avatar_api_key_name: str
  secondme_channel: str
  secondme_ws_origin: str
  frontend_auth_success_url: str
  frontend_auth_error_url: str
  avatar_interviewer_id: str
  avatar_interviewer_name: str
  avatar_interviewer_title: str
  avatar_interviewer_description: str
  avatar_interviewer_avatar_url: str
  system_interviewer_id: str
  system_interviewer_name: str
  system_interviewer_title: str
  system_interviewer_description: str
  system_interviewer_avatar_url: str
  doubao_api_key: str
  doubao_model: str
  doubao_base_url: str
  doubao_request_timeout_seconds: float
  doubao_max_retries: int
  request_timeout_seconds: float
  websocket_reply_timeout_seconds: float
  heartbeat_interval_seconds: int

  @property
  def database_enabled(self) -> bool:
    return bool(self.database_url)

  @property
  def secondme_legacy_enabled(self) -> bool:
    return bool(self.secondme_api_key and self.secondme_avatar_share_code)

  @property
  def secondme_visitor_enabled(self) -> bool:
    return bool(self.secondme_app_client_id and self.secondme_app_client_secret)

  @property
  def doubao_enabled(self) -> bool:
    return bool(self.doubao_api_key and self.doubao_model and self.doubao_base_url)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
  _load_dotenv()
  return Settings(
    app_name="Interview Hub API",
    app_version="0.1.0",
    cors_origins=_read_env_list(
      "BACKEND_CORS_ORIGINS",
      ("http://127.0.0.1:5173", "http://localhost:5173"),
    ),
    cors_origin_regex=_read_regex_env(
      "BACKEND_CORS_ORIGIN_REGEX",
      r"https?://(127\.0\.0\.1|localhost)(:\d+)?|https://[A-Za-z0-9-]+\.(netlify|vercel)\.app",
    ),
    database_url=_read_env("DATABASE_URL"),
    secondme_base_url=_read_env("SECONDME_BASE_URL", "https://mindos-prek8s.mindverse.ai/gate/in"),
    secondme_visitor_base_url=_read_env("SECONDME_VISITOR_BASE_URL", "https://api.mindverse.com/gate/lab"),
    secondme_api_key=_read_env("SECONDME_API_KEY"),
    secondme_avatar_share_code=_read_env("SECONDME_AVATAR_SHARE_CODE"),
    secondme_app_client_id=_read_env("SECONDME_APP_CLIENT_ID"),
    secondme_app_client_secret=_read_env("SECONDME_APP_CLIENT_SECRET"),
    secondme_avatar_api_key=_read_env("SECONDME_AVATAR_API_KEY") or _read_env("SECONDME_API_KEY"),
    secondme_oauth_authorize_url=_read_env(
      "SECONDME_OAUTH_AUTHORIZE_URL",
      "https://go.second-me.cn/oauth/",
    ),
    secondme_oauth_token_url=_read_env(
      "SECONDME_OAUTH_TOKEN_URL",
      "https://api.mindverse.com/gate/lab/api/oauth/token/code",
    ),
    secondme_oauth_redirect_uri=_read_env("SECONDME_OAUTH_REDIRECT_URI"),
    secondme_oauth_scopes=_read_env("SECONDME_OAUTH_SCOPES", "userinfo chat.write avatar.read"),
    secondme_oauth_state_secret=_read_env("SECONDME_OAUTH_STATE_SECRET"),
    secondme_avatar_api_key_name=_read_env("SECONDME_AVATAR_API_KEY_NAME", "Interview Hub"),
    secondme_channel=_read_env("SECONDME_CHANNEL", "web"),
    secondme_ws_origin=_read_env("SECONDME_WS_ORIGIN", "https://second-me.cn"),
    frontend_auth_success_url=_read_env("FRONTEND_AUTH_SUCCESS_URL", "http://localhost:5173/setup"),
    frontend_auth_error_url=_read_env("FRONTEND_AUTH_ERROR_URL", "http://localhost:5173/setup"),
    avatar_interviewer_id=_read_env("SECONDME_INTERVIEWER_ID", "secondme_tech"),
    avatar_interviewer_name=_read_env("SECONDME_INTERVIEWER_NAME", "SecondMe 技术面试官"),
    avatar_interviewer_title=_read_env("SECONDME_INTERVIEWER_TITLE", "固定分身技术面试官"),
    avatar_interviewer_description=_read_env(
      "SECONDME_INTERVIEWER_DESCRIPTION",
      "负责发起技术模拟面试并持续追问项目细节。",
    ),
    avatar_interviewer_avatar_url=_read_env(
      "SECONDME_INTERVIEWER_AVATAR_URL",
      "https://api.dicebear.com/9.x/bottts/svg?seed=secondme-tech",
    ),
    system_interviewer_id=_read_env("SYSTEM_INTERVIEWER_ID", "system_tech"),
    system_interviewer_name=_read_env("SYSTEM_INTERVIEWER_NAME", "系统技术面试官"),
    system_interviewer_title=_read_env("SYSTEM_INTERVIEWER_TITLE", "豆包系统面试官"),
    system_interviewer_description=_read_env(
      "SYSTEM_INTERVIEWER_DESCRIPTION",
      "负责围绕岗位通用能力发起结构化技术追问。",
    ),
    system_interviewer_avatar_url=_read_env(
      "SYSTEM_INTERVIEWER_AVATAR_URL",
      "https://api.dicebear.com/9.x/bottts/svg?seed=system-tech",
    ),
    doubao_api_key=_read_env("DOUBAO_API_KEY"),
    doubao_model=_read_env("DOUBAO_MODEL"),
    doubao_base_url=_read_env("DOUBAO_BASE_URL", "https://operator.las.cn-beijing.volces.com/api/v1"),
    doubao_request_timeout_seconds=float(_read_env("DOUBAO_REQUEST_TIMEOUT_SECONDS", "90")),
    doubao_max_retries=int(_read_env("DOUBAO_MAX_RETRIES", "2")),
    request_timeout_seconds=float(_read_env("SECONDME_REQUEST_TIMEOUT_SECONDS", "30")),
    websocket_reply_timeout_seconds=float(_read_env("SECONDME_WS_REPLY_TIMEOUT_SECONDS", "25")),
    heartbeat_interval_seconds=int(_read_env("SECONDME_HEARTBEAT_SECONDS", "15")),
  )
