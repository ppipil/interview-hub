from __future__ import annotations

from dataclasses import replace
import tempfile
import unittest

from app.core.config import Settings
from app.core.errors import UpstreamServiceError, ValidationError
from app.models.api import (
  ConversationMessage,
  CreateSessionRequest,
  InterviewFeedback,
  Interviewer,
  SendMessageRequest,
  Session,
  UpsertAdminInterviewerRequest,
)
from app.models.persistence import InterviewerProfileEntry
from app.models.runtime import DoubaoRuntime, SecondMeVisitorChatRuntime
from app.repositories.in_memory import InMemorySessionRepository
from app.repositories.persistence import NullPersistenceRepository
from app.repositories.sqlite_persistence import SqlitePersistenceRepository
from app.services.admin_interviewers import AdminInterviewerService
from app.services.catalog import InterviewerCatalog
from app.services.interview import InterviewService
from app.services.interview_prompts import (
  build_avatar_bootstrap_prompt,
  build_avatar_follow_up_prompt,
  sanitize_interviewer_question,
)
from app.services.interview_provider import InterviewProviderRegistry, ProviderBootstrapResult


class FakeProvider:
  def __init__(self, provider_name: str) -> None:
    self.provider_name = provider_name
    self.bootstrap_calls = 0
    self.follow_up_calls = 0
    self.feedback_calls = 0

  async def bootstrap(self, interviewer, role, mode, total_rounds):
    _ = (interviewer, role, mode, total_rounds)
    self.bootstrap_calls += 1
    if self.provider_name == "doubao":
      runtime = DoubaoRuntime(provider="doubao", model="fake-model")
    else:
      runtime = SecondMeVisitorChatRuntime(
        provider="secondme_visitor",
        session_id="sess_visitor",
        access_token="token",
        api_key="sk-avatar",
        visitor_id="visitor_1",
        visitor_name="Test User",
      )
    return ProviderBootstrapResult(
      first_question_text=f"{self.provider_name}-question-1",
      runtime=runtime,
      channel=None,
    )

  async def follow_up(self, interviewer, session, runtime, channel, answer):
    _ = (interviewer, session, runtime, channel, answer)
    self.follow_up_calls += 1
    return f"{self.provider_name}-follow-up-{self.follow_up_calls}"

  async def generate_feedback(self, session, messages, runtime, channel):
    _ = (messages, runtime, channel)
    self.feedback_calls += 1
    return InterviewFeedback(
      sessionId=session.id,
      summary=f"{self.provider_name}-summary",
      dimensions=[
        {"key": "clarity", "label": "表达清晰度", "score": 4, "comment": "表达清楚"},
        {"key": "depth", "label": "专业深度", "score": 4, "comment": "深度不错"},
        {"key": "relevance", "label": "问题贴合度", "score": 5, "comment": "回答贴题"},
      ],
      strengths=["结构完整", "表达稳定"],
      improvements=["补充细节", "增加量化结果", "收尾更有力"],
      suggestedAnswer="先讲背景，再讲方案和结果。",
      roundReviews=[
        {
          "round": 1,
          "question": "Q1",
          "answer": "A1",
          "note": "回答完成度较高",
          "evaluation": "回答结构清楚，但结果量化不足。",
          "referenceAnswer": "可以先说明项目背景，再讲具体行动、技术取舍和最终结果。",
        }
      ],
      generatedAt="2026-04-20T00:00:00+00:00",
    )


class EmptyBootstrapProvider(FakeProvider):
  async def bootstrap(self, interviewer, role, mode, total_rounds):
    result = await super().bootstrap(interviewer, role, mode, total_rounds)
    return ProviderBootstrapResult(
      first_question_text=" ",
      runtime=result.runtime,
      channel=result.channel,
    )

  async def close(self, runtime, channel):
    _ = (runtime, channel)


class PromptEchoProvider(FakeProvider):
  async def bootstrap(self, interviewer, role, mode, total_rounds):
    result = await super().bootstrap(interviewer, role, mode, total_rounds)
    return ProviderBootstrapResult(
      first_question_text=build_avatar_bootstrap_prompt(interviewer, role, mode, total_rounds),
      runtime=result.runtime,
      channel=result.channel,
    )

  async def follow_up(self, interviewer, session, runtime, channel, answer):
    _ = (runtime, channel)
    return build_avatar_follow_up_prompt(
      interviewer=interviewer,
      role=session.role,
      mode=session.mode,
      next_round=session.currentRound + 1,
      total_rounds=session.totalRounds,
      answer=answer,
    )


class FakePersistenceRepository(NullPersistenceRepository):
  def __init__(self, profiles=None) -> None:
    self._profiles = profiles or []

  def list_interviewer_profiles(self, enabled_only=True):
    _ = enabled_only
    return self._profiles


def build_settings() -> Settings:
  return Settings(
    app_name="Interview Hub API",
    app_version="0.1.0",
    cors_origins=("http://127.0.0.1:5173",),
    cors_origin_regex="",
    database_url="",
    secondme_base_url="https://mindos-prek8s.mindverse.ai/gate/in",
    secondme_visitor_base_url="https://api.mindverse.com/gate/lab",
    secondme_api_key="legacy_key",
    secondme_avatar_share_code="legacy_share",
    secondme_app_client_id="client_id",
    secondme_app_client_secret="client_secret",
    secondme_avatar_api_key="sk-avatar",
    secondme_oauth_authorize_url="https://go.second-me.cn/oauth/",
    secondme_oauth_token_url="https://api.mindverse.com/gate/lab/api/oauth/token/code",
    secondme_oauth_redirect_uri="http://localhost:8000/api/auth/secondme/callback",
    secondme_oauth_scopes="userinfo chat.write avatar.read",
    secondme_oauth_state_secret="state-secret",
    secondme_avatar_api_key_name="Interview Hub Test",
    secondme_channel="web",
    secondme_ws_origin="https://second-me.cn",
    frontend_auth_success_url="http://localhost:5173/setup",
    frontend_auth_error_url="http://localhost:5173/setup",
    avatar_interviewer_id="secondme_tech",
    avatar_interviewer_name="SecondMe 技术面试官",
    avatar_interviewer_title="固定分身技术面试官",
    avatar_interviewer_description="负责发起技术模拟面试并持续追问项目细节。",
    avatar_interviewer_avatar_url="https://example.com/avatar.png",
    system_interviewer_id="system_tech",
    system_interviewer_name="系统技术面试官",
    system_interviewer_title="豆包系统面试官",
    system_interviewer_description="负责围绕岗位通用能力发起结构化技术追问。",
    system_interviewer_avatar_url="https://example.com/system.png",
    doubao_api_key="doubao-key",
    doubao_model="doubao-test-model",
    doubao_base_url="https://operator.las.cn-beijing.volces.com/api/v1",
    doubao_request_timeout_seconds=90.0,
    doubao_max_retries=2,
    request_timeout_seconds=30.0,
    websocket_reply_timeout_seconds=25.0,
    heartbeat_interval_seconds=15,
  )


class InterviewServiceTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self) -> None:
    settings = build_settings()
    self.catalog = InterviewerCatalog(settings)
    self.system_provider = FakeProvider("doubao")
    self.avatar_provider = FakeProvider("secondme_visitor")
    self.service = InterviewService(
      settings=settings,
      repository=InMemorySessionRepository(),
      persistence=NullPersistenceRepository(),
      catalog=self.catalog,
      providers=InterviewProviderRegistry([self.system_provider, self.avatar_provider]),
    )

  async def test_system_interviewer_flow_routes_to_doubao_provider(self) -> None:
    create_response = await self.service.create_session(
      payload=CreateSessionRequest(
        role="frontend",
        mode="guided",
        interviewerId="system_tech",
        totalRounds=2,
      )
    )
    self.assertEqual(create_response.interviewer.provider, "doubao")
    self.assertEqual(create_response.firstQuestion.content, "doubao-question-1")

    follow_up_response = await self.service.send_message(
      create_response.session.id,
      payload=SendMessageRequest(content="我的第一轮回答"),
    )
    self.assertEqual(follow_up_response.assistantMessage.content, "doubao-follow-up-1")

    complete_response = await self.service.send_message(
      create_response.session.id,
      payload=SendMessageRequest(content="我的第二轮回答"),
    )
    self.assertTrue(complete_response.shouldFetchFeedback)

    feedback = await self.service.get_feedback(create_response.session.id)
    self.assertEqual(feedback.summary, "doubao-summary")
    self.assertEqual(self.system_provider.bootstrap_calls, 1)
    self.assertEqual(self.system_provider.follow_up_calls, 1)
    self.assertEqual(self.system_provider.feedback_calls, 1)
    self.assertEqual(self.avatar_provider.bootstrap_calls, 0)

  async def test_avatar_interviewer_flow_routes_to_secondme_provider(self) -> None:
    create_response = await self.service.create_session(
      payload=CreateSessionRequest(
        role="backend",
        mode="real",
        interviewerId="secondme_tech",
        totalRounds=1,
      )
    )
    self.assertEqual(create_response.interviewer.provider, "secondme_visitor")
    self.assertEqual(create_response.firstQuestion.content, "secondme_visitor-question-1")

    complete_response = await self.service.send_message(
      create_response.session.id,
      payload=SendMessageRequest(content="这是我的回答"),
    )
    self.assertTrue(complete_response.shouldFetchFeedback)

    feedback = await self.service.get_feedback(create_response.session.id)
    self.assertEqual(feedback.summary, "secondme_visitor-summary")
    self.assertEqual(self.avatar_provider.bootstrap_calls, 1)
    self.assertEqual(self.avatar_provider.feedback_calls, 1)

  async def test_empty_first_question_is_rejected(self) -> None:
    service = InterviewService(
      settings=build_settings(),
      repository=InMemorySessionRepository(),
      persistence=NullPersistenceRepository(),
      catalog=self.catalog,
      providers=InterviewProviderRegistry([EmptyBootstrapProvider("doubao"), self.avatar_provider]),
    )

    with self.assertRaises(UpstreamServiceError) as ctx:
      await service.create_session(
        payload=CreateSessionRequest(
          role="frontend",
          mode="guided",
          interviewerId="system_tech",
          totalRounds=2,
        )
      )

    self.assertEqual(ctx.exception.code, "INTERVIEWER_EMPTY_FIRST_QUESTION")

  async def test_internal_prompt_echo_is_sanitized_before_returning(self) -> None:
    service = InterviewService(
      settings=build_settings(),
      repository=InMemorySessionRepository(),
      persistence=NullPersistenceRepository(),
      catalog=self.catalog,
      providers=InterviewProviderRegistry([PromptEchoProvider("doubao"), self.avatar_provider]),
    )

    create_response = await service.create_session(
      payload=CreateSessionRequest(
        role="frontend",
        mode="guided",
        interviewerId="system_tech",
        totalRounds=3,
      )
    )
    self.assertEqual(
      create_response.firstQuestion.content,
      "请简要介绍一下你的背景，以及最近一个与前端工程师岗位相关的项目经历。",
    )
    self.assertNotIn("【当前阶段任务卡】", create_response.firstQuestion.content)

    follow_up_response = await service.send_message(
      create_response.session.id,
      payload=SendMessageRequest(content="我做过一个中后台项目。"),
    )

    self.assertEqual(
      follow_up_response.assistantMessage.content,
      "请结合你的前端工程师经历，说明一个关键项目难点、你的解决思路和最终结果。",
    )
    self.assertNotIn("候选人刚才", follow_up_response.assistantMessage.content)

  async def test_round_validation_rejects_out_of_range_values(self) -> None:
    with self.assertRaises(ValidationError):
      await self.service.create_session(
        payload=CreateSessionRequest(
          role="frontend",
          mode="guided",
          interviewerId="system_tech",
          totalRounds=11,
        )
      )

  async def test_database_profile_skill_is_exposed_on_interviewer(self) -> None:
    settings = build_settings()
    persistence = FakePersistenceRepository(
      profiles=[
        InterviewerProfileEntry(
          interviewer_id="secondme_tech",
          skill_prompt="只追问候选人的项目复杂度和量化结果。",
          avatar_api_key="sk-profile",
          enabled=True,
          created_at="2026-04-21T00:00:00+00:00",
          updated_at="2026-04-21T00:00:00+00:00",
        )
      ]
    )
    service = InterviewService(
      settings=settings,
      repository=InMemorySessionRepository(),
      persistence=persistence,
      catalog=InterviewerCatalog(settings),
      providers=InterviewProviderRegistry([FakeProvider("doubao"), FakeProvider("secondme_visitor")]),
    )

    interviewers = service.list_interviewers()
    avatar = next(item for item in interviewers if item.id == "secondme_tech")

    self.assertEqual(avatar.skillPrompt, "只追问候选人的项目复杂度和量化结果。")

  async def test_database_profile_skill_is_included_in_avatar_prompt(self) -> None:
    settings = build_settings()
    profile_skill = "只追问候选人的项目复杂度和量化结果。"
    persistence = FakePersistenceRepository(
      profiles=[
        InterviewerProfileEntry(
          interviewer_id="secondme_tech",
          skill_prompt=profile_skill,
          interview_flow=(
            "第1阶段：自我介绍与背景了解\n"
            "问题：请简要介绍背景。\n\n"
            "第2阶段：算法与数据结构\n"
            "问题：链表中间节点、CAP 定理。\n\n"
            "第3阶段：系统设计\n"
            "问题：设计秒杀系统。"
          ),
          avatar_api_key="sk-profile",
          enabled=True,
          created_at="2026-04-21T00:00:00+00:00",
          updated_at="2026-04-21T00:00:00+00:00",
        )
      ]
    )
    interviewer = InterviewerCatalog(settings).get(
      "secondme_tech",
      "backend",
      "real",
      profiles=persistence.list_interviewer_profiles(),
    )

    prompt = build_avatar_bootstrap_prompt(
      interviewer=interviewer,
      role="backend",
      mode="real",
      total_rounds=3,
    )

    self.assertIn("【Interview Hub 面试官 Skill】", prompt)
    self.assertIn(profile_skill, prompt)
    self.assertIn("【当前阶段任务卡】", prompt)
    self.assertIn("第1阶段：自我介绍与背景了解", prompt)
    self.assertIn("当前阶段任务卡是流程硬约束", prompt)

    follow_up_prompt = build_avatar_follow_up_prompt(
      interviewer=interviewer,
      role="backend",
      mode="real",
      next_round=2,
      total_rounds=3,
      answer="我做过高并发项目。",
    )
    self.assertIn("第2阶段：算法与数据结构", follow_up_prompt)
    self.assertIn("不能跳到其他阶段", follow_up_prompt)

  def test_prompt_echo_sanitizer_extracts_stage_question(self) -> None:
    leaked_prompt = (
      "【Interview Hub 面试官 Skill】\n"
      "阿里后端面试官分身\n"
      "【Skill 结束】\n"
      "【当前阶段任务卡】\n"
      "当前轮次：第 1 / 5 轮。\n"
      "第1阶段：自我介绍与背景了解\n"
      "问题：\n"
      "“请简要介绍一下你的背景和之前的工作经历。”\n"
      "“你在前一个项目中使用的技术栈是什么？有什么技术难题？”\n"
      "硬性规则：只能执行本阶段任务；不能跳到其他阶段；只能问一个问题。\n"
      "【任务卡结束】"
    )

    self.assertEqual(
      sanitize_interviewer_question(leaked_prompt, fallback="请介绍一下你自己。"),
      "请简要介绍一下你的背景和之前的工作经历。",
    )


class SqlitePersistenceRepositoryTests(unittest.TestCase):
  def test_sqlite_repository_persists_session_feedback_and_question_bank(self) -> None:
    with tempfile.TemporaryDirectory() as tempdir:
      repo = SqlitePersistenceRepository(f"sqlite:///{tempdir}/interview-hub.sqlite3")
      repo.sync_interviewers(self._build_interviewers())
      repo.upsert_interviewer_secret("secondme_tech", "sk-avatar-from-db")
      with repo._connect() as connection:
        connection.execute(
          """
          INSERT INTO interviewer_profiles (
            interviewer_id, skill_prompt, interview_flow, avatar_api_key, enabled, created_at, updated_at
          )
          VALUES (?, ?, ?, ?, ?, ?, ?)
          """,
          (
            "system_tech",
            "请重点考察候选人的项目拆解能力。",
            "第1阶段：项目背景\n第2阶段：项目拆解",
            "sk-system-profile",
            1,
            "2026-04-21T00:00:00+00:00",
            "2026-04-21T00:00:00+00:00",
          ),
        )

      session = Session(
        id="session_1",
        role="frontend",
        mode="guided",
        interviewerId="system_tech",
        status="completed",
        currentRound=2,
        totalRounds=2,
        startedAt="2026-04-20T00:00:00+00:00",
        finishedAt="2026-04-20T00:10:00+00:00",
      )
      message = ConversationMessage(
        id="message_1",
        role="assistant",
        content="请介绍一下你最近做过的前端项目。",
        round=1,
        createdAt="2026-04-20T00:00:01+00:00",
      )
      feedback = InterviewFeedback(
        sessionId=session.id,
        summary="整体不错",
        dimensions=[
          {"key": "clarity", "label": "表达清晰度", "score": 4, "comment": "表达清楚"},
          {"key": "depth", "label": "专业深度", "score": 4, "comment": "深度不错"},
          {"key": "relevance", "label": "问题贴合度", "score": 5, "comment": "回答贴题"},
        ],
        strengths=["结构完整", "表达稳定"],
        improvements=["补充细节", "增加量化结果", "收尾更有力"],
        suggestedAnswer="先讲背景，再讲方案。",
        roundReviews=[
          {
            "round": 1,
            "question": "Q1",
            "answer": "A1",
            "note": "回答完成度较高",
            "evaluation": "回答结构清楚，但结果量化不足。",
            "referenceAnswer": "可以先说明项目背景，再讲具体行动、技术取舍和最终结果。",
          }
        ],
        generatedAt="2026-04-20T00:20:00+00:00",
      )

      repo.save_session(session)
      repo.append_message(session.id, message)
      repo.save_feedback(feedback)
      repo.add_question(
        role="frontend",
        mode="guided",
        interviewer_type="system",
        provider="doubao",
        prompt_strategy="system_structured",
        question=message.content,
        source_session_id=session.id,
        created_at=message.createdAt,
      )

      stored_feedback = repo.get_feedback(session.id)
      stored_questions = repo.list_questions(role="frontend", provider="doubao")
      stored_secret = repo.get_interviewer_secret("secondme_tech")
      stored_profiles = repo.list_interviewer_profiles()

      self.assertIsNotNone(stored_feedback)
      self.assertEqual(stored_feedback.summary, "整体不错")
      self.assertEqual(len(stored_questions), 1)
      self.assertEqual(stored_questions[0].question, message.content)
      self.assertIsNotNone(stored_secret)
      self.assertEqual(stored_secret.avatar_api_key, "sk-avatar-from-db")
      self.assertEqual(len(stored_profiles), 1)
      self.assertEqual(stored_profiles[0].skill_prompt, "请重点考察候选人的项目拆解能力。")
      self.assertEqual(stored_profiles[0].interview_flow, "第1阶段：项目背景\n第2阶段：项目拆解")

  def test_admin_interviewer_service_crud_profiles(self) -> None:
    with tempfile.TemporaryDirectory() as tempdir:
      settings = replace(build_settings(), database_url=f"sqlite:///{tempdir}/interview-hub.sqlite3")
      repo = SqlitePersistenceRepository(settings.database_url)
      catalog = InterviewerCatalog(settings)
      service = AdminInterviewerService(settings=settings, catalog=catalog, persistence=repo)

      created = service.upsert_interviewer(
        UpsertAdminInterviewerRequest(
          id="avatar_product_mentor",
          type="avatar",
          provider="secondme_visitor",
          name="产品分身面试官",
          title="产品案例深挖官",
          description="专门追问产品判断、指标拆解和复盘能力。",
          avatarUrl="",
          tags=["SecondMe", "产品"],
          supportedRoles=["product_manager"],
          supportedModes=["guided", "real"],
          persona="语气直接但不压迫。",
          promptStrategy="avatar_skill",
          skillPrompt="重点追问候选人的产品决策依据和指标定义。",
          interviewFlow="第1阶段：产品背景\n第2阶段：指标拆解",
          avatarApiKey="sk-custom-avatar-key",
          enabled=True,
        )
      )

      self.assertEqual(created.id, "avatar_product_mentor")
      self.assertTrue(created.hasAvatarApiKey)
      self.assertEqual(created.avatarApiKey, "sk-custom-avatar-key")
      self.assertEqual(created.avatarApiKeyMasked, "sk-cu...-key")
      self.assertEqual(created.skillPrompt, "重点追问候选人的产品决策依据和指标定义。")
      self.assertEqual(created.interviewFlow, "第1阶段：产品背景\n第2阶段：指标拆解")

      listed = service.list_interviewers()
      custom = next(item for item in listed if item.id == "avatar_product_mentor")
      self.assertEqual(custom.supportedRoles, ["product_manager"])

      updated = service.upsert_interviewer(
        UpsertAdminInterviewerRequest(
          id="avatar_product_mentor",
          type="avatar",
          provider="secondme_visitor",
          name="产品分身面试官",
          title="产品案例深挖官",
          description="专门追问产品判断、指标拆解和复盘能力。",
          avatarUrl="",
          tags=["SecondMe", "产品"],
          supportedRoles=["product_manager"],
          supportedModes=["guided", "real"],
          persona="语气直接但不压迫。",
          promptStrategy="avatar_skill",
          skillPrompt="更新后的 skill：继续追问取舍和量化结果。",
          interviewFlow="第1阶段：产品背景\n第2阶段：方案取舍",
          enabled=True,
        )
      )

      self.assertTrue(updated.hasAvatarApiKey)
      self.assertEqual(updated.avatarApiKey, "sk-custom-avatar-key")
      self.assertEqual(updated.skillPrompt, "更新后的 skill：继续追问取舍和量化结果。")
      self.assertEqual(updated.interviewFlow, "第1阶段：产品背景\n第2阶段：方案取舍")
      service.delete_interviewer("avatar_product_mentor")
      self.assertFalse(repo.list_interviewer_profiles(enabled_only=False))

  def _build_interviewers(self):
    return [
      Interviewer(
        id="system_tech",
        type="system",
        provider="doubao",
        name="系统技术面试官",
        title="豆包系统面试官",
        description="负责围绕岗位通用能力发起结构化技术追问。",
        avatarUrl="https://example.com/system.png",
        tags=["System", "Doubao"],
        supportedRoles=["frontend", "backend"],
        supportedModes=["guided", "real"],
        persona="系统面试官",
        promptStrategy="system_structured",
      )
    ]


if __name__ == "__main__":
  unittest.main()
