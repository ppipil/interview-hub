from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Iterator, List, Optional

from app.core.errors import ConfigError
from app.models.api import ConversationMessage, InterviewFeedback, InterviewMode, InterviewRole, InterviewStageKey, Interviewer, Session
from app.models.persistence import (
  FormalQuestionBankEntry,
  FormalQuestionBankWrite,
  FormalQuestionUsageEntry,
  InterviewerProfileEntry,
  InterviewerSecretEntry,
  QuestionBankEntry,
  SecondMeConnectionEntry,
)

try:
  import psycopg
  from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - only hit when Postgres dependency is absent
  psycopg = None
  dict_row = None


class PostgresPersistenceRepository:
  def __init__(self, database_url: str) -> None:
    if psycopg is None or dict_row is None:
      raise ConfigError(
        "当前环境缺少 Postgres 驱动，请先安装 psycopg 后再使用 Neon/Postgres 持久化。",
      )

    self._dsn = self._resolve_dsn(database_url)
    self._initialize()

  def sync_interviewers(self, interviewers: List[Interviewer]) -> None:
    with self._connect() as connection:
      with connection.cursor() as cursor:
        cursor.executemany(
          """
          INSERT INTO interviewers (
            id, type, provider, prompt_strategy, name, title, description,
            avatar_url, tags_json, supported_roles_json, supported_modes_json,
            persona, skill_prompt, updated_at
          )
          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
        VALUES (%s, %s, %s, %s)
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
        WHERE interviewer_id = %s
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
      query.append("WHERE enabled = TRUE")
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
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
          profile.enabled,
          profile.created_at,
          profile.updated_at,
        ),
      )

  def delete_interviewer_profile(self, interviewer_id: str) -> bool:
    with self._connect() as connection:
      cursor = connection.execute(
        "DELETE FROM interviewer_profiles WHERE interviewer_id = %s",
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
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
        INSERT INTO conversation_messages (
          id, session_id, role, content, round, created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT(id) DO UPDATE SET
          session_id=excluded.session_id,
          role=excluded.role,
          content=excluded.content,
          round=excluded.round,
          created_at=excluded.created_at
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
        VALUES (%s, %s, %s, %s)
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
        "SELECT payload_json FROM interview_feedback WHERE session_id = %s",
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
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
      query.append("AND role = %s")
      params.append(role)
    if mode:
      query.append("AND mode = %s")
      params.append(mode)
    if provider:
      query.append("AND provider = %s")
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

  def seed_formal_questions(self, questions: List[FormalQuestionBankWrite]) -> None:
    if not questions:
      return
    with self._connect() as connection:
      self._insert_formal_questions(connection, questions)

  def replace_interviewer_question_bank(self, interviewer_id: str, questions: List[FormalQuestionBankWrite]) -> None:
    with self._connect() as connection:
      connection.execute(
        "DELETE FROM formal_question_bank WHERE scope_type = %s AND interviewer_id = %s",
        ("interviewer", interviewer_id),
      )
      self._insert_formal_questions(connection, questions)

  def replace_global_question_bank(self, role: InterviewRole, questions: List[FormalQuestionBankWrite]) -> None:
    with self._connect() as connection:
      connection.execute(
        "DELETE FROM formal_question_bank WHERE scope_type = %s AND role = %s",
        ("global", role),
      )
      self._insert_formal_questions(connection, questions)

  def list_formal_questions(
    self,
    *,
    scope_type: Optional[str] = None,
    interviewer_id: Optional[str] = None,
    role: Optional[InterviewRole] = None,
    stage_key: Optional[InterviewStageKey] = None,
    enabled_only: bool = True,
  ) -> List[FormalQuestionBankEntry]:
    query = [
      """
      SELECT
        id, scope_type, interviewer_id, role, stage_key, question, reference_answer,
        tags_json, enabled, sort_order, created_at, updated_at
      FROM formal_question_bank
      WHERE 1 = 1
      """
    ]
    params: List[str] = []
    if enabled_only:
      query.append("AND enabled = TRUE")
    if scope_type:
      query.append("AND scope_type = %s")
      params.append(scope_type)
    if interviewer_id:
      query.append("AND interviewer_id = %s")
      params.append(interviewer_id)
    if role:
      query.append("AND role = %s")
      params.append(role)
    if stage_key:
      query.append("AND stage_key = %s")
      params.append(stage_key)
    query.append("ORDER BY sort_order ASC, created_at ASC")

    with self._connect() as connection:
      rows = connection.execute("\n".join(query), params).fetchall()

    return [self._row_to_formal_question(row) for row in rows]

  def save_formal_question_usage(self, usage: FormalQuestionUsageEntry) -> None:
    with self._connect() as connection:
      connection.execute(
        """
        INSERT INTO formal_question_usage (
          message_id, session_id, question_id, interviewer_id, role, round_number,
          stage_key, source_scope, used_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(message_id) DO UPDATE SET
          session_id=excluded.session_id,
          question_id=excluded.question_id,
          interviewer_id=excluded.interviewer_id,
          role=excluded.role,
          round_number=excluded.round_number,
          stage_key=excluded.stage_key,
          source_scope=excluded.source_scope,
          used_at=excluded.used_at
        """,
        (
          usage.message_id,
          usage.session_id,
          usage.question_id,
          usage.interviewer_id,
          usage.role,
          usage.round_number,
          usage.stage_key,
          usage.source_scope,
          usage.used_at,
        ),
      )

  def list_formal_question_usage(self, session_id: str) -> List[FormalQuestionUsageEntry]:
    with self._connect() as connection:
      rows = connection.execute(
        """
        SELECT
          message_id, session_id, question_id, interviewer_id, role, round_number,
          stage_key, source_scope, used_at
        FROM formal_question_usage
        WHERE session_id = %s
        ORDER BY round_number ASC, used_at ASC
        """,
        (session_id,),
      ).fetchall()
    return [self._row_to_formal_question_usage(row) for row in rows]

  @contextmanager
  def _connect(self) -> Iterator[Any]:
    assert psycopg is not None
    assert dict_row is not None
    connection = psycopg.connect(self._dsn, row_factory=dict_row)
    try:
      yield connection
      connection.commit()
    finally:
      connection.close()

  def _initialize(self) -> None:
    with self._connect() as connection:
      connection.execute(
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
        )
        """
      )
      connection.execute("ALTER TABLE interviewers ADD COLUMN IF NOT EXISTS skill_prompt TEXT")
      connection.execute(
        """
        CREATE TABLE IF NOT EXISTS interviewer_secrets (
          interviewer_id TEXT PRIMARY KEY,
          avatar_api_key TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
        """
      )
      connection.execute(
        """
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
          enabled BOOLEAN NOT NULL DEFAULT TRUE,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
        """
      )
      connection.execute("ALTER TABLE interviewer_profiles ADD COLUMN IF NOT EXISTS type TEXT")
      connection.execute("ALTER TABLE interviewer_profiles ADD COLUMN IF NOT EXISTS provider TEXT")
      connection.execute("ALTER TABLE interviewer_profiles ADD COLUMN IF NOT EXISTS name TEXT")
      connection.execute("ALTER TABLE interviewer_profiles ADD COLUMN IF NOT EXISTS title TEXT")
      connection.execute("ALTER TABLE interviewer_profiles ADD COLUMN IF NOT EXISTS description TEXT")
      connection.execute("ALTER TABLE interviewer_profiles ADD COLUMN IF NOT EXISTS avatar_url TEXT")
      connection.execute("ALTER TABLE interviewer_profiles ADD COLUMN IF NOT EXISTS tags_json TEXT")
      connection.execute("ALTER TABLE interviewer_profiles ADD COLUMN IF NOT EXISTS supported_roles_json TEXT")
      connection.execute("ALTER TABLE interviewer_profiles ADD COLUMN IF NOT EXISTS supported_modes_json TEXT")
      connection.execute("ALTER TABLE interviewer_profiles ADD COLUMN IF NOT EXISTS persona TEXT")
      connection.execute("ALTER TABLE interviewer_profiles ADD COLUMN IF NOT EXISTS prompt_strategy TEXT")
      connection.execute("ALTER TABLE interviewer_profiles ADD COLUMN IF NOT EXISTS interview_flow TEXT")
      connection.execute(
        """
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
        )
        """
      )
      connection.execute(
        """
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
        )
        """
      )
      connection.execute(
        """
        CREATE TABLE IF NOT EXISTS conversation_messages (
          id TEXT PRIMARY KEY,
          session_id TEXT NOT NULL,
          role TEXT NOT NULL,
          content TEXT NOT NULL,
          round INTEGER NOT NULL,
          created_at TEXT NOT NULL
        )
        """
      )
      connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_conversation_messages_session
          ON conversation_messages(session_id, created_at)
        """
      )
      connection.execute(
        """
        CREATE TABLE IF NOT EXISTS interview_feedback (
          session_id TEXT PRIMARY KEY,
          payload_json TEXT NOT NULL,
          generated_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
        """
      )
      connection.execute(
        """
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
        )
        """
      )
      connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_question_bank_lookup
          ON question_bank(role, mode, provider, created_at DESC)
        """
      )
      connection.execute(
        """
        CREATE TABLE IF NOT EXISTS formal_question_bank (
          id TEXT PRIMARY KEY,
          scope_type TEXT NOT NULL,
          interviewer_id TEXT,
          role TEXT NOT NULL,
          stage_key TEXT NOT NULL,
          question TEXT NOT NULL,
          reference_answer TEXT,
          tags_json TEXT NOT NULL,
          enabled BOOLEAN NOT NULL DEFAULT TRUE,
          sort_order INTEGER NOT NULL DEFAULT 100,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
        """
      )
      connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_formal_question_lookup
          ON formal_question_bank(scope_type, interviewer_id, role, stage_key, enabled, sort_order)
        """
      )
      connection.execute(
        """
        CREATE TABLE IF NOT EXISTS formal_question_usage (
          message_id TEXT PRIMARY KEY,
          session_id TEXT NOT NULL,
          question_id TEXT NOT NULL,
          interviewer_id TEXT NOT NULL,
          role TEXT NOT NULL,
          round_number INTEGER NOT NULL,
          stage_key TEXT NOT NULL,
          source_scope TEXT NOT NULL,
          used_at TEXT NOT NULL
        )
        """
      )
      connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_formal_question_usage_session
          ON formal_question_usage(session_id, round_number)
        """
      )

  def _resolve_dsn(self, database_url: str) -> str:
    normalized = database_url.strip()
    if not normalized:
      raise ConfigError("DATABASE_URL 为空，无法初始化 Postgres 持久化仓储。")
    if normalized.startswith("jdbc:postgresql://"):
      return normalized.removeprefix("jdbc:")
    if normalized.startswith("postgresql://") or normalized.startswith("postgres://"):
      return normalized
    raise ConfigError("仅支持 postgresql://... 或 jdbc:postgresql://... 形式的 DATABASE_URL。")

  def _now(self) -> str:
    return datetime.now(timezone.utc).isoformat()

  def _row_to_interviewer_profile(self, row: dict[str, Any]) -> InterviewerProfileEntry:
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

  def _insert_formal_questions(self, connection: Any, questions: List[FormalQuestionBankWrite]) -> None:
    if not questions:
      return
    now = self._now()
    with connection.cursor() as cursor:
      cursor.executemany(
        """
        INSERT INTO formal_question_bank (
          id, scope_type, interviewer_id, role, stage_key, question, reference_answer,
          tags_json, enabled, sort_order, created_at, updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(id) DO UPDATE SET
          question=excluded.question,
          reference_answer=excluded.reference_answer,
          tags_json=excluded.tags_json,
          enabled=excluded.enabled,
          sort_order=excluded.sort_order,
          updated_at=excluded.updated_at
        """,
        [
          (
            self._formal_question_id(question),
            question.scope_type,
            question.interviewer_id,
            question.role,
            question.stage_key,
            question.question.strip(),
            question.reference_answer.strip() if question.reference_answer else None,
            json.dumps(question.tags or [], ensure_ascii=False),
            question.enabled,
            question.sort_order,
            now,
            now,
          )
          for question in questions
        ],
      )

  def _formal_question_id(self, question: FormalQuestionBankWrite) -> str:
    return hashlib.sha256(
      "|".join(
        [
          question.scope_type,
          question.interviewer_id or "",
          question.role,
          question.stage_key,
          str(question.sort_order),
          question.question.strip(),
        ]
      ).encode("utf-8"),
    ).hexdigest()

  def _row_to_formal_question(self, row: dict[str, Any]) -> FormalQuestionBankEntry:
    return FormalQuestionBankEntry(
      id=row["id"],
      scope_type=row["scope_type"],
      interviewer_id=row["interviewer_id"],
      role=row["role"],
      stage_key=row["stage_key"],
      question=row["question"],
      reference_answer=row["reference_answer"],
      tags=self._load_json_list(row["tags_json"]),
      enabled=bool(row["enabled"]),
      sort_order=int(row["sort_order"]),
      created_at=row["created_at"],
      updated_at=row["updated_at"],
    )

  def _row_to_formal_question_usage(self, row: dict[str, Any]) -> FormalQuestionUsageEntry:
    return FormalQuestionUsageEntry(
      message_id=row["message_id"],
      session_id=row["session_id"],
      question_id=row["question_id"],
      interviewer_id=row["interviewer_id"],
      role=row["role"],
      round_number=int(row["round_number"]),
      stage_key=row["stage_key"],
      source_scope=row["source_scope"],
      used_at=row["used_at"],
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
