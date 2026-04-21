from __future__ import annotations

from typing import Dict, List, Optional

from app.core.errors import NotFoundError
from app.models.api import ConversationMessage, InterviewFeedback, Session
from app.models.runtime import SessionRuntime
from app.services.realtime import SecondMeRealtimeChannel


class InMemorySessionRepository:
  def __init__(self) -> None:
    self._sessions: Dict[str, Session] = {}
    self._messages: Dict[str, List[ConversationMessage]] = {}
    self._feedbacks: Dict[str, InterviewFeedback] = {}
    self._runtimes: Dict[str, SessionRuntime] = {}
    self._channels: Dict[str, SecondMeRealtimeChannel] = {}

  def create(
    self,
    session: Session,
    runtime: SessionRuntime,
    channel: Optional[SecondMeRealtimeChannel],
    first_question: ConversationMessage,
  ) -> None:
    self._sessions[session.id] = session
    self._runtimes[session.id] = runtime
    if channel:
      self._channels[session.id] = channel
    self._messages[session.id] = [first_question]

  def get_session(self, session_id: str) -> Session:
    session = self._sessions.get(session_id)
    if not session:
      raise NotFoundError("未找到对应的面试 Session。", field="sessionId")
    return session

  def save_session(self, session: Session) -> None:
    self._sessions[session.id] = session

  def append_message(self, session_id: str, message: ConversationMessage) -> None:
    self._messages.setdefault(session_id, []).append(message)

  def list_messages(self, session_id: str) -> List[ConversationMessage]:
    self.get_session(session_id)
    return list(self._messages.get(session_id, []))

  def save_feedback(self, feedback: InterviewFeedback) -> None:
    self._feedbacks[feedback.sessionId] = feedback

  def get_feedback(self, session_id: str) -> Optional[InterviewFeedback]:
    return self._feedbacks.get(session_id)

  def get_runtime(self, session_id: str) -> SessionRuntime:
    self.get_session(session_id)
    runtime = self._runtimes.get(session_id)
    if not runtime:
      raise NotFoundError("未找到对应的会话运行时。", field="sessionId")
    return runtime

  def save_runtime(self, session_id: str, runtime: SessionRuntime) -> None:
    self._runtimes[session_id] = runtime

  def get_channel(self, session_id: str) -> SecondMeRealtimeChannel:
    self.get_session(session_id)
    channel = self._channels.get(session_id)
    if not channel:
      raise NotFoundError("未找到对应的实时连接。", field="sessionId")
    return channel

  def get_optional_channel(self, session_id: str) -> Optional[SecondMeRealtimeChannel]:
    self.get_session(session_id)
    return self._channels.get(session_id)

  async def close_all(self) -> None:
    for channel in list(self._channels.values()):
      if channel:
        await channel.close()
