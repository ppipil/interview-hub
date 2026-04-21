from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Iterator, List, Optional

from app.core.errors import ConfigError
from app.models.api import ConversationMessage, InterviewFeedback, InterviewMode, InterviewRole, Interviewer, Session
from app.models.persistence import InterviewerProfileEntry, InterviewerSecretEntry, QuestionBankEntry, SecondMeConnectionEntry


class SqlitePersistenceRepository:
  def __init__(self, database_url: str) -> None:
    self._db_path = self._resolve_db_path(database_url)
    self._db_path.parent.mkdir(parents=True, exist_ok=True)
    self._initialize()

  def sync_interviewers(self, interviewers: List[Interviewer]) -> None:
    with self._connect() as connection:
      connection.executemany(
        """
        INSERT INTO interviewers (
          id, type, provider, prompt_strategy, name, title, description,
          avatar_url, tags_json, supported_roles_json, supported_modes_json,
          persona, skill_prompt, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          type=excluded.type,
          provider=excluded.provider,
          prompt_strategy=excluded.prompt_strategy,
          name=excluded.name,
          title=excluded.title,
          description=excluded.description,
          avatar_url=excluded.avatar_url,
          tags_json=excluded.tags_json,
          supported_roles_json=excluded.supported_roles_json,
          supported_modes_json=excluded.supported_modes_json,
          persona=excluded.persona,
          skill_prompt=COALESCE(interviewers.skill_prompt, excluded.skill_prompt),
          updated_at=excluded.updated_at
        """,
        [
          (
            interviewer.id,
            interviewer.type,
            interviewer.provider,
            interviewer.promptStrategy,
            interviewer.name,
            interviewer.title,
            interviewer.description,
            interviewer.avatarUrl,
            json.dumps(interviewer.tags, ensure_ascii=False),
            json.dumps(interviewer.supportedRoles, ensure_ascii=False),
            json.dumps(interviewer.supportedModes, ensure_ascii=False),
            interviewer.persona,
            interviewer.skillPrompt,
            self._now(),
          )
          for interviewer in interviewers
        ],
      )

  def upsert_interviewer_secret(self, interviewer_id: str, avatar_api_key: str) -> None:
    now = self._now()
    with self._connect() as connection:
      connection.execute(
        """
        INSERT INTO interviewer_secrets (
          interviewer_id, avatar_api_key, created_at, updated_at
        )
        VALUES (?, ?, ?, ?)
        ON CONFLICT(interviewer_id) DO UPDATE SET
          avatar_api_key=excluded.avatar_api_key,
          updated_at=excluded.updated_at
        """,
        (
          interviewer_id,
          avatar_api_key,
          now,
          now,
        ),
      )

  def get_interviewer_secret(self, interviewer_id: str) -> Optional[InterviewerSecretEntry]:
    with self._connect() as connection:
      row = connection.execute(
        """
        SELECT interviewer_id, avatar_api_key, created_at, updated_at
        FROM interviewer_secrets
        WHERE interviewer_id = ?
        """,
        (interviewer_id,),
      ).fetchone()
    if not row:
      return None
    return InterviewerSecretEntry(
      interviewer_id=row["interviewer_id"],
      avatar_api_key=row["avatar_api_key"],
      created_at=row["created_at"],
      updated_at=row["updated_at"],
    )

  def list_interviewer_profiles(self, enabled_only: bool = True) -> List[InterviewerProfileEntry]:
    query = [
      """
      SELECT
        interviewer_id, type, provider, name, title, description, avatar_url,
        tags_json, supported_roles_json, supported_modes_json, persona,
        prompt_strategy, skill_prompt, interview_flow, avatar_api_key,
        enabled, created_at, updated_at
      FROM interviewer_profiles
      """
    ]
    if enabled_only:
      query.append("WHERE enabled = 1")
    query.append("ORDER BY updated_at DESC")

    with self._connect() as connection:
      rows = connection.execute("\n".join(query)).fetchall()

    return [self._row_to_interviewer_profile(row) for row in rows]

  def upsert_interviewer_profile(self, profile: InterviewerProfileEntry) -> None:
    with self._connect() as connection:
      connection.execute(
        """
        INSERT INTO interviewer_profiles (
          interviewer_id, type, provider, name, title, description, avatar_url,
          tags_json, supported_roles_json, supported_modes_json, persona,
          prompt_strategy, skill_prompt, interview_flow, avatar_api_key,
          enabled, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(interviewer_id) DO UPDATE SET
          type=excluded.type,
          provider=excluded.provider,
          name=excluded.name,
          title=excluded.title,
          description=excluded.description,
          avatar_url=excluded.avatar_url,
          tags_json=excluded.tags_json,
          supported_roles_json=excluded.supported_roles_json,
          supported_modes_json=excluded.supported_modes_json,
          persona=excluded.persona,
          prompt_strategy=excluded.prompt_strategy,
          skill_prompt=excluded.skill_prompt,
          interview_flow=excluded.interview_flow,
          avatar_api_key=excluded.avatar_api_key,
          enabled=excluded.enabled,
          updated_at=excluded.updated_at
        """,
        (
          profile.interviewer_id,
          profile.type,
          profile.provider,
          profile.name,
          profile.title,
          profile.description,
          profile.avatar_url,
          json.dumps(profile.tags or [], ensure_ascii=False),
          json.dumps(profile.supported_roles or [], ensure_ascii=False),
          json.dumps(profile.supported_modes or [], ensure_ascii=False),
          profile.persona,
          profile.prompt_strategy,
          profile.skill_prompt,
          profile.interview_flow,
          profile.avatar_api_key,
          1 if profile.enabled else 0,
          profile.created_at,
          profile.updated_at,
        ),
      )

  def delete_interviewer_profile(self, interviewer_id: str) -> bool:
    with self._connect() as connection:
      cursor = connection.execute(
        "DELETE FROM interviewer_profiles WHERE interviewer_id = ?",
        (interviewer_id,),
      )
      return cursor.rowcount > 0

  def save_secondme_connection(self, connection_entry: SecondMeConnectionEntry) -> None:
    with self._connect() as connection:
      connection.execute(
        """
        INSERT INTO secondme_connections (
          interviewer_id, secondme_user_id, avatar_id, avatar_name,
          access_token, refresh_token, token_expires_at, scope_json,
          avatar_api_key, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(interviewer_id) DO UPDATE SET
          secondme_user_id=excluded.secondme_user_id,
          avatar_id=excluded.avatar_id,
          avatar_name=excluded.avatar_name,
          access_token=excluded.access_token,
          refresh_token=excluded.refresh_token,
          token_expires_at=excluded.token_expires_at,
          scope_json=excluded.scope_json,
          avatar_api_key=excluded.avatar_api_key,
          updated_at=excluded.updated_at
        """,
        (
          connection_entry.interviewer_id,
          connection_entry.secondme_user_id,
          connection_entry.avatar_id,
          connection_entry.avatar_name,
          connection_entry.access_token,
          connection_entry.refresh_token,
          connection_entry.token_expires_at,
          json.dumps(connection_entry.scope, ensure_ascii=False),
          connection_entry.avatar_api_key,
          connection_entry.created_at,
          connection_entry.updated_at,
        ),
      )

  def save_session(self, session: Session) -> None:
    with self._connect() as connection:
      connection.execute(
        """
        INSERT INTO interview_sessions (
          id, role, mode, interviewer_id, status, current_round, total_rounds,
          started_at, finished_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          role=excluded.role,
          mode=excluded.mode,
          interviewer_id=excluded.interviewer_id,
          status=excluded.status,
          current_round=excluded.current_round,
          total_rounds=excluded.total_rounds,
          started_at=excluded.started_at,
          finished_at=excluded.finished_at,
          updated_at=excluded.updated_at
        """,
        (
          session.id,
          session.role,
          session.mode,
          session.interviewerId,
          session.status,
          session.currentRound,
          session.totalRounds,
          session.startedAt,
          session.finishedAt,
          self._now(),
        ),
      )

  def append_message(self, session_id: str, message: ConversationMessage) -> None:
    with self._connect() as connection:
      connection.execute(
        """
        INSERT OR REPLACE INTO conversation_messages (
          id, session_id, role, content, round, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
          message.id,
          session_id,
          message.role,
          message.content,
          message.round,
          message.createdAt,
        ),
      )

  def save_feedback(self, feedback: InterviewFeedback) -> None:
    payload_json = feedback.model_dump_json()
    with self._connect() as connection:
      connection.execute(
        """
        INSERT INTO interview_feedback (
          session_id, payload_json, generated_at, updated_at
        )
        VALUES (?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
          payload_json=excluded.payload_json,
          generated_at=excluded.generated_at,
          updated_at=excluded.updated_at
        """,
        (
          feedback.sessionId,
          payload_json,
          feedback.generatedAt,
          self._now(),
        ),
      )

  def get_feedback(self, session_id: str) -> Optional[InterviewFeedback]:
    with self._connect() as connection:
      row = connection.execute(
        "SELECT payload_json FROM interview_feedback WHERE session_id = ?",
        (session_id,),
      ).fetchone()
    if not row:
      return None
    return InterviewFeedback.model_validate_json(row["payload_json"])

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
    fingerprint = hashlib.sha256(
      "|".join(
        [
          role,
          mode or "",
          interviewer_type,
          provider,
          prompt_strategy,
          question.strip(),
        ]
      ).encode("utf-8"),
    ).hexdigest()
    with self._connect() as connection:
      connection.execute(
        """
        INSERT INTO question_bank (
          id, role, mode, interviewer_type, provider, prompt_strategy,
          question, source_session_id, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          source_session_id=COALESCE(excluded.source_session_id, question_bank.source_session_id),
          created_at=question_bank.created_at
        """,
        (
          fingerprint,
          role,
          mode,
          interviewer_type,
          provider,
          prompt_strategy,
          question.strip(),
          source_session_id,
          created_at,
        ),
      )

  def list_questions(
    self,
    *,
    role: Optional[InterviewRole] = None,
    mode: Optional[InterviewMode] = None,
    provider: Optional[str] = None,
  ) -> List[QuestionBankEntry]:
    query = [
      """
      SELECT id, role, mode, interviewer_type, provider, prompt_strategy,
             question, source_session_id, created_at
      FROM question_bank
      WHERE 1 = 1
      """
    ]
    params: List[str] = []
    if role:
      query.append("AND role = ?")
      params.append(role)
    if mode:
      query.append("AND mode = ?")
      params.append(mode)
    if provider:
      query.append("AND provider = ?")
      params.append(provider)
    query.append("ORDER BY created_at DESC")

    with self._connect() as connection:
      rows = connection.execute("\n".join(query), params).fetchall()

    return [
      QuestionBankEntry(
        id=row["id"],
        role=row["role"],
        mode=row["mode"],
        interviewer_type=row["interviewer_type"],
        provider=row["provider"],
        prompt_strategy=row["prompt_strategy"],
        question=row["question"],
        source_session_id=row["source_session_id"],
        created_at=row["created_at"],
      )
      for row in rows
    ]

  @contextmanager
  def _connect(self) -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(self._db_path)
    connection.row_factory = sqlite3.Row
    try:
      yield connection
      connection.commit()
    finally:
      connection.close()

  def _initialize(self) -> None:
    with self._connect() as connection:
      connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS interviewers (
          id TEXT PRIMARY KEY,
          type TEXT NOT NULL,
          provider TEXT NOT NULL,
          prompt_strategy TEXT,
          name TEXT NOT NULL,
          title TEXT NOT NULL,
          description TEXT NOT NULL,
          avatar_url TEXT NOT NULL,
          tags_json TEXT NOT NULL,
          supported_roles_json TEXT NOT NULL,
          supported_modes_json TEXT NOT NULL,
          persona TEXT,
          skill_prompt TEXT,
          updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS interviewer_secrets (
          interviewer_id TEXT PRIMARY KEY,
          avatar_api_key TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS interviewer_profiles (
          interviewer_id TEXT PRIMARY KEY,
          type TEXT,
          provider TEXT,
          name TEXT,
          title TEXT,
          description TEXT,
          avatar_url TEXT,
          tags_json TEXT,
          supported_roles_json TEXT,
          supported_modes_json TEXT,
          persona TEXT,
          prompt_strategy TEXT,
          skill_prompt TEXT,
          interview_flow TEXT,
          avatar_api_key TEXT,
          enabled INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS secondme_connections (
          interviewer_id TEXT PRIMARY KEY,
          secondme_user_id TEXT,
          avatar_id TEXT NOT NULL,
          avatar_name TEXT NOT NULL,
          access_token TEXT NOT NULL,
          refresh_token TEXT,
          token_expires_at TEXT,
          scope_json TEXT NOT NULL,
          avatar_api_key TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS interview_sessions (
          id TEXT PRIMARY KEY,
          role TEXT NOT NULL,
          mode TEXT NOT NULL,
          interviewer_id TEXT NOT NULL,
          status TEXT NOT NULL,
          current_round INTEGER NOT NULL,
          total_rounds INTEGER NOT NULL,
          started_at TEXT NOT NULL,
          finished_at TEXT,
          updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS conversation_messages (
          id TEXT PRIMARY KEY,
          session_id TEXT NOT NULL,
          role TEXT NOT NULL,
          content TEXT NOT NULL,
          round INTEGER NOT NULL,
          created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_conversation_messages_session
          ON conversation_messages(session_id, created_at);

        CREATE TABLE IF NOT EXISTS interview_feedback (
          session_id TEXT PRIMARY KEY,
          payload_json TEXT NOT NULL,
          generated_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS question_bank (
          id TEXT PRIMARY KEY,
          role TEXT NOT NULL,
          mode TEXT,
          interviewer_type TEXT NOT NULL,
          provider TEXT NOT NULL,
          prompt_strategy TEXT NOT NULL,
          question TEXT NOT NULL,
          source_session_id TEXT,
          created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_question_bank_lookup
          ON question_bank(role, mode, provider, created_at DESC);
        """
      )
      self._ensure_column(connection, "interviewers", "skill_prompt", "TEXT")
      self._ensure_column(connection, "interviewer_profiles", "type", "TEXT")
      self._ensure_column(connection, "interviewer_profiles", "provider", "TEXT")
      self._ensure_column(connection, "interviewer_profiles", "name", "TEXT")
      self._ensure_column(connection, "interviewer_profiles", "title", "TEXT")
      self._ensure_column(connection, "interviewer_profiles", "description", "TEXT")
      self._ensure_column(connection, "interviewer_profiles", "avatar_url", "TEXT")
      self._ensure_column(connection, "interviewer_profiles", "tags_json", "TEXT")
      self._ensure_column(connection, "interviewer_profiles", "supported_roles_json", "TEXT")
      self._ensure_column(connection, "interviewer_profiles", "supported_modes_json", "TEXT")
      self._ensure_column(connection, "interviewer_profiles", "persona", "TEXT")
      self._ensure_column(connection, "interviewer_profiles", "prompt_strategy", "TEXT")
      self._ensure_column(connection, "interviewer_profiles", "interview_flow", "TEXT")

  def _ensure_column(self, connection: sqlite3.Connection, table_name: str, column_name: str, column_type: str) -> None:
    columns = {
      row["name"]
      for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name not in columns:
      connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")

  def _resolve_db_path(self, database_url: str) -> Path:
    normalized = database_url.strip()
    if not normalized:
      raise ConfigError("DATABASE_URL 为空，无法初始化 SQLite 持久化仓储。")
    if normalized.startswith("sqlite:///"):
      raw_path = normalized.removeprefix("sqlite:///")
      return Path(raw_path).expanduser().resolve()
    if normalized.startswith("sqlite://"):
      raise ConfigError("仅支持 sqlite:///absolute/or/relative/path 形式的 DATABASE_URL。")
    return Path(normalized).expanduser().resolve()

  def _now(self) -> str:
    return datetime.now(timezone.utc).isoformat()

  def _row_to_interviewer_profile(self, row: sqlite3.Row) -> InterviewerProfileEntry:
    return InterviewerProfileEntry(
      interviewer_id=row["interviewer_id"],
      type=row["type"],
      provider=row["provider"],
      name=row["name"],
      title=row["title"],
      description=row["description"],
      avatar_url=row["avatar_url"],
      tags=self._load_json_list(row["tags_json"]),
      supported_roles=self._load_json_list(row["supported_roles_json"]),
      supported_modes=self._load_json_list(row["supported_modes_json"]),
      persona=row["persona"],
      prompt_strategy=row["prompt_strategy"],
      skill_prompt=row["skill_prompt"],
      interview_flow=row["interview_flow"],
      avatar_api_key=row["avatar_api_key"],
      enabled=bool(row["enabled"]),
      created_at=row["created_at"],
      updated_at=row["updated_at"],
    )

  def _load_json_list(self, raw: Optional[str]) -> List[str]:
    if not raw:
      return []
    try:
      value = json.loads(raw)
    except json.JSONDecodeError:
      return []
    if not isinstance(value, list):
      return []
    return [str(item) for item in value if str(item).strip()]
