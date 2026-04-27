from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import List, Optional

from app.core.config import Settings
from app.core.errors import ConfigError, NotFoundError, ValidationError
from app.models.api import (
  AdminQuestionBankQuestion,
  AdminInterviewer,
  GlobalQuestionBankResponse,
  InterviewMode,
  InterviewRole,
  Interviewer,
  InterviewerProvider,
  InterviewerType,
  UpsertAdminInterviewerRequest,
  UpsertGlobalQuestionBankRequest,
)
from app.models.persistence import FormalQuestionBankEntry, FormalQuestionBankWrite, InterviewerProfileEntry
from app.repositories.persistence import PersistenceRepository
from app.services.catalog import InterviewerCatalog, SUPPORTED_MODES, SUPPORTED_ROLES
from app.services.formal_question_bank import build_seed_formal_questions, normalize_question_tags, validate_stage_key

INTERVIEWER_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


class AdminInterviewerService:
  def __init__(
    self,
    settings: Settings,
    catalog: InterviewerCatalog,
    persistence: PersistenceRepository,
  ) -> None:
    self._settings = settings
    self._catalog = catalog
    self._persistence = persistence

  def list_interviewers(self) -> List[AdminInterviewer]:
    self._ensure_default_question_banks()
    profiles = self._persistence.list_interviewer_profiles(enabled_only=False)
    base_interviewers = self._catalog.list()
    base_by_id = {item.id: item for item in base_interviewers}
    profile_by_id = {item.interviewer_id: item for item in profiles}
    interviewer_questions = self._group_formal_questions_by_interviewer()
    ordered_ids = [item.id for item in base_interviewers]
    ordered_ids.extend(item.interviewer_id for item in profiles if item.interviewer_id not in base_by_id)

    return [
      self._build_admin_interviewer(
        interviewer_id=interviewer_id,
        base=base_by_id.get(interviewer_id),
        profile=profile_by_id.get(interviewer_id),
        owned_questions=interviewer_questions.get(interviewer_id, []),
      )
      for interviewer_id in ordered_ids
    ]

  def upsert_interviewer(self, payload: UpsertAdminInterviewerRequest) -> AdminInterviewer:
    self._ensure_database_enabled()
    self._ensure_default_question_banks()
    self._validate_payload(payload)

    existing_profile = self._find_profile(payload.id)
    base = self._find_base_interviewer(payload.id)
    now = self._now()
    provider = payload.provider or self._default_provider_for_type(payload.type)
    avatar_api_key = self._resolve_next_avatar_api_key(payload.avatarApiKey, existing_profile)
    profile = InterviewerProfileEntry(
      interviewer_id=payload.id.strip(),
      type=payload.type,
      provider=provider,
      name=payload.name.strip(),
      title=payload.title.strip(),
      description=payload.description.strip(),
      avatar_url=(payload.avatarUrl or self._default_avatar_url(payload.id)).strip(),
      tags=self._normalize_strings(payload.tags),
      supported_roles=payload.supportedRoles,
      supported_modes=payload.supportedModes,
      persona=self._normalize_optional(payload.persona),
      prompt_strategy=self._normalize_optional(payload.promptStrategy) or self._default_prompt_strategy(payload.type),
      skill_prompt=self._normalize_optional(payload.skillPrompt),
      interview_flow=self._normalize_optional(payload.interviewFlow),
      avatar_api_key=avatar_api_key,
      enabled=payload.enabled,
      created_at=existing_profile.created_at if existing_profile else now,
      updated_at=now,
    )
    self._persistence.upsert_interviewer_profile(profile)
    if payload.ownedQuestions is not None:
      self._persistence.replace_interviewer_question_bank(
        profile.interviewer_id,
        self._normalize_question_bank(
          payload.ownedQuestions,
          scope_type="interviewer",
          interviewer_id=profile.interviewer_id,
          supported_roles=payload.supportedRoles,
        ),
      )

    return self._build_admin_interviewer(
      interviewer_id=profile.interviewer_id,
      base=base,
      profile=profile,
      owned_questions=self._persistence.list_formal_questions(
        scope_type="interviewer",
        interviewer_id=profile.interviewer_id,
        enabled_only=False,
      ),
    )

  def get_global_question_bank(self, role: InterviewRole) -> GlobalQuestionBankResponse:
    self._ensure_database_enabled()
    self._ensure_default_question_banks()
    return GlobalQuestionBankResponse(
      role=role,
      questions=[
        self._to_admin_question(item)
        for item in self._persistence.list_formal_questions(
          scope_type="global",
          role=role,
          enabled_only=False,
        )
      ],
    )

  def update_global_question_bank(self, payload: UpsertGlobalQuestionBankRequest) -> GlobalQuestionBankResponse:
    self._ensure_database_enabled()
    self._ensure_default_question_banks()
    normalized_questions = self._normalize_question_bank(
      payload.questions,
      scope_type="global",
      interviewer_id=None,
      supported_roles=[payload.role],
      forced_role=payload.role,
    )
    self._persistence.replace_global_question_bank(payload.role, normalized_questions)
    return self.get_global_question_bank(payload.role)

  def delete_interviewer(self, interviewer_id: str) -> None:
    self._ensure_database_enabled()
    deleted = self._persistence.delete_interviewer_profile(interviewer_id)
    if not deleted:
      raise NotFoundError("没有找到可删除的面试官配置。", field="interviewerId")

  def _build_admin_interviewer(
    self,
    *,
    interviewer_id: str,
    base: Optional[Interviewer],
    profile: Optional[InterviewerProfileEntry],
    owned_questions: Optional[List[FormalQuestionBankEntry]] = None,
  ) -> AdminInterviewer:
    interviewer_type = self._first_present(profile.type if profile else None, base.type if base else None, "avatar")
    provider = self._first_present(
      profile.provider if profile else None,
      base.provider if base else None,
      self._default_provider_for_type(interviewer_type),
    )
    avatar_api_key = profile.avatar_api_key if profile else None
    if not avatar_api_key:
      secret = self._persistence.get_interviewer_secret(interviewer_id)
      avatar_api_key = secret.avatar_api_key if secret else None

    return AdminInterviewer(
      id=interviewer_id,
      type=interviewer_type,
      provider=provider,
      name=self._first_present(profile.name if profile else None, base.name if base else None, interviewer_id),
      title=self._first_present(profile.title if profile else None, base.title if base else None, "自定义面试官"),
      description=self._first_present(
        profile.description if profile else None,
        base.description if base else None,
        "由 Interview Hub 管理台创建的面试官。",
      ),
      avatarUrl=self._first_present(
        profile.avatar_url if profile else None,
        base.avatarUrl if base else None,
        self._default_avatar_url(interviewer_id),
      ),
      tags=self._first_list(profile.tags if profile else None, base.tags if base else None),
      supportedRoles=self._first_list(profile.supported_roles if profile else None, base.supportedRoles if base else None)
      or SUPPORTED_ROLES,
      supportedModes=self._first_list(profile.supported_modes if profile else None, base.supportedModes if base else None)
      or SUPPORTED_MODES,
      persona=self._first_present(profile.persona if profile else None, base.persona if base else None, None),
      promptStrategy=self._first_present(
        profile.prompt_strategy if profile else None,
        base.promptStrategy if base else None,
        self._default_prompt_strategy(interviewer_type),
      ),
      skillPrompt=self._first_present(profile.skill_prompt if profile else None, base.skillPrompt if base else None, None),
      interviewFlow=self._first_present(
        profile.interview_flow if profile else None,
        base.interviewFlow if base else None,
        None,
      ),
      enabled=profile.enabled if profile else True,
      profileExists=profile is not None,
      hasAvatarApiKey=bool(avatar_api_key),
      avatarApiKey=avatar_api_key,
      avatarApiKeyMasked=self._mask_secret(avatar_api_key),
      updatedAt=profile.updated_at if profile else None,
      ownedQuestions=[self._to_admin_question(item) for item in (owned_questions or [])],
    )

  def _find_profile(self, interviewer_id: str) -> Optional[InterviewerProfileEntry]:
    return next(
      (item for item in self._persistence.list_interviewer_profiles(enabled_only=False) if item.interviewer_id == interviewer_id),
      None,
    )

  def _find_base_interviewer(self, interviewer_id: str) -> Optional[Interviewer]:
    return next((item for item in self._catalog.list() if item.id == interviewer_id), None)

  def _validate_payload(self, payload: UpsertAdminInterviewerRequest) -> None:
    if not INTERVIEWER_ID_PATTERN.match(payload.id.strip()):
      raise ValidationError("面试官 ID 只能包含英文字母、数字、下划线和连字符。", field="id")
    if not payload.supportedRoles:
      raise ValidationError("至少选择一个支持岗位。", field="supportedRoles")
    if not payload.supportedModes:
      raise ValidationError("至少选择一个支持模式。", field="supportedModes")
    provider = payload.provider or self._default_provider_for_type(payload.type)
    if payload.type == "system" and provider != "doubao":
      raise ValidationError("系统面试官当前仅支持 doubao provider。", field="provider")
    if payload.type == "avatar" and provider == "doubao":
      raise ValidationError("AI 分身面试官不能使用 doubao provider。", field="provider")

  def _group_formal_questions_by_interviewer(self) -> dict[str, List[FormalQuestionBankEntry]]:
    grouped: dict[str, List[FormalQuestionBankEntry]] = {}
    for question in self._persistence.list_formal_questions(scope_type="interviewer", enabled_only=False):
      if not question.interviewer_id:
        continue
      grouped.setdefault(question.interviewer_id, []).append(question)
    return grouped

  def _to_admin_question(self, question: FormalQuestionBankEntry) -> AdminQuestionBankQuestion:
    return AdminQuestionBankQuestion(
      id=question.id,
      scopeType=question.scope_type,
      interviewerId=question.interviewer_id,
      role=question.role,
      stageKey=question.stage_key,
      question=question.question,
      referenceAnswer=question.reference_answer,
      tags=question.tags,
      enabled=question.enabled,
      sortOrder=question.sort_order,
    )

  def _normalize_question_bank(
    self,
    questions,
    *,
    scope_type: str,
    interviewer_id: Optional[str],
    supported_roles: List[InterviewRole],
    forced_role: Optional[InterviewRole] = None,
  ) -> List[FormalQuestionBankWrite]:
    normalized: List[FormalQuestionBankWrite] = []
    for index, item in enumerate(questions):
      role = forced_role or item.role
      if role not in supported_roles:
        raise ValidationError("题库岗位必须属于当前面试官支持岗位。", field=f"ownedQuestions[{index}].role")
      question_text = item.question.strip()
      if not question_text:
        raise ValidationError("题目内容不能为空。", field=f"ownedQuestions[{index}].question")
      normalized.append(
        FormalQuestionBankWrite(
          scope_type=scope_type,  # type: ignore[arg-type]
          interviewer_id=interviewer_id,
          role=role,
          stage_key=validate_stage_key(item.stageKey),
          question=question_text,
          reference_answer=self._normalize_optional(item.referenceAnswer),
          tags=normalize_question_tags(item.tags),
          enabled=item.enabled,
          sort_order=item.sortOrder if item.sortOrder is not None else (index + 1) * 10,
        )
      )
    return normalized

  def _ensure_default_question_banks(self) -> None:
    if not self._settings.database_enabled:
      return
    if self._persistence.list_formal_questions(enabled_only=False):
      return
    self._persistence.seed_formal_questions(build_seed_formal_questions(self._settings.avatar_interviewer_id))

  def _ensure_database_enabled(self) -> None:
    if not self._settings.database_enabled:
      raise ConfigError("隐藏管理台需要先配置 DATABASE_URL，否则面试官资料无法保存。")

  def _default_provider_for_type(self, interviewer_type: InterviewerType) -> InterviewerProvider:
    if interviewer_type == "system":
      return "doubao"
    return "secondme_visitor" if self._settings.secondme_visitor_enabled else "secondme_legacy"

  def _default_prompt_strategy(self, interviewer_type: InterviewerType) -> str:
    return "system_structured" if interviewer_type == "system" else "avatar_skill"

  def _default_avatar_url(self, interviewer_id: str) -> str:
    return f"https://api.dicebear.com/9.x/bottts/svg?seed={interviewer_id}"

  def _resolve_next_avatar_api_key(
    self,
    avatar_api_key: Optional[str],
    existing_profile: Optional[InterviewerProfileEntry],
  ) -> Optional[str]:
    normalized = self._normalize_optional(avatar_api_key)
    if normalized:
      return normalized
    return existing_profile.avatar_api_key if existing_profile else None

  def _mask_secret(self, secret: Optional[str]) -> Optional[str]:
    if not secret:
      return None
    if len(secret) <= 10:
      return "已保存"
    return f"{secret[:5]}...{secret[-4:]}"

  def _normalize_strings(self, values: List[str]) -> List[str]:
    return [item.strip() for item in values if item.strip()]

  def _normalize_optional(self, value: Optional[str]) -> Optional[str]:
    if value is None:
      return None
    normalized = value.strip()
    return normalized or None

  def _first_present(self, *values):
    for value in values:
      if isinstance(value, str):
        if value.strip():
          return value.strip()
      elif value is not None:
        return value
    return None

  def _first_list(self, *values) -> List[str]:
    for value in values:
      if value:
        return list(value)
    return []

  def _now(self) -> str:
    return datetime.now(timezone.utc).isoformat()
