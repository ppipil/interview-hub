from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.core.config import Settings
from app.core.errors import NotFoundError, ValidationError
from app.models.api import InterviewMode, InterviewRole, Interviewer, InterviewerProvider
from app.models.persistence import InterviewerProfileEntry

SUPPORTED_ROLES: List[InterviewRole] = [
  "frontend",
  "backend",
  "product_manager",
  "operations",
  "data_analyst",
]
SUPPORTED_MODES: List[InterviewMode] = ["guided", "real"]


@dataclass(frozen=True)
class CatalogEntry:
  interviewer: Interviewer
  config_keys: tuple[str, ...]


class InterviewerCatalog:
  def __init__(self, settings: Settings) -> None:
    avatar_provider = "secondme_visitor" if settings.secondme_visitor_enabled else "secondme_legacy"
    self._default_avatar_provider = avatar_provider
    avatar_config_keys = (
      ("SECONDME_APP_CLIENT_ID", "SECONDME_APP_CLIENT_SECRET", "SECONDME_AVATAR_API_KEY")
      if avatar_provider == "secondme_visitor"
      else ("SECONDME_API_KEY", "SECONDME_AVATAR_SHARE_CODE")
    )
    self._entries = [
      CatalogEntry(
        interviewer=Interviewer(
          id=settings.system_interviewer_id,
          type="system",
          provider="doubao",
          name=settings.system_interviewer_name,
          title=settings.system_interviewer_title,
          description=settings.system_interviewer_description,
          avatarUrl=settings.system_interviewer_avatar_url,
          tags=["System", "Doubao", "结构化"],
          supportedRoles=SUPPORTED_ROLES,
          supportedModes=SUPPORTED_MODES,
          persona="由应用内 Prompt 控制问题与反馈风格的系统面试官。",
          promptStrategy="system_structured",
        ),
        config_keys=("DOUBAO_API_KEY", "DOUBAO_MODEL", "DOUBAO_BASE_URL"),
      ),
      CatalogEntry(
        interviewer=Interviewer(
          id=settings.avatar_interviewer_id,
          type="avatar",
          provider=avatar_provider,
          name=settings.avatar_interviewer_name,
          title=settings.avatar_interviewer_title,
          description=settings.avatar_interviewer_description,
          avatarUrl=settings.avatar_interviewer_avatar_url,
          tags=["SecondMe", "分身", "MVP"],
          supportedRoles=SUPPORTED_ROLES,
          supportedModes=SUPPORTED_MODES,
          persona="优先遵循分身自身的 skill 文档与人设进行模拟面试。",
          promptStrategy="avatar_skill",
        ),
        config_keys=avatar_config_keys,
      ),
    ]

  def list(
    self,
    role: Optional[InterviewRole] = None,
    profiles: Optional[List[InterviewerProfileEntry]] = None,
  ) -> List[Interviewer]:
    active_profiles = profiles or []
    base_interviewers = self._apply_profiles([entry.interviewer for entry in self._entries], active_profiles)
    base_ids = {item.interviewer.id for item in self._entries}
    custom_interviewers = [
      interviewer
      for profile in active_profiles
      if profile.interviewer_id not in base_ids
      for interviewer in [self._profile_to_interviewer(profile)]
      if interviewer is not None
    ]
    interviewers = [*base_interviewers, *custom_interviewers]
    if not role:
      return interviewers
    return [item for item in interviewers if role in item.supportedRoles]

  def get_entry(
    self,
    interviewer_id: str,
    role: InterviewRole,
    mode: InterviewMode,
    profiles: Optional[List[InterviewerProfileEntry]] = None,
  ) -> CatalogEntry:
    active_profiles = profiles or []
    entries = [
      CatalogEntry(interviewer=interviewer, config_keys=entry.config_keys)
      for entry in self._entries
      for interviewer in [self._apply_profile(entry.interviewer, active_profiles)]
    ]
    base_ids = {entry.interviewer.id for entry in self._entries}
    entries.extend(
      CatalogEntry(interviewer=interviewer, config_keys=self._config_keys_for_provider(interviewer.provider))
      for profile in active_profiles
      if profile.interviewer_id not in base_ids
      for interviewer in [self._profile_to_interviewer(profile)]
      if interviewer is not None
    )
    entry = next((item for item in entries if item.interviewer.id == interviewer_id), None)
    if not entry:
      raise NotFoundError("未找到对应的面试官。", field="interviewerId")
    interviewer = entry.interviewer
    if role not in interviewer.supportedRoles:
      raise ValidationError("当前面试官不支持这个岗位。", field="role")
    if mode not in interviewer.supportedModes:
      raise ValidationError("当前面试官不支持这个模式。", field="mode")
    return entry

  def get(
    self,
    interviewer_id: str,
    role: InterviewRole,
    mode: InterviewMode,
    profiles: Optional[List[InterviewerProfileEntry]] = None,
  ) -> Interviewer:
    return self.get_entry(interviewer_id, role, mode, profiles).interviewer

  def _apply_profiles(
    self,
    interviewers: List[Interviewer],
    profiles: List[InterviewerProfileEntry],
  ) -> List[Interviewer]:
    return [self._apply_profile(interviewer, profiles) for interviewer in interviewers]

  def _apply_profile(self, interviewer: Interviewer, profiles: List[InterviewerProfileEntry]) -> Interviewer:
    profile = next((item for item in profiles if item.interviewer_id == interviewer.id), None)
    if not profile:
      return interviewer

    payload = interviewer.model_dump()
    if profile.type:
      payload["type"] = profile.type
    if profile.provider:
      payload["provider"] = profile.provider
    if profile.name and profile.name.strip():
      payload["name"] = profile.name.strip()
    if profile.title and profile.title.strip():
      payload["title"] = profile.title.strip()
    if profile.description and profile.description.strip():
      payload["description"] = profile.description.strip()
    if profile.avatar_url and profile.avatar_url.strip():
      payload["avatarUrl"] = profile.avatar_url.strip()
    if profile.tags:
      payload["tags"] = profile.tags
    if profile.supported_roles:
      payload["supportedRoles"] = profile.supported_roles
    if profile.supported_modes:
      payload["supportedModes"] = profile.supported_modes
    if profile.persona and profile.persona.strip():
      payload["persona"] = profile.persona.strip()
    if profile.prompt_strategy and profile.prompt_strategy.strip():
      payload["promptStrategy"] = profile.prompt_strategy.strip()
    if profile.skill_prompt and profile.skill_prompt.strip():
      payload["skillPrompt"] = profile.skill_prompt.strip()
    if profile.interview_flow and profile.interview_flow.strip():
      payload["interviewFlow"] = profile.interview_flow.strip()
    return Interviewer(**payload)

  def _profile_to_interviewer(self, profile: InterviewerProfileEntry) -> Optional[Interviewer]:
    if not profile.enabled or not profile.type or not profile.name or not profile.title or not profile.description:
      return None

    provider = profile.provider or self._default_provider_for_type(profile.type)
    return Interviewer(
      id=profile.interviewer_id,
      type=profile.type,
      provider=provider,
      name=profile.name.strip(),
      title=profile.title.strip(),
      description=profile.description.strip(),
      avatarUrl=(profile.avatar_url or f"https://api.dicebear.com/9.x/bottts/svg?seed={profile.interviewer_id}").strip(),
      tags=profile.tags or [],
      supportedRoles=profile.supported_roles or SUPPORTED_ROLES,
      supportedModes=profile.supported_modes or SUPPORTED_MODES,
      persona=profile.persona,
      promptStrategy=profile.prompt_strategy or ("system_structured" if profile.type == "system" else "avatar_skill"),
      skillPrompt=profile.skill_prompt,
      interviewFlow=profile.interview_flow,
    )

  def _default_provider_for_type(self, interviewer_type: str) -> InterviewerProvider:
    return "doubao" if interviewer_type == "system" else self._default_avatar_provider

  def _config_keys_for_provider(self, provider: InterviewerProvider) -> tuple[str, ...]:
    if provider == "doubao":
      return ("DOUBAO_API_KEY", "DOUBAO_MODEL", "DOUBAO_BASE_URL")
    if provider == "secondme_visitor":
      return ("SECONDME_APP_CLIENT_ID", "SECONDME_APP_CLIENT_SECRET", "SECONDME_AVATAR_API_KEY")
    return ("SECONDME_API_KEY", "SECONDME_AVATAR_SHARE_CODE")
