from __future__ import annotations

from dataclasses import replace
import tempfile
import unittest

from app.core.config import Settings
from app.core.errors import ValidationError
from app.models.api import (
  ConversationMessage,
  CreateSessionRequest,
  InterviewFeedback,
  Interviewer,
  SendMessageRequest,
  Session,
  UpsertAdminInterviewerRequest,
  UpsertGlobalQuestionBankRequest,
)
from app.models.persistence import (
  FormalQuestionBankEntry,
  FormalQuestionBankWrite,
  FormalQuestionUsageEntry,
  InterviewerProfileEntry,
)
from app.models.runtime import DoubaoRuntime, SecondMeVisitorChatRuntime
from app.repositories.in_memory import InMemorySessionRepository
from app.repositories.persistence import NullPersistenceRepository
from app.repositories.sqlite_persistence import SqlitePersistenceRepository
from app.services.admin_interviewers import AdminInterviewerService
from app.services.catalog import InterviewerCatalog
from app.services.feedback import FeedbackService
from app.services.interview import InterviewService
from app.services.interview_prompts import (
  build_avatar_bootstrap_prompt,
  build_avatar_follow_up_prompt,
  build_system_follow_up_prompt,
  sanitize_interviewer_question,
)
from app.services.interview_provider import InterviewProviderRegistry, ProviderBootstrapResult


class FakeProvider:
  def __init__(self, provider_name: str) -> None:
    self.provider_name = provider_name
    self.bootstrap_calls = 0
    self.follow_up_calls = 0
    self.feedback_calls = 0
    self.last_follow_up_messages = []

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

  async def follow_up(self, interviewer, session, runtime, channel, answer, messages):
    _ = (interviewer, session, runtime, channel, answer)
    self.follow_up_calls += 1
    self.last_follow_up_messages = messages
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


class FakePersistenceRepository(NullPersistenceRepository):
  def __init__(self, profiles=None, formal_questions=None) -> None:
    self._profiles = profiles or []
    self._formal_questions = list(formal_questions or [])
    self._usage = []

  def list_interviewer_profiles(self, enabled_only=True):
    _ = enabled_only
    return self._profiles

  def seed_formal_questions(self, questions):
    existing = {self._formal_question_key(item) for item in self._formal_questions}
    for question in questions:
      if self._formal_question_key(question) in existing:
        continue
      self._formal_questions.append(question)
      existing.add(self._formal_question_key(question))

  def list_formal_questions(self, *, scope_type=None, interviewer_id=None, role=None, stage_key=None, enabled_only=True):
    rows = self._formal_questions
    if scope_type:
      rows = [item for item in rows if item.scope_type == scope_type]
    if interviewer_id:
      rows = [item for item in rows if item.interviewer_id == interviewer_id]
    if role:
      rows = [item for item in rows if item.role == role]
    if stage_key:
      rows = [item for item in rows if item.stage_key == stage_key]
    if enabled_only:
      rows = [item for item in rows if item.enabled]
    return [
      FormalQuestionBankEntry(
        id=self._formal_question_key(item),
        scope_type=item.scope_type,
        interviewer_id=item.interviewer_id,
        role=item.role,
        stage_key=item.stage_key,
        question=item.question,
        reference_answer=item.reference_answer,
        tags=item.tags,
        enabled=item.enabled,
        sort_order=item.sort_order,
        created_at="2026-04-20T00:00:00+00:00",
        updated_at="2026-04-20T00:00:00+00:00",
      )
      for item in sorted(rows, key=lambda current: current.sort_order)
    ]

  def save_formal_question_usage(self, usage):
    self._usage.append(usage)

  def list_formal_question_usage(self, session_id):
    return [item for item in self._usage if item.session_id == session_id]

  def replace_interviewer_question_bank(self, interviewer_id, questions):
    self._formal_questions = [
      item
      for item in self._formal_questions
      if not (item.scope_type == "interviewer" and item.interviewer_id == interviewer_id)
    ]
    self._formal_questions.extend(questions)

  def replace_global_question_bank(self, role, questions):
    self._formal_questions = [
      item for item in self._formal_questions if not (item.scope_type == "global" and item.role == role)
    ]
    self._formal_questions.extend(questions)

  def _formal_question_key(self, question):
    return "|".join(
      [
        question.scope_type,
        question.interviewer_id or "",
        question.role,
        question.stage_key,
        str(question.sort_order),
        question.question,
      ]
    )


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
    self.persistence = FakePersistenceRepository()
    self.service = InterviewService(
      settings=settings,
      repository=InMemorySessionRepository(),
      persistence=self.persistence,
      catalog=self.catalog,
      providers=InterviewProviderRegistry([self.system_provider, self.avatar_provider]),
    )
    self.service.sync_catalog()

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
    self.assertEqual(
      create_response.firstQuestion.content,
      "请先做一个简短的自我介绍，并讲一个最近最能体现你前端能力的页面或应用。",
    )

    follow_up_response = await self.service.send_message(
      create_response.session.id,
      payload=SendMessageRequest(content="我的第一轮回答"),
    )
    self.assertEqual(
      follow_up_response.assistantMessage.content,
      "请解释一个你最熟悉的前端基础知识点，并说明它的核心原理、适用场景和常见问题。",
    )

    complete_response = await self.service.send_message(
      create_response.session.id,
      payload=SendMessageRequest(content="我的第二轮回答"),
    )
    self.assertTrue(complete_response.shouldFetchFeedback)

    feedback = await self.service.get_feedback(create_response.session.id)
    self.assertEqual(feedback.summary, "doubao-summary")
    self.assertEqual(self.system_provider.bootstrap_calls, 1)
    self.assertEqual(self.system_provider.follow_up_calls, 0)
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
    self.assertEqual(
      create_response.firstQuestion.content,
      "请先做一个简短的自我介绍，并讲一个最近最能体现你后端能力的服务或系统。",
    )

    complete_response = await self.service.send_message(
      create_response.session.id,
      payload=SendMessageRequest(content="这是我的回答"),
    )
    self.assertTrue(complete_response.shouldFetchFeedback)

    feedback = await self.service.get_feedback(create_response.session.id)
    self.assertEqual(feedback.summary, "secondme_visitor-summary")
    self.assertEqual(self.avatar_provider.bootstrap_calls, 1)
    self.assertEqual(self.avatar_provider.feedback_calls, 1)

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

  async def test_incomplete_interviewer_bank_falls_back_to_global_questions(self) -> None:
    create_response = await self.service.create_session(
      payload=CreateSessionRequest(
        role="backend",
        mode="real",
        interviewerId="secondme_tech",
        totalRounds=6,
      )
    )
    self.assertEqual(
      create_response.firstQuestion.content,
      "请先做一个简短的自我介绍，并讲一个最近最能体现你后端能力的服务或系统。",
    )

    follow_up_response = await self.service.send_message(
      create_response.session.id,
      payload=SendMessageRequest(content="我最近做过订单系统。"),
    )
    self.assertEqual(
      follow_up_response.assistantMessage.content,
      "如果让你用 HashMap 证明自己的 Java 基础，你会怎么讲它的底层实现、扩容机制，以及 1.8 为什么引入红黑树？",
    )

    third_round_response = await self.service.send_message(
      create_response.session.id,
      payload=SendMessageRequest(content="我也做过缓存优化。"),
    )
    self.assertEqual(
      third_round_response.assistantMessage.content,
      "如果从数据库原理里挑一道高频题，你会怎么回答为什么 MySQL 索引使用 B+ 树，而不是 B 树或红黑树？",
    )

    fourth_round_response = await self.service.send_message(
      create_response.session.id,
      payload=SendMessageRequest(content="我排查过慢查询。"),
    )
    self.assertEqual(
      fourth_round_response.assistantMessage.content,
      "你会怎么系统解释缓存穿透、缓存击穿、缓存雪崩，以及各自的解决方案？",
    )

    fallback_response = await self.service.send_message(
      create_response.session.id,
      payload=SendMessageRequest(content="我也了解网络协议。"),
    )
    self.assertEqual(
      fallback_response.assistantMessage.content,
      "HashMap 的底层实现、扩容机制，以及为什么 1.8 之后引入红黑树？",
    )

  async def test_same_session_does_not_repeat_formal_questions(self) -> None:
    create_response = await self.service.create_session(
      payload=CreateSessionRequest(
        role="backend",
        mode="guided",
        interviewerId="system_tech",
        totalRounds=8,
      )
    )

    assistant_questions = [create_response.firstQuestion.content]
    session_id = create_response.session.id
    for round_number in range(2, 9):
      response = await self.service.send_message(
        session_id,
        payload=SendMessageRequest(content=f"第 {round_number - 1} 轮回答"),
      )
      if response.assistantMessage:
        assistant_questions.append(response.assistantMessage.content)

    self.assertEqual(len(assistant_questions), len(set(assistant_questions)))

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

  def test_system_follow_up_prompt_includes_history_and_dedup_rules(self) -> None:
    settings = build_settings()
    interviewer = InterviewerCatalog(settings).get("system_tech", "backend", "real")
    messages = [
      ConversationMessage(
        id="m1",
        role="assistant",
        content="请介绍一下你最近做过的高并发项目。",
        round=1,
        createdAt="2026-04-21T00:00:00+00:00",
      ),
      ConversationMessage(
        id="m2",
        role="user",
        content="我做过订单系统。",
        round=1,
        createdAt="2026-04-21T00:01:00+00:00",
      ),
    ]

    prompt = build_system_follow_up_prompt(
      interviewer=interviewer,
      role="backend",
      mode="real",
      next_round=2,
      total_rounds=10,
      answer="我做过订单系统。",
      messages=messages,
    )

    self.assertIn("已问过的问题（严禁重复或换壳重复）", prompt)
    self.assertIn("请介绍一下你最近做过的高并发项目。", prompt)
    self.assertIn("不得把旧问题换一种说法重复再问", prompt)
    self.assertIn("最近对话", prompt)

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

  def test_feedback_prompt_requests_detailed_reference_answers(self) -> None:
    session = Session(
      id="session_feedback",
      role="backend",
      mode="real",
      interviewerId="system_tech",
      status="completed",
      currentRound=1,
      totalRounds=1,
      startedAt="2026-04-21T00:00:00+00:00",
      finishedAt="2026-04-21T00:10:00+00:00",
    )
    messages = [
      ConversationMessage(
        id="q1",
        role="assistant",
        content="请介绍一个你做过的高并发项目。",
        round=1,
        createdAt="2026-04-21T00:00:00+00:00",
      ),
      ConversationMessage(
        id="a1",
        role="user",
        content="我做过订单系统。",
        round=1,
        createdAt="2026-04-21T00:01:00+00:00",
      ),
    ]

    prompt = FeedbackService().build_feedback_prompt(session, messages)

    self.assertIn("referenceAnswer 要比普通建议更详细，控制在180到260字", prompt)
    self.assertIn("给出可直接学习的示范答案", prompt)
    self.assertIn("不要只写“可以按背景-行动-结果回答”这类空泛模板", prompt)
    self.assertIn("每项必须包含 round、evaluation、referenceAnswer", prompt)
    self.assertIn("不要输出 note、comment、复盘观察等额外字段", prompt)
    self.assertNotIn("note 用中文一句话概括观察", prompt)

  def test_feedback_parser_accepts_round_reviews_without_note(self) -> None:
    session = Session(
      id="session_feedback",
      role="backend",
      mode="real",
      interviewerId="system_tech",
      status="completed",
      currentRound=1,
      totalRounds=1,
      startedAt="2026-04-21T00:00:00+00:00",
      finishedAt="2026-04-21T00:10:00+00:00",
    )
    messages = [
      ConversationMessage(
        id="q1",
        role="assistant",
        content="请介绍一个你做过的高并发项目。",
        round=1,
        createdAt="2026-04-21T00:00:00+00:00",
      ),
      ConversationMessage(
        id="a1",
        role="user",
        content="我做过订单系统。",
        round=1,
        createdAt="2026-04-21T00:01:00+00:00",
      ),
    ]
    raw_feedback = (
      '{"summary":"整体表达可继续补细节",'
      '"dimensions":['
      '{"key":"clarity","label":"表达清晰度","score":4,"comment":"结构较清楚"},'
      '{"key":"depth","label":"专业深度","score":3,"comment":"细节偏少"},'
      '{"key":"relevance","label":"问题贴合度","score":4,"comment":"基本贴题"}],'
      '"strengths":["方向明确","表达稳定"],'
      '"improvements":["补充数据","讲清取舍","加强复盘"],'
      '"suggestedAnswer":"先讲背景目标，再讲关键动作、技术取舍和结果。",'
      '"roundReviews":[{"round":1,"evaluation":"回答方向对，但技术细节和结果量化不足。",'
      '"referenceAnswer":"可以先说明订单系统的业务背景和并发目标，再讲你负责的模块、核心瓶颈、缓存或异步化取舍，以及最终延迟、吞吐或稳定性结果，最后补充一次复盘。"}]}'
    )

    feedback = FeedbackService().parse_feedback(session, messages, raw_feedback)

    self.assertEqual(feedback.roundReviews[0].note, "")
    self.assertIn("技术细节", feedback.roundReviews[0].evaluation)
    self.assertIn("业务背景", feedback.roundReviews[0].referenceAnswer)

  def test_fallback_reference_answer_is_detailed(self) -> None:
    reference_answer = FeedbackService()._build_fallback_reference_answer(
      {
        "question": "请介绍一个你做过的高并发项目。",
        "answer": "我做过订单系统。",
      }
    )

    self.assertGreaterEqual(len(reference_answer), 100)
    self.assertIn("业务背景和目标", reference_answer)
    self.assertIn("技术/方案取舍", reference_answer)


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
      repo.seed_formal_questions(
        [
          FormalQuestionBankWrite(
            scope_type="global",
            interviewer_id=None,
            role="frontend",
            stage_key="intro",
            question="请先介绍一下你最近做过的前端项目。",
            reference_answer="优秀回答会先说明背景、职责和结果。",
            tags=["通用题库", "前端"],
            enabled=True,
            sort_order=10,
          )
        ]
      )
      formal_questions = repo.list_formal_questions(scope_type="global", role="frontend")
      repo.save_formal_question_usage(
        FormalQuestionUsageEntry(
          message_id=message.id,
          session_id=session.id,
          question_id=formal_questions[0].id,
          interviewer_id=session.interviewerId,
          role=session.role,
          round_number=1,
          stage_key="intro",
          source_scope="global",
          used_at=message.createdAt,
        )
      )

      stored_feedback = repo.get_feedback(session.id)
      stored_questions = repo.list_questions(role="frontend", provider="doubao")
      stored_formal_questions = repo.list_formal_questions(scope_type="global", role="frontend")
      stored_usage = repo.list_formal_question_usage(session.id)
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
      self.assertEqual(len(stored_formal_questions), 1)
      self.assertEqual(stored_formal_questions[0].stage_key, "intro")
      self.assertEqual(len(stored_usage), 1)
      self.assertEqual(stored_usage[0].source_scope, "global")

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
          ownedQuestions=[
            {
              "role": "product_manager",
              "stageKey": "intro",
              "question": "请先介绍一个你主导过的产品项目。",
              "referenceAnswer": "优秀回答应包含背景、职责和结果。",
              "tags": ["项目背景"],
              "enabled": True,
              "sortOrder": 10,
            },
            {
              "role": "product_manager",
              "stageKey": "project",
              "question": "讲一个你做过的关键产品取舍。",
              "referenceAnswer": "优秀回答应讲清目标、数据依据和结果。",
              "tags": ["项目深挖"],
              "enabled": True,
              "sortOrder": 20,
            },
          ],
        )
      )

      self.assertEqual(created.id, "avatar_product_mentor")
      self.assertTrue(created.hasAvatarApiKey)
      self.assertEqual(created.avatarApiKey, "sk-custom-avatar-key")
      self.assertEqual(created.avatarApiKeyMasked, "sk-cu...-key")
      self.assertEqual(created.skillPrompt, "重点追问候选人的产品决策依据和指标定义。")
      self.assertEqual(created.interviewFlow, "第1阶段：产品背景\n第2阶段：指标拆解")
      self.assertEqual(len(created.ownedQuestions), 2)

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
          ownedQuestions=[
            {
              "role": "product_manager",
              "stageKey": "intro",
              "question": "请先介绍一个你主导过的产品项目。",
              "referenceAnswer": "优秀回答应包含背景、职责和结果。",
              "tags": ["项目背景"],
              "enabled": True,
              "sortOrder": 10,
            },
            {
              "role": "product_manager",
              "stageKey": "project",
              "question": "讲一个你做过的关键产品取舍。",
              "referenceAnswer": "优秀回答应讲清目标、数据依据和结果。",
              "tags": ["项目深挖"],
              "enabled": True,
              "sortOrder": 20,
            },
          ],
        )
      )

      self.assertTrue(updated.hasAvatarApiKey)
      self.assertEqual(updated.avatarApiKey, "sk-custom-avatar-key")
      self.assertEqual(updated.skillPrompt, "更新后的 skill：继续追问取舍和量化结果。")
      self.assertEqual(updated.interviewFlow, "第1阶段：产品背景\n第2阶段：方案取舍")
      self.assertEqual(len(updated.ownedQuestions), 2)
      service.delete_interviewer("avatar_product_mentor")
      self.assertFalse(repo.list_interviewer_profiles(enabled_only=False))

  def test_admin_interviewer_service_updates_global_question_bank(self) -> None:
    with tempfile.TemporaryDirectory() as tempdir:
      settings = replace(build_settings(), database_url=f"sqlite:///{tempdir}/interview-hub.sqlite3")
      repo = SqlitePersistenceRepository(settings.database_url)
      catalog = InterviewerCatalog(settings)
      service = AdminInterviewerService(settings=settings, catalog=catalog, persistence=repo)

      response = service.update_global_question_bank(
        UpsertGlobalQuestionBankRequest(
          role="backend",
          questions=[
            {
              "role": "backend",
              "stageKey": "intro",
              "question": "请先介绍一个你最熟悉的后端项目。",
              "referenceAnswer": "优秀回答应包含背景、职责和结果。",
              "tags": ["通用题库"],
              "enabled": True,
              "sortOrder": 10,
            },
            {
              "role": "backend",
              "stageKey": "project",
              "question": "讲一个你做过的高并发问题。",
              "referenceAnswer": "优秀回答应讲清瓶颈、方案和结果。",
              "tags": ["项目深挖"],
              "enabled": True,
              "sortOrder": 20,
            },
          ],
        )
      )

      self.assertEqual(response.role, "backend")
      self.assertEqual(len(response.questions), 2)
      self.assertEqual(response.questions[0].stageKey, "intro")

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
