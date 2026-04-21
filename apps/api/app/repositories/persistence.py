from __future__ import annotations

from typing import List, Optional, Protocol

from app.models.api import ConversationMessage, InterviewFeedback, InterviewMode, InterviewRole, Interviewer, Session
from app.models.persistence import InterviewerProfileEntry, InterviewerSecretEntry, QuestionBankEntry, SecondMeConnectionEntry


class PersistenceRepository(Protocol):
  def sync_interviewers(self, interviewers: List[Interviewer]) -> None:
    ...

  def upsert_interviewer_secret(self, interviewer_id: str, avatar_api_key: str) -> None:
    ...

  def get_interviewer_secret(self, interviewer_id: str) -> Optional[InterviewerSecretEntry]:
    ...

  def list_interviewer_profiles(self, enabled_only: bool = True) -> List[InterviewerProfileEntry]:
    ...

  def upsert_interviewer_profile(self, profile: InterviewerProfileEntry) -> None:
    ...

  def delete_interviewer_profile(self, interviewer_id: str) -> bool:
    ...

  def save_secondme_connection(self, connection: SecondMeConnectionEntry) -> None:
    ...

  def save_session(self, session: Session) -> None:
    ...

  def append_message(self, session_id: str, message: ConversationMessage) -> None:
    ...

  def save_feedback(self, feedback: InterviewFeedback) -> None:
    ...

  def get_feedback(self, session_id: str) -> Optional[InterviewFeedback]:
    ...

  def add_question(
    self,
    *,
    role: InterviewRole,
    mode: Optional[InterviewMode],
    interviewer_type: str,
    provider: str,
    prompt_strategy: str,
    question: str,
    source_session_id: Optional[str],
    created_at: str,
  ) -> None:
    ...

  def list_questions(
    self,
    *,
    role: Optional[InterviewRole] = None,
    mode: Optional[InterviewMode] = None,
    provider: Optional[str] = None,
  ) -> List[QuestionBankEntry]:
    ...


class NullPersistenceRepository:
  def sync_interviewers(self, interviewers: List[Interviewer]) -> None:
    _ = interviewers

  def upsert_interviewer_secret(self, interviewer_id: str, avatar_api_key: str) -> None:
    _ = (interviewer_id, avatar_api_key)

  def get_interviewer_secret(self, interviewer_id: str) -> Optional[InterviewerSecretEntry]:
    _ = interviewer_id
    return None

  def list_interviewer_profiles(self, enabled_only: bool = True) -> List[InterviewerProfileEntry]:
    _ = enabled_only
    return []

  def upsert_interviewer_profile(self, profile: InterviewerProfileEntry) -> None:
    _ = profile

  def delete_interviewer_profile(self, interviewer_id: str) -> bool:
    _ = interviewer_id
    return False

  def save_secondme_connection(self, connection: SecondMeConnectionEntry) -> None:
    _ = connection

  def save_session(self, session: Session) -> None:
    _ = session

  def append_message(self, session_id: str, message: ConversationMessage) -> None:
    _ = (session_id, message)

  def save_feedback(self, feedback: InterviewFeedback) -> None:
    _ = feedback

  def get_feedback(self, session_id: str) -> Optional[InterviewFeedback]:
    _ = session_id
    return None

  def add_question(
    self,
    *,
    role: InterviewRole,
    mode: Optional[InterviewMode],
    interviewer_type: str,
    provider: str,
    prompt_strategy: str,
    question: str,
    source_session_id: Optional[str],
    created_at: str,
  ) -> None:
    _ = (role, mode, interviewer_type, provider, prompt_strategy, question, source_session_id, created_at)

  def list_questions(
    self,
    *,
    role: Optional[InterviewRole] = None,
    mode: Optional[InterviewMode] = None,
    provider: Optional[str] = None,
  ) -> List[QuestionBankEntry]:
    _ = (role, mode, provider)
    return []
