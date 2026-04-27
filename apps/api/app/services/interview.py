from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from app.core.config import Settings
from app.core.errors import ConflictError, ValidationError
from app.models.api import (
  ConversationMessage,
  CreateSessionRequest,
  CreateSessionResponse,
  InterviewFeedback,
  InterviewRole,
  InterviewStageKey,
  Interviewer,
  InterviewerProvider,
  SendMessageRequest,
  SendMessageResponse,
  Session,
)
from app.models.persistence import FormalQuestionBankEntry, FormalQuestionUsageEntry
from app.repositories.in_memory import InMemorySessionRepository
from app.repositories.persistence import PersistenceRepository
from app.services.catalog import InterviewerCatalog
from app.services.formal_question_bank import (
  FORMAL_QUESTION_STAGE_LABELS,
  build_seed_formal_questions,
  get_stage_key_for_round,
)
from app.services.interview_provider import InterviewProvider, InterviewProviderRegistry


class InterviewService:
  def __init__(
    self,
    settings: Settings,
    repository: InMemorySessionRepository,
    persistence: PersistenceRepository,
    catalog: InterviewerCatalog,
    providers: InterviewProviderRegistry,
  ) -> None:
    self._settings = settings
    self._repository = repository
    self._persistence = persistence
    self._catalog = catalog
    self._providers = providers

  def sync_catalog(self) -> None:
    self._persistence.sync_interviewers(self._catalog.list())
    self._seed_formal_questions()

  def list_interviewers(self, role: InterviewRole = None) -> List[Interviewer]:
    interviewers = self._catalog.list(role, profiles=self._persistence.list_interviewer_profiles())
    self._persistence.sync_interviewers(interviewers)
    return interviewers

  async def create_session(self, payload: CreateSessionRequest) -> CreateSessionResponse:
    entry = self._catalog.get_entry(
      payload.interviewerId,
      payload.role,
      payload.mode,
      profiles=self._persistence.list_interviewer_profiles(),
    )
    interviewer = entry.interviewer
    total_rounds = self._validate_total_rounds(payload.totalRounds)
    local_session_id = str(uuid4())
    selected_question = self._select_formal_question(
      interviewer_id=interviewer.id,
      role=payload.role,
      round_number=1,
      total_rounds=total_rounds,
      session_id=None,
    )

    session = Session(
      id=local_session_id,
      role=payload.role,
      mode=payload.mode,
      interviewerId=interviewer.id,
      status="in_progress",
      currentRound=1,
      totalRounds=total_rounds,
      startedAt=self._now(),
      finishedAt=None,
    )
    first_question = ConversationMessage(
      id=str(uuid4()),
      role="assistant",
      content=selected_question.question.question,
      round=1,
      createdAt=self._now(),
    )
    self._repository.create(session, None, None, first_question)
    self._persistence.save_session(session)
    self._persistence.append_message(session.id, first_question)
    self._persist_formal_question_usage(
      session=session,
      message=first_question,
      selected_question=selected_question,
    )

    return CreateSessionResponse(
      session=session,
      interviewer=interviewer,
      firstQuestion=first_question,
    )

  async def send_message(
    self,
    session_id: str,
    payload: SendMessageRequest,
  ) -> SendMessageResponse:
    content = payload.content.strip()
    if not content:
      raise ValidationError("回答内容不能为空。", field="content")

    session = self._repository.get_session(session_id)
    interviewer = self._catalog.get(
      session.interviewerId,
      session.role,
      session.mode,
      profiles=self._persistence.list_interviewer_profiles(),
    )

    if session.status != "in_progress":
      raise ConflictError("当前 Session 已结束，无法继续发送消息。")

    user_message = ConversationMessage(
      id=payload.clientMessageId or str(uuid4()),
      role="user",
      content=content,
      round=session.currentRound,
      createdAt=self._now(),
    )
    self._repository.append_message(session.id, user_message)
    self._persistence.append_message(session.id, user_message)

    if session.currentRound >= session.totalRounds:
      completed_session = self._clone_session(
        session,
        status="completed",
        finishedAt=self._now(),
      )
      self._repository.save_session(completed_session)
      self._persistence.save_session(completed_session)
      return SendMessageResponse(
        session=completed_session,
        userMessage=user_message,
        assistantMessage=None,
        shouldFetchFeedback=True,
      )

    next_round = session.currentRound + 1
    selected_question = self._select_formal_question(
      interviewer_id=interviewer.id,
      role=session.role,
      round_number=next_round,
      total_rounds=session.totalRounds,
      session_id=session.id,
    )

    assistant_message = ConversationMessage(
      id=str(uuid4()),
      role="assistant",
      content=selected_question.question.question,
      round=next_round,
      createdAt=self._now(),
    )
    self._repository.append_message(session.id, assistant_message)
    self._persistence.append_message(session.id, assistant_message)

    updated_session = self._clone_session(session, currentRound=next_round)
    self._repository.save_session(updated_session)
    self._persistence.save_session(updated_session)
    self._persist_formal_question_usage(
      session=updated_session,
      message=assistant_message,
      selected_question=selected_question,
    )

    return SendMessageResponse(
      session=updated_session,
      userMessage=user_message,
      assistantMessage=assistant_message,
      shouldFetchFeedback=False,
    )

  async def get_feedback(self, session_id: str) -> InterviewFeedback:
    session = self._repository.get_session(session_id)
    if session.status != "completed":
      raise ConflictError("当前 Session 尚未完成，暂时无法获取反馈。")

    existing_feedback = self._repository.get_feedback(session_id) or self._persistence.get_feedback(session_id)
    if existing_feedback:
      self._repository.save_feedback(existing_feedback)
      return existing_feedback

    messages = self._repository.list_messages(session_id)
    interviewer = self._catalog.get(
      session.interviewerId,
      session.role,
      session.mode,
      profiles=self._persistence.list_interviewer_profiles(),
    )
    provider = self._providers.get(interviewer.provider)
    runtime, channel = await self._ensure_feedback_runtime(
      interviewer=interviewer,
      session=session,
      provider=provider,
    )

    feedback = await provider.generate_feedback(
      session=session,
      messages=messages,
      runtime=runtime,
      channel=channel,
    )
    self._repository.save_feedback(feedback)
    self._persistence.save_feedback(feedback)
    return feedback

  async def close(self) -> None:
    await self._repository.close_all()

  def _clone_session(self, session: Session, **changes: object) -> Session:
    payload = session.model_dump()
    payload.update(changes)
    return Session(**payload)

  def _validate_total_rounds(self, total_rounds: int = None) -> int:
    if total_rounds is None:
      return 3

    try:
      normalized = int(total_rounds)
    except (TypeError, ValueError) as exc:
      raise ValidationError("轮次数量必须是数字。", field="totalRounds") from exc

    if normalized < 1 or normalized > 10:
      raise ValidationError("当前仅支持 1 到 10 轮面试。", field="totalRounds")
    return normalized

  def _now(self) -> str:
    return datetime.now(timezone.utc).isoformat()

  def _seed_formal_questions(self) -> None:
    if self._persistence.list_formal_questions(enabled_only=False):
      return
    self._persistence.seed_formal_questions(build_seed_formal_questions(self._settings.avatar_interviewer_id))

  async def _ensure_feedback_runtime(
    self,
    interviewer: Interviewer,
    session: Session,
    provider: InterviewProvider,
  ):
    runtime = self._repository.get_optional_runtime(session.id)
    channel = self._repository.get_optional_channel(session.id)
    if runtime is not None:
      return runtime, channel

    bootstrap = await provider.bootstrap(
      interviewer=interviewer,
      role=session.role,
      mode=session.mode,
      total_rounds=session.totalRounds,
    )
    self._repository.save_runtime(session.id, bootstrap.runtime)
    if bootstrap.channel is not None:
      self._repository.save_channel(session.id, bootstrap.channel)
    return bootstrap.runtime, bootstrap.channel

  def _select_formal_question(
    self,
    *,
    interviewer_id: str,
    role: InterviewRole,
    round_number: int,
    total_rounds: int,
    session_id: Optional[str],
  ) -> "SelectedFormalQuestion":
    stage_key = get_stage_key_for_round(round_number, total_rounds)
    used_question_ids = {
      item.question_id
      for item in self._persistence.list_formal_question_usage(session_id)
    } if session_id else set()

    if stage_key not in {"intro", "closing"}:
      owned_candidates = self._persistence.list_formal_questions(
        scope_type="interviewer",
        interviewer_id=interviewer_id,
        role=role,
        stage_key=stage_key,
      )
      owned_question = next((item for item in owned_candidates if item.id not in used_question_ids), None)
      if owned_question is not None:
        return SelectedFormalQuestion(question=owned_question, source_scope="interviewer", stage_key=stage_key)

    global_candidates = self._persistence.list_formal_questions(
      scope_type="global",
      role=role,
      stage_key=stage_key,
    )
    global_question = next((item for item in global_candidates if item.id not in used_question_ids), None)
    if global_question is not None:
      return SelectedFormalQuestion(question=global_question, source_scope="global", stage_key=stage_key)

    stage_label = FORMAL_QUESTION_STAGE_LABELS[stage_key]
    raise ValidationError(
      f"当前题库还没有覆盖第 {round_number} 轮需要的“{stage_label}”题目，请先补充该岗位的面试官题库或通用题库。",
      field="questionBank",
    )

  def _persist_formal_question_usage(
    self,
    *,
    session: Session,
    message: ConversationMessage,
    selected_question: "SelectedFormalQuestion",
  ) -> None:
    self._persistence.save_formal_question_usage(
      FormalQuestionUsageEntry(
        message_id=message.id,
        session_id=session.id,
        question_id=selected_question.question.id,
        interviewer_id=session.interviewerId,
        role=session.role,
        round_number=message.round,
        stage_key=selected_question.stage_key,
        source_scope=selected_question.source_scope,
        used_at=message.createdAt,
      )
    )


@dataclass(frozen=True)
class SelectedFormalQuestion:
  question: FormalQuestionBankEntry
  source_scope: str
  stage_key: InterviewStageKey
