from __future__ import annotations

import unittest

from app.services.realtime import ReplyDone, SecondMeRealtimeChannel


class SecondMeRealtimeChannelTests(unittest.IsolatedAsyncioTestCase):
  async def test_wait_for_reply_ignores_done_before_content(self) -> None:
    channel = SecondMeRealtimeChannel(
      ws_id="ws-test",
      visitor_user_id="visitor_1",
      origin=None,
      heartbeat_interval_seconds=0,
      reply_timeout_seconds=1,
    )
    channel._queue.put_nowait(ReplyDone())
    channel._queue.put_nowait("请简要介绍一下你的后端项目经历。")

    reply = await channel.wait_for_reply()

    self.assertEqual(reply, "请简要介绍一下你的后端项目经历。")

  async def test_wait_for_reply_ignores_echoed_prompt_before_content(self) -> None:
    channel = SecondMeRealtimeChannel(
      ws_id="ws-test",
      visitor_user_id="visitor_1",
      origin=None,
      heartbeat_interval_seconds=0,
      reply_timeout_seconds=1,
    )
    prompt = (
      "【当前阶段任务卡】\n"
      "当前轮次：第 1 / 3 轮。\n"
      "流程规则：只提出当前轮次最合适的一个面试问题，不要提前总结，不要输出反馈。\n"
      "【任务卡结束】\n"
      "你是 SecondMe 技术面试官。请严格执行当前阶段任务卡，只输出一个问题本身。"
    )
    channel._queue.put_nowait(prompt)
    channel._queue.put_nowait("请介绍一个你最近主导的后端项目。")

    reply = await channel.wait_for_reply(ignored_texts=[prompt])

    self.assertEqual(reply, "请介绍一个你最近主导的后端项目。")

  async def test_wait_for_reply_resets_merged_prompt_echo(self) -> None:
    channel = SecondMeRealtimeChannel(
      ws_id="ws-test",
      visitor_user_id="visitor_1",
      origin=None,
      heartbeat_interval_seconds=0,
      reply_timeout_seconds=1,
    )
    prompt = (
      "你是 SecondMe 技术面试官，当前正在作为后端工程师模拟面试官进行面试。"
      "【当前阶段任务卡】当前轮次：第 1 / 3 轮。【任务卡结束】"
      "只输出一个问题本身。"
    )
    channel._queue.put_nowait("你是 SecondMe 技术面试官，当前正在作为后端工程师模拟面试官进行面试。")
    channel._queue.put_nowait("【当前阶段任务卡】当前轮次：第 1 / 3 轮。【任务卡结束】")
    channel._queue.put_nowait("请讲一下你在高并发项目里的具体职责。")

    reply = await channel.wait_for_reply(ignored_texts=[prompt])

    self.assertEqual(reply, "请讲一下你在高并发项目里的具体职责。")

  async def test_wait_for_reply_ignores_prompt_prefix_fragment(self) -> None:
    channel = SecondMeRealtimeChannel(
      ws_id="ws-test",
      visitor_user_id="visitor_1",
      origin=None,
      heartbeat_interval_seconds=0,
      reply_timeout_seconds=1,
    )
    prompt = (
      "你是 SecondMe 技术面试官，当前正在作为后端工程师模拟面试官进行面试。"
      "请严格执行当前阶段任务卡，只输出一个问题本身。"
    )
    channel._queue.put_nowait("你是 SecondMe 技术面试官，当前正在作为后端工程师模拟面试官进行面试。")
    channel._queue.put_nowait("请介绍一下你最近负责的系统设计。")

    reply = await channel.wait_for_reply(ignored_texts=[prompt])

    self.assertEqual(reply, "请介绍一下你最近负责的系统设计。")

  async def test_wait_for_reply_keeps_stage_question_that_appears_inside_prompt(self) -> None:
    channel = SecondMeRealtimeChannel(
      ws_id="ws-test",
      visitor_user_id="visitor_1",
      origin=None,
      heartbeat_interval_seconds=0,
      reply_timeout_seconds=1,
    )
    prompt = (
      "【当前阶段任务卡】\n"
      "当前轮次：第 1 / 3 轮。\n"
      "问题：请简要介绍一下你的背景和之前的工作经历。\n"
      "【任务卡结束】\n"
      "只输出一个问题本身。"
    )
    channel._queue.put_nowait("请简要介绍一下你的背景和之前的工作经历。")

    reply = await channel.wait_for_reply(ignored_texts=[prompt])

    self.assertEqual(reply, "请简要介绍一下你的背景和之前的工作经历。")

  def test_extracts_nested_modal_answer(self) -> None:
    channel = SecondMeRealtimeChannel(
      ws_id="ws-test",
      visitor_user_id="visitor_1",
      origin=None,
      heartbeat_interval_seconds=0,
      reply_timeout_seconds=1,
    )

    reply = channel._extract_answer(
      {
        "sender": "umm",
        "multipleData": [
          {
            "modal": {
              "answer": "请介绍一下你最近负责的后端系统。"
            }
          }
        ],
      }
    )

    self.assertEqual(reply, "请介绍一下你最近负责的后端系统。")

  def test_extracts_avatar_text_from_client_sender_when_not_current_visitor(self) -> None:
    channel = SecondMeRealtimeChannel(
      ws_id="ws-test",
      visitor_user_id="visitor_1",
      origin=None,
      heartbeat_interval_seconds=0,
      reply_timeout_seconds=1,
    )

    reply = channel._extract_answer(
      {
        "sender": "client",
        "sendUserId": "avatar_user",
        "data": {
          "content": "说说 CAP 定理，以及你在项目里如何权衡一致性和可用性。"
        },
      }
    )

    self.assertEqual(reply, "说说 CAP 定理，以及你在项目里如何权衡一致性和可用性。")


if __name__ == "__main__":
  unittest.main()
