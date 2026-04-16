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


@dataclass(frozen=True)
class Settings:
  app_name: str
  app_version: str
  cors_origins: tuple[str, ...]
  cors_origin_regex: str
  secondme_base_url: str
  secondme_api_key: str
  secondme_avatar_share_code: str
  secondme_channel: str
  secondme_ws_origin: str
  interviewer_id: str
  interviewer_name: str
  interviewer_title: str
  interviewer_description: str
  interviewer_avatar_url: str
  request_timeout_seconds: float
  websocket_reply_timeout_seconds: float
  heartbeat_interval_seconds: int

  @property
  def secondme_enabled(self) -> bool:
    return bool(self.secondme_api_key and self.secondme_avatar_share_code)


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
    cors_origin_regex=_read_env(
      "BACKEND_CORS_ORIGIN_REGEX",
      r"https?://(127\.0\.0\.1|localhost)(:\d+)?",
    ),
    secondme_base_url=_read_env("SECONDME_BASE_URL", "https://mindos-prek8s.mindverse.ai/gate/in"),
    secondme_api_key=_read_env("SECONDME_API_KEY"),
    secondme_avatar_share_code=_read_env("SECONDME_AVATAR_SHARE_CODE"),
    secondme_channel=_read_env("SECONDME_CHANNEL", "web"),
    secondme_ws_origin=_read_env("SECONDME_WS_ORIGIN", "https://second-me.cn"),
    interviewer_id=_read_env("SECONDME_INTERVIEWER_ID", "secondme_tech"),
    interviewer_name=_read_env("SECONDME_INTERVIEWER_NAME", "SecondMe 技术面试官"),
    interviewer_title=_read_env("SECONDME_INTERVIEWER_TITLE", "固定分身技术面试官"),
    interviewer_description=_read_env(
      "SECONDME_INTERVIEWER_DESCRIPTION",
      "负责发起技术模拟面试并持续追问项目细节。",
    ),
    interviewer_avatar_url=_read_env(
      "SECONDME_INTERVIEWER_AVATAR_URL",
      "https://api.dicebear.com/9.x/bottts/svg?seed=secondme-tech",
    ),
    request_timeout_seconds=float(_read_env("SECONDME_REQUEST_TIMEOUT_SECONDS", "30")),
    websocket_reply_timeout_seconds=float(_read_env("SECONDME_WS_REPLY_TIMEOUT_SECONDS", "25")),
    heartbeat_interval_seconds=int(_read_env("SECONDME_HEARTBEAT_SECONDS", "15")),
  )
