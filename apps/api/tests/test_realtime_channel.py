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
