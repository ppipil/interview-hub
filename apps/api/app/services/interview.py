from __future__ import annotations

from datetime import datetime, timezone
from typing import List
from uuid import uuid4

from app.core.config import Settings
from app.core.errors import ConflictError, ValidationError
from app.models.api import (
  ConversationMessage,
  CreateSessionRequest,
  CreateSessionResponse,
  InterviewFeedback,
  InterviewRole,
  Interviewer,
  SendMessageRequest,
  SendMessageResponse,
  Session,
)
from app.repositories.in_memory import InMemorySessionRepository
from app.repositories.persistence import PersistenceRepository
from app.services.catalog import InterviewerCatalog
from app.services.interview_provider import InterviewProviderRegistry


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
    provider = self._providers.get(interviewer.provider)
    total_rounds = self._validate_total_rounds(payload.totalRounds)
    local_session_id = str(uuid4())

    bootstrap = await provider.bootstrap(
      interviewer=interviewer,
      role=payload.role,
      mode=payload.mode,
      total_rounds=total_rounds,
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
      content=bootstrap.first_question_text,
      round=1,
      createdAt=self._now(),
    )
    self._repository.create(session, bootstrap.runtime, bootstrap.channel, first_question)
    self._persistence.save_session(session)
    self._persistence.append_message(session.id, first_question)
    self._persist_question(interviewer, session, first_question)

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
    runtime = self._repository.get_runtime(session_id)
    channel = self._repository.get_optional_channel(session_id)
    interviewer = self._catalog.get(
      session.interviewerId,
      session.role,
      session.mode,
      profiles=self._persistence.list_interviewer_profiles(),
    )
    provider = self._providers.get(interviewer.provider)

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

    assistant_reply = await provider.follow_up(
      interviewer=interviewer,
      session=session,
      runtime=runtime,
      channel=channel,
      answer=content,
    )

    next_round = session.currentRound + 1
    assistant_message = ConversationMessage(
      id=str(uuid4()),
      role="assistant",
      content=assistant_reply,
      round=next_round,
      createdAt=self._now(),
    )
    self._repository.append_message(session.id, assistant_message)
    self._persistence.append_message(session.id, assistant_message)

    updated_session = self._clone_session(session, currentRound=next_round)
    self._repository.save_session(updated_session)
    self._persistence.save_session(updated_session)
    self._persist_question(interviewer, updated_session, assistant_message)

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
    runtime = self._repository.get_runtime(session_id)
    channel = self._repository.get_optional_channel(session_id)
    interviewer = self._catalog.get(
      session.interviewerId,
      session.role,
      session.mode,
      profiles=self._persistence.list_interviewer_profiles(),
    )
    provider = self._providers.get(interviewer.provider)

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

  def _persist_question(
    self,
    interviewer: Interviewer,
    session: Session,
    message: ConversationMessage,
  ) -> None:
    if message.role != "assistant" or not message.content.strip():
      return

    self._persistence.add_question(
      role=session.role,
      mode=session.mode,
      interviewer_type=interviewer.type,
      provider=interviewer.provider,
      prompt_strategy=interviewer.promptStrategy or "default",
      question=message.content,
      source_session_id=session.id,
      created_at=message.createdAt,
    )

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
