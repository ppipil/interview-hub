from __future__ import annotations

from typing import List, Optional

from app.core.config import Settings
from app.core.errors import NotFoundError, ValidationError
from app.models.api import InterviewMode, InterviewRole, Interviewer

SUPPORTED_ROLES: List[InterviewRole] = [
  "frontend",
  "backend",
  "product_manager",
  "operations",
  "data_analyst",
]
SUPPORTED_MODES: List[InterviewMode] = ["guided", "real"]


class InterviewerCatalog:
  def __init__(self, settings: Settings) -> None:
    self._interviewer = Interviewer(
      id=settings.interviewer_id,
      type="avatar",
      name=settings.interviewer_name,
      title=settings.interviewer_title,
      description=settings.interviewer_description,
      avatarUrl=settings.interviewer_avatar_url,
      tags=["SecondMe", "固定分身", "MVP"],
      supportedRoles=SUPPORTED_ROLES,
      supportedModes=SUPPORTED_MODES,
      persona="使用固定 SecondMe 分身作为模拟面试官。",
    )

  def list(self, role: Optional[InterviewRole] = None) -> List[Interviewer]:
    if role and role not in self._interviewer.supportedRoles:
      return []
    return [self._interviewer]

  def get(
    self,
    interviewer_id: str,
    role: InterviewRole,
    mode: InterviewMode,
  ) -> Interviewer:
    if interviewer_id != self._interviewer.id:
      raise NotFoundError("未找到对应的面试官。", field="interviewerId")
    if role not in self._interviewer.supportedRoles:
      raise ValidationError("当前面试官不支持这个岗位。", field="role")
    if mode not in self._interviewer.supportedModes:
      raise ValidationError("当前面试官不支持这个模式。", field="mode")
    return self._interviewer
