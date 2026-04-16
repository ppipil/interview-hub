from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Dict, List
from uuid import uuid4

from app.core.config import Settings
from app.core.errors import ConfigError, ConflictError, UpstreamServiceError, ValidationError
from app.models.api import (
  ConversationMessage,
  CreateSessionRequest,
  CreateSessionResponse,
  InterviewFeedback,
  InterviewMode,
  InterviewRole,
  Interviewer,
  SendMessageRequest,
  SendMessageResponse,
  Session,
)
from app.models.runtime import SessionRuntime
from app.repositories.in_memory import InMemorySessionRepository
from app.services.catalog import InterviewerCatalog
from app.services.feedback import FeedbackService
from app.services.realtime import SecondMeRealtimeChannel
from app.services.secondme_client import SecondMeClient

ROLE_LABELS: Dict[InterviewRole, str] = {
  "frontend": "前端工程师",
  "backend": "后端工程师",
  "product_manager": "产品经理",
  "operations": "运营",
  "data_analyst": "数据分析",
}

MODE_LABELS: Dict[InterviewMode, str] = {
  "guided": "带飞模式",
  "real": "真实模式",
}

logger = logging.getLogger(__name__)


class InterviewService:
  def __init__(
    self,
    settings: Settings,
    repository: InMemorySessionRepository,
    catalog: InterviewerCatalog,
    secondme_client: SecondMeClient,
    feedback_service: FeedbackService,
  ) -> None:
    self._settings = settings
    self._repository = repository
    self._catalog = catalog
    self._secondme_client = secondme_client
    self._feedback_service = feedback_service

  def list_interviewers(self, role: InterviewRole = None) -> List[Interviewer]:
    return self._catalog.list(role)

  async def create_session(self, payload: CreateSessionRequest) -> CreateSessionResponse:
    self._ensure_secondme_configured()
    interviewer = self._catalog.get(payload.interviewerId, payload.role, payload.mode)
    total_rounds = self._clamp_rounds(payload.totalRounds)
    local_session_id = str(uuid4())
    visitor_id = f"{self._settings.secondme_channel}_{uuid4()}"

    auth = await self._secondme_client.authenticate(
      api_key=self._settings.secondme_api_key,
      visitor_id=visitor_id,
      visitor_name="Interview Hub User",
    )
    chat = await self._secondme_client.initialize_chat(
      visitor_token=auth.visitor_token,
      visitor_id=auth.visitor_id,
      share_code=self._settings.secondme_avatar_share_code,
    )
    socket = await self._secondme_client.create_websocket(
      visitor_token=auth.visitor_token,
      visitor_id=auth.visitor_id,
      visitor_user_id=auth.visitor_user_id,
    )

    channel = SecondMeRealtimeChannel(
      ws_id=socket.ws_id,
      visitor_user_id=auth.visitor_user_id,
      origin=self._settings.secondme_ws_origin,
      heartbeat_interval_seconds=self._settings.heartbeat_interval_seconds,
      reply_timeout_seconds=self._settings.websocket_reply_timeout_seconds,
    )
    await channel.connect(socket.address)

    try:
      secondme_session_id = await self._secondme_client.create_session(
        visitor_token=auth.visitor_token,
        visitor_id=auth.visitor_id,
        visitor_mind_id=auth.visitor_mind_id,
        owner_user_id=auth.owner_user_id,
      )
      avatar_id = await self._secondme_client.get_avatar_id(
        visitor_token=auth.visitor_token,
        share_code=self._settings.secondme_avatar_share_code,
      )
      await self._secondme_client.bind_session(
        visitor_token=auth.visitor_token,
        visitor_id=auth.visitor_id,
        avatar_id=avatar_id,
        session_id=secondme_session_id,
      )
      first_question_text = await self._bootstrap_first_question(
        payload.role,
        payload.mode,
        total_rounds,
        auth.visitor_token,
        auth.visitor_id,
        secondme_session_id,
        auth.visitor_user_id,
        chat.mind_id,
        socket.ws_id,
        channel,
      )
    except Exception:
      await channel.close()
      raise

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
      content=first_question_text,
      round=1,
      createdAt=self._now(),
    )
    runtime = SessionRuntime(
      secondme_session_id=secondme_session_id,
      auth=auth,
      chat=chat,
      socket=socket,
      next_index=1,
    )
    self._repository.create(session, runtime, channel, first_question)

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
    channel = self._repository.get_channel(session_id)

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

    if session.currentRound >= session.totalRounds:
      completed_session = self._clone_session(
        session,
        status="completed",
        finishedAt=self._now(),
      )
      self._repository.save_session(completed_session)
      return SendMessageResponse(
        session=completed_session,
        userMessage=user_message,
        assistantMessage=None,
        shouldFetchFeedback=True,
      )

    next_round = session.currentRound + 1
    await self._secondme_client.send_message(
      visitor_token=runtime.auth.visitor_token,
      visitor_id=runtime.auth.visitor_id,
      session_id=runtime.secondme_session_id,
      visitor_user_id=runtime.auth.visitor_user_id,
      mind_id=runtime.chat.mind_id,
      ws_id=runtime.socket.ws_id,
      content=self._build_follow_up_prompt(
        role=session.role,
        mode=session.mode,
        next_round=next_round,
        total_rounds=session.totalRounds,
        answer=content,
      ),
      index=runtime.next_index,
    )
    runtime.next_index += 1
    self._repository.save_runtime(session.id, runtime)

    assistant_reply = await channel.wait_for_reply()
    assistant_message = ConversationMessage(
      id=str(uuid4()),
      role="assistant",
      content=assistant_reply,
      round=next_round,
      createdAt=self._now(),
    )
    self._repository.append_message(session.id, assistant_message)

    updated_session = self._clone_session(session, currentRound=next_round)
    self._repository.save_session(updated_session)

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

    existing_feedback = self._repository.get_feedback(session_id)
    if existing_feedback:
      return existing_feedback

    messages = self._repository.list_messages(session_id)
    runtime = self._repository.get_runtime(session_id)
    channel = self._repository.get_channel(session_id)
    feedback = await self._generate_feedback_with_secondme(
      session_id,
      session,
      messages,
      runtime,
      channel,
    )
    self._repository.save_feedback(feedback)
    return feedback

  async def close(self) -> None:
    await self._repository.close_all()

  async def _bootstrap_first_question(
    self,
    role: InterviewRole,
    mode: InterviewMode,
    total_rounds: int,
    visitor_token: str,
    visitor_id: str,
    secondme_session_id: str,
    visitor_user_id: str,
    mind_id: str,
    ws_id: str,
    channel: SecondMeRealtimeChannel,
  ) -> str:
    await self._secondme_client.send_message(
      visitor_token=visitor_token,
      visitor_id=visitor_id,
      session_id=secondme_session_id,
      visitor_user_id=visitor_user_id,
      mind_id=mind_id,
      ws_id=ws_id,
      content=self._build_bootstrap_prompt(role, mode, total_rounds),
      index=0,
    )
    return await channel.wait_for_reply()

  def _build_bootstrap_prompt(
    self,
    role: InterviewRole,
    mode: InterviewMode,
    total_rounds: int,
  ) -> str:
    return (
      f"你现在是一个{ROLE_LABELS[role]}模拟面试官。"
      f"当前模式是{MODE_LABELS[mode]}，整场共{total_rounds}轮。"
      "请直接开始第1轮提问，只输出一个问题本身，不要自我介绍，不要给建议，不要列点。"
    )

  def _build_follow_up_prompt(
    self,
    role: InterviewRole,
    mode: InterviewMode,
    next_round: int,
    total_rounds: int,
    answer: str,
  ) -> str:
    return (
      f"候选人刚才针对{ROLE_LABELS[role]}岗位的回答如下：{answer}\n"
      f"请继续以{MODE_LABELS[mode]}的面试节奏提出第{next_round}轮问题。"
      f"整场共{total_rounds}轮。"
      "只输出一个问题本身，不要复述回答，不要给建议，不要列点。"
    )

  async def _generate_feedback_with_secondme(
    self,
    session_id: str,
    session: Session,
    messages: List[ConversationMessage],
    runtime: SessionRuntime,
    channel: SecondMeRealtimeChannel,
  ) -> InterviewFeedback:
    raw_feedback = await self._request_secondme_reply(
      session_id=session_id,
      runtime=runtime,
      channel=channel,
      content=self._feedback_service.build_feedback_prompt(session, messages),
    )

    try:
      return self._feedback_service.parse_feedback(session, messages, raw_feedback)
    except UpstreamServiceError as exc:
      if exc.code != "SECONDME_FEEDBACK_PARSE_ERROR":
        raise
      logger.warning("SecondMe feedback parse failed on first pass: %s | raw=%s", exc.message, raw_feedback)
      repaired_feedback = await self._request_secondme_reply(
        session_id=session_id,
        runtime=runtime,
        channel=channel,
        content=self._feedback_service.build_repair_prompt(session, messages, raw_feedback),
      )
      return self._feedback_service.parse_feedback(session, messages, repaired_feedback)

  async def _request_secondme_reply(
    self,
    session_id: str,
    runtime: SessionRuntime,
    channel: SecondMeRealtimeChannel,
    content: str,
  ) -> str:
    await self._secondme_client.send_message(
      visitor_token=runtime.auth.visitor_token,
      visitor_id=runtime.auth.visitor_id,
      session_id=runtime.secondme_session_id,
      visitor_user_id=runtime.auth.visitor_user_id,
      mind_id=runtime.chat.mind_id,
      ws_id=runtime.socket.ws_id,
      content=content,
      index=runtime.next_index,
    )
    runtime.next_index += 1
    self._repository.save_runtime(session_id, runtime)
    return await channel.wait_for_reply()

  def _clone_session(self, session: Session, **changes: object) -> Session:
    payload = session.model_dump()
    payload.update(changes)
    return Session(**payload)

  def _ensure_secondme_configured(self) -> None:
    if not self._settings.secondme_enabled:
      raise ConfigError("SecondMe 配置缺失，请先在 apps/api/.env 中补齐 API Key 和 share code。")

  def _clamp_rounds(self, total_rounds: int = None) -> int:
    if total_rounds is None:
      return 3
    return min(3, max(1, int(total_rounds)))

  def _now(self) -> str:
    return datetime.now(timezone.utc).isoformat()
