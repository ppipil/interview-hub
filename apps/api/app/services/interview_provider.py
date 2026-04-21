from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Dict, List, Optional, Protocol
from uuid import uuid4

from app.core.errors import ConfigError, UpstreamServiceError
from app.models.api import (
  ConversationMessage,
  InterviewFeedback,
  InterviewMode,
  InterviewRole,
  Interviewer,
  InterviewerProvider,
  Session,
)
from app.models.runtime import (
  DoubaoRuntime,
  SecondMeLegacyRuntime,
  SecondMeVisitorChatRuntime,
  SessionRuntime,
)
from app.repositories.persistence import PersistenceRepository
from app.services.doubao_client import DoubaoClient
from app.services.feedback import FeedbackService
from app.services.interview_prompts import (
  build_avatar_bootstrap_prompt,
  build_avatar_follow_up_prompt,
  build_system_bootstrap_prompt,
  build_system_follow_up_prompt,
)
from app.services.realtime import SecondMeRealtimeChannel
from app.services.secondme_client import SecondMeClient
from app.services.secondme_visitor_client import SecondMeVisitorChatClient

logger = logging.getLogger(__name__)


@dataclass
class ProviderBootstrapResult:
  first_question_text: str
  runtime: SessionRuntime
  channel: Optional[SecondMeRealtimeChannel] = None


class InterviewProvider(Protocol):
  provider_name: InterviewerProvider

  async def bootstrap(
    self,
    interviewer: Interviewer,
    role: InterviewRole,
    mode: InterviewMode,
    total_rounds: int,
  ) -> ProviderBootstrapResult:
    ...

  async def follow_up(
    self,
    interviewer: Interviewer,
    session: Session,
    runtime: SessionRuntime,
    channel: Optional[SecondMeRealtimeChannel],
    answer: str,
  ) -> str:
    ...

  async def generate_feedback(
    self,
    session: Session,
    messages: List[ConversationMessage],
    runtime: SessionRuntime,
    channel: Optional[SecondMeRealtimeChannel],
  ) -> InterviewFeedback:
    ...

  async def close(
    self,
    runtime: SessionRuntime,
    channel: Optional[SecondMeRealtimeChannel],
  ) -> None:
    ...


class LegacySecondMeInterviewProvider:
  provider_name: InterviewerProvider = "secondme_legacy"

  def __init__(
    self,
    secondme_client: SecondMeClient,
    feedback_service: FeedbackService,
    *,
    secondme_api_key: str,
    secondme_avatar_share_code: str,
    secondme_channel: str,
    secondme_ws_origin: str,
    heartbeat_interval_seconds: int,
    websocket_reply_timeout_seconds: float,
  ) -> None:
    self._secondme_client = secondme_client
    self._feedback_service = feedback_service
    self._secondme_api_key = secondme_api_key
    self._secondme_avatar_share_code = secondme_avatar_share_code
    self._secondme_channel = secondme_channel
    self._secondme_ws_origin = secondme_ws_origin
    self._heartbeat_interval_seconds = heartbeat_interval_seconds
    self._websocket_reply_timeout_seconds = websocket_reply_timeout_seconds

  async def bootstrap(
    self,
    interviewer: Interviewer,
    role: InterviewRole,
    mode: InterviewMode,
    total_rounds: int,
  ) -> ProviderBootstrapResult:
    if not self._secondme_api_key or not self._secondme_avatar_share_code:
      raise ConfigError("SecondMe Legacy 配置缺失，请先补齐 SECONDME_API_KEY 和 SECONDME_AVATAR_SHARE_CODE。")

    visitor_id = f"{self._secondme_channel}_{uuid4()}"
    auth = await self._secondme_client.authenticate(
      api_key=self._secondme_api_key,
      visitor_id=visitor_id,
      visitor_name="Interview Hub User",
    )
    chat = await self._secondme_client.initialize_chat(
      visitor_token=auth.visitor_token,
      visitor_id=auth.visitor_id,
      share_code=self._secondme_avatar_share_code,
    )
    socket = await self._secondme_client.create_websocket(
      visitor_token=auth.visitor_token,
      visitor_id=auth.visitor_id,
      visitor_user_id=auth.visitor_user_id,
    )

    channel = SecondMeRealtimeChannel(
      ws_id=socket.ws_id,
      visitor_user_id=auth.visitor_user_id,
      origin=self._secondme_ws_origin,
      heartbeat_interval_seconds=self._heartbeat_interval_seconds,
      reply_timeout_seconds=self._websocket_reply_timeout_seconds,
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
        share_code=self._secondme_avatar_share_code,
      )
      await self._secondme_client.bind_session(
        visitor_token=auth.visitor_token,
        visitor_id=auth.visitor_id,
        avatar_id=avatar_id,
        session_id=secondme_session_id,
      )
      prompt = build_avatar_bootstrap_prompt(interviewer, role, mode, total_rounds)
      await self._secondme_client.send_message(
        visitor_token=auth.visitor_token,
        visitor_id=auth.visitor_id,
        session_id=secondme_session_id,
        visitor_user_id=auth.visitor_user_id,
        mind_id=chat.mind_id,
        ws_id=socket.ws_id,
        content=prompt,
        index=0,
      )
      first_question_text = await channel.wait_for_reply()
    except Exception:
      await channel.close()
      raise

    return ProviderBootstrapResult(
      first_question_text=first_question_text,
      runtime=SecondMeLegacyRuntime(
        provider=self.provider_name,
        secondme_session_id=secondme_session_id,
        auth=auth,
        chat=chat,
        socket=socket,
        next_index=1,
      ),
      channel=channel,
    )

  async def follow_up(
    self,
    interviewer: Interviewer,
    session: Session,
    runtime: SessionRuntime,
    channel: Optional[SecondMeRealtimeChannel],
    answer: str,
  ) -> str:
    if not isinstance(runtime, SecondMeLegacyRuntime) or channel is None:
      raise UpstreamServiceError("SecondMe Legacy 运行时缺失，无法继续面试。", code="SECONDME_LEGACY_RUNTIME_ERROR")

    next_round = session.currentRound + 1
    await self._secondme_client.send_message(
      visitor_token=runtime.auth.visitor_token,
      visitor_id=runtime.auth.visitor_id,
      session_id=runtime.secondme_session_id,
      visitor_user_id=runtime.auth.visitor_user_id,
      mind_id=runtime.chat.mind_id,
      ws_id=runtime.socket.ws_id,
      content=build_avatar_follow_up_prompt(
        interviewer=interviewer,
        role=session.role,
        mode=session.mode,
        next_round=next_round,
        total_rounds=session.totalRounds,
        answer=answer,
      ),
      index=runtime.next_index,
    )
    runtime.next_index += 1
    return await channel.wait_for_reply()

  async def generate_feedback(
    self,
    session: Session,
    messages: List[ConversationMessage],
    runtime: SessionRuntime,
    channel: Optional[SecondMeRealtimeChannel],
  ) -> InterviewFeedback:
    if not isinstance(runtime, SecondMeLegacyRuntime) or channel is None:
      raise UpstreamServiceError("SecondMe Legacy 运行时缺失，暂时无法生成反馈。", code="SECONDME_LEGACY_RUNTIME_ERROR")

    raw_feedback = await self._request_reply(
      runtime=runtime,
      channel=channel,
      content=self._feedback_service.build_feedback_prompt(session, messages),
    )
    try:
      return self._feedback_service.parse_feedback(session, messages, raw_feedback)
    except UpstreamServiceError as exc:
      if exc.code != "SECONDME_FEEDBACK_PARSE_ERROR":
        raise
      logger.warning("Legacy SecondMe feedback parse failed on first pass: %s | raw=%s", exc.message, raw_feedback)
      repaired_feedback = await self._request_reply(
        runtime=runtime,
        channel=channel,
        content=self._feedback_service.build_repair_prompt(session, messages, raw_feedback),
      )
      return self._feedback_service.parse_feedback(session, messages, repaired_feedback)

  async def close(self, runtime: SessionRuntime, channel: Optional[SecondMeRealtimeChannel]) -> None:
    _ = runtime
    if channel:
      await channel.close()

  async def _request_reply(
    self,
    *,
    runtime: SecondMeLegacyRuntime,
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
    return await channel.wait_for_reply()


class SecondMeVisitorInterviewProvider:
  provider_name: InterviewerProvider = "secondme_visitor"

  def __init__(
    self,
    visitor_client: SecondMeVisitorChatClient,
    feedback_service: FeedbackService,
    persistence: PersistenceRepository,
    *,
    websocket_reply_timeout_seconds: float,
  ) -> None:
    self._visitor_client = visitor_client
    self._feedback_service = feedback_service
    self._persistence = persistence
    self._websocket_reply_timeout_seconds = websocket_reply_timeout_seconds

  async def bootstrap(
    self,
    interviewer: Interviewer,
    role: InterviewRole,
    mode: InterviewMode,
    total_rounds: int,
  ) -> ProviderBootstrapResult:
    if not self._visitor_client.configured:
      raise ConfigError(
        "SecondMe Visitor Chat 配置缺失，请先补齐 SECONDME_APP_CLIENT_ID 和 SECONDME_APP_CLIENT_SECRET。",
      )

    visitor_id = f"visitor_{uuid4().hex}"
    visitor_name = "Interview Hub User"
    avatar_api_key = self._resolve_avatar_api_key(interviewer.id)
    chat = await self._visitor_client.initialize_chat(
      visitor_id=visitor_id,
      visitor_name=visitor_name,
      avatar_api_key=avatar_api_key,
    )
    channel = SecondMeRealtimeChannel(
      ws_id=chat.session_id,
      visitor_user_id=visitor_id,
      origin=None,
      heartbeat_interval_seconds=0,
      reply_timeout_seconds=self._websocket_reply_timeout_seconds,
    )
    await channel.connect(chat.ws_url)
    try:
      await self._visitor_client.send_message(
        access_token=chat.access_token,
        session_id=chat.session_id,
        avatar_api_key=avatar_api_key,
        message=build_avatar_bootstrap_prompt(interviewer, role, mode, total_rounds),
      )
      first_question_text = await channel.wait_for_reply()
    except Exception:
      await channel.close()
      raise

    return ProviderBootstrapResult(
      first_question_text=first_question_text,
      runtime=SecondMeVisitorChatRuntime(
        provider=self.provider_name,
        session_id=chat.session_id,
        access_token=chat.access_token,
        api_key=avatar_api_key,
        visitor_id=visitor_id,
        visitor_name=visitor_name,
      ),
      channel=channel,
    )

  async def follow_up(
    self,
    interviewer: Interviewer,
    session: Session,
    runtime: SessionRuntime,
    channel: Optional[SecondMeRealtimeChannel],
    answer: str,
  ) -> str:
    if not isinstance(runtime, SecondMeVisitorChatRuntime) or channel is None:
      raise UpstreamServiceError("SecondMe Visitor Chat 运行时缺失，无法继续面试。", code="SECONDME_VISITOR_RUNTIME_ERROR")

    next_round = session.currentRound + 1
    await self._visitor_client.send_message(
      access_token=runtime.access_token,
      session_id=runtime.session_id,
      avatar_api_key=runtime.api_key,
      message=build_avatar_follow_up_prompt(
        interviewer=interviewer,
        role=session.role,
        mode=session.mode,
        next_round=next_round,
        total_rounds=session.totalRounds,
        answer=answer,
      ),
    )
    return await channel.wait_for_reply()

  async def generate_feedback(
    self,
    session: Session,
    messages: List[ConversationMessage],
    runtime: SessionRuntime,
    channel: Optional[SecondMeRealtimeChannel],
  ) -> InterviewFeedback:
    if not isinstance(runtime, SecondMeVisitorChatRuntime) or channel is None:
      raise UpstreamServiceError("SecondMe Visitor Chat 运行时缺失，暂时无法生成反馈。", code="SECONDME_VISITOR_RUNTIME_ERROR")

    raw_feedback = await self._request_reply(
      runtime=runtime,
      channel=channel,
      content=self._feedback_service.build_feedback_prompt(session, messages),
    )
    try:
      return self._feedback_service.parse_feedback(session, messages, raw_feedback)
    except UpstreamServiceError as exc:
      if exc.code != "SECONDME_FEEDBACK_PARSE_ERROR":
        raise
      logger.warning("Visitor Chat feedback parse failed on first pass: %s | raw=%s", exc.message, raw_feedback)
      repaired_feedback = await self._request_reply(
        runtime=runtime,
        channel=channel,
        content=self._feedback_service.build_repair_prompt(session, messages, raw_feedback),
      )
      return self._feedback_service.parse_feedback(session, messages, repaired_feedback)

  async def close(self, runtime: SessionRuntime, channel: Optional[SecondMeRealtimeChannel]) -> None:
    _ = runtime
    if channel:
      await channel.close()

  async def _request_reply(
    self,
    *,
    runtime: SecondMeVisitorChatRuntime,
    channel: SecondMeRealtimeChannel,
    content: str,
  ) -> str:
    await self._visitor_client.send_message(
      access_token=runtime.access_token,
      session_id=runtime.session_id,
      avatar_api_key=runtime.api_key,
      message=content,
    )
    return await channel.wait_for_reply()

  def _resolve_avatar_api_key(self, interviewer_id: str) -> str:
    profile = next(
      (item for item in self._persistence.list_interviewer_profiles() if item.interviewer_id == interviewer_id),
      None,
    )
    if profile and profile.avatar_api_key and profile.avatar_api_key.strip():
      return profile.avatar_api_key.strip()

    secret = self._persistence.get_interviewer_secret(interviewer_id)
    if secret and secret.avatar_api_key.strip():
      return secret.avatar_api_key.strip()

    default_key = self._visitor_client.avatar_api_key
    if default_key:
      return default_key

    raise ConfigError(
      "SecondMe Visitor Chat 缺少分身 API Key，请配置 SECONDME_AVATAR_API_KEY，或在 interviewer_profiles 表中为当前 interviewer 写入 avatar_api_key。",
    )


class DoubaoInterviewProvider:
  provider_name: InterviewerProvider = "doubao"

  def __init__(self, doubao_client: DoubaoClient, feedback_service: FeedbackService) -> None:
    self._doubao_client = doubao_client
    self._feedback_service = feedback_service

  async def bootstrap(
    self,
    interviewer: Interviewer,
    role: InterviewRole,
    mode: InterviewMode,
    total_rounds: int,
  ) -> ProviderBootstrapResult:
    first_question_text = await self._doubao_client.chat(
      messages=[
        {
          "role": "system",
          "content": "你是一位专业、直接、表达清晰的中文模拟面试官。",
        },
        {
          "role": "user",
          "content": build_system_bootstrap_prompt(interviewer, role, mode, total_rounds),
        },
      ],
      max_tokens=384,
    )
    return ProviderBootstrapResult(
      first_question_text=first_question_text,
      runtime=DoubaoRuntime(provider=self.provider_name, model=self._doubao_client.model),
      channel=None,
    )

  async def follow_up(
    self,
    interviewer: Interviewer,
    session: Session,
    runtime: SessionRuntime,
    channel: Optional[SecondMeRealtimeChannel],
    answer: str,
  ) -> str:
    _ = (runtime, channel)
    return await self._doubao_client.chat(
      messages=[
        {
          "role": "system",
          "content": "你是一位专业、直接、表达清晰的中文模拟面试官。",
        },
        {
          "role": "user",
          "content": build_system_follow_up_prompt(
            interviewer=interviewer,
            role=session.role,
            mode=session.mode,
            next_round=session.currentRound + 1,
            total_rounds=session.totalRounds,
            answer=answer,
          ),
        },
      ],
      max_tokens=384,
    )

  async def generate_feedback(
    self,
    session: Session,
    messages: List[ConversationMessage],
    runtime: SessionRuntime,
    channel: Optional[SecondMeRealtimeChannel],
  ) -> InterviewFeedback:
    _ = (runtime, channel)
    raw_feedback = await self._doubao_client.chat(
      messages=[
        {
          "role": "system",
          "content": "你是一位严格但建设性的中文模拟面试官，请严格遵守用户给出的 JSON 输出要求。",
        },
        {
          "role": "user",
          "content": self._feedback_service.build_feedback_prompt(session, messages),
        },
      ],
      max_tokens=1800,
    )
    try:
      return self._feedback_service.parse_feedback(session, messages, raw_feedback)
    except UpstreamServiceError as exc:
      if exc.code != "SECONDME_FEEDBACK_PARSE_ERROR":
        raise
      repaired_feedback = await self._doubao_client.chat(
        messages=[
          {
            "role": "system",
            "content": "你是一位严格但建设性的中文模拟面试官，请严格遵守用户给出的 JSON 输出要求。",
          },
          {
            "role": "user",
            "content": self._feedback_service.build_repair_prompt(session, messages, raw_feedback),
          },
        ],
        max_tokens=1800,
      )
      return self._feedback_service.parse_feedback(session, messages, repaired_feedback)

  async def close(self, runtime: SessionRuntime, channel: Optional[SecondMeRealtimeChannel]) -> None:
    _ = (runtime, channel)


class InterviewProviderRegistry:
  def __init__(self, providers: List[InterviewProvider]) -> None:
    self._providers: Dict[InterviewerProvider, InterviewProvider] = {
      provider.provider_name: provider
      for provider in providers
    }

  def get(self, provider_name: InterviewerProvider) -> InterviewProvider:
    provider = self._providers.get(provider_name)
    if not provider:
      raise ConfigError(f"未找到 provider={provider_name} 的面试能力实现。")
    return provider
