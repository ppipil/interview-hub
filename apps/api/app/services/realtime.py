from __future__ import annotations

import asyncio
import contextlib
import json
import threading
from typing import Any, Dict, Optional, Sequence, Union

import websocket

from app.core.errors import UpstreamServiceError


class ReplyDone:
  pass


RealtimeEvent = Union[str, UpstreamServiceError, ReplyDone]

INTERNAL_PROMPT_MARKERS = (
  "【Interview Hub 面试官 Skill】",
  "【Skill 结束】",
  "【当前阶段任务卡】",
  "【任务卡结束】",
  "当前阶段任务卡是流程硬约束",
  "请严格执行当前阶段任务卡",
  "只输出一个问题本身",
  "不要自我介绍，不要解释流程",
  "候选人刚才针对",
  "现在这场模拟面试已经结束",
  "JSON 字段必须严格使用以下 key",
  "只返回一个可解析",
)


class SecondMeRealtimeChannel:
  def __init__(
    self,
    ws_id: str,
    visitor_user_id: str,
    origin: Optional[str],
    heartbeat_interval_seconds: int,
    reply_timeout_seconds: float,
  ) -> None:
    self._ws_id = ws_id
    self._visitor_user_id = visitor_user_id
    self._origin = origin
    self._heartbeat_interval_seconds = heartbeat_interval_seconds
    self._reply_timeout_seconds = reply_timeout_seconds
    self._stream_idle_timeout_seconds = min(3.0, max(1.0, reply_timeout_seconds / 8))
    self._queue: "asyncio.Queue[RealtimeEvent]" = asyncio.Queue()
    self._loop: Optional[asyncio.AbstractEventLoop] = None
    self._app: Optional[websocket.WebSocketApp] = None
    self._socket_thread: Optional[threading.Thread] = None
    self._heartbeat_thread: Optional[threading.Thread] = None
    self._stop_event = threading.Event()
    self._connect_event = threading.Event()
    self._connected = False
    self._connect_error: Optional[BaseException] = None

  async def connect(self, address: str) -> None:
    self._loop = asyncio.get_running_loop()
    self._stop_event = threading.Event()
    self._connect_event = threading.Event()
    self._connected = False
    self._connect_error = None

    self._app = websocket.WebSocketApp(
      address,
      on_open=self._on_open,
      on_message=self._on_message,
      on_error=self._on_error,
      on_close=self._on_close,
    )
    self._socket_thread = threading.Thread(
      target=self._run_socket_forever,
      name=f"secondme-ws-{self._ws_id}",
      daemon=True,
    )
    self._socket_thread.start()

    opened = await asyncio.to_thread(self._connect_event.wait, 10)
    if not opened or not self._connected or not self._app or not self._app.sock or not self._app.sock.connected:
      await self.close()
      raise UpstreamServiceError("当前无法建立 SecondMe 实时连接，请稍后重试。") from self._connect_error

    if self._heartbeat_interval_seconds > 0 and self._ws_id:
      self._heartbeat_thread = threading.Thread(
        target=self._run_heartbeat_loop,
        name=f"secondme-heartbeat-{self._ws_id}",
        daemon=True,
      )
      self._heartbeat_thread.start()

  async def wait_for_reply(self, ignored_texts: Optional[Sequence[str]] = None) -> str:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + self._reply_timeout_seconds
    merged_reply = ""
    ignored_replies = self._normalize_ignored_texts(ignored_texts)

    while True:
      timeout_seconds = self._stream_idle_timeout_seconds if merged_reply else max(0.0, deadline - loop.time())
      try:
        event = await asyncio.wait_for(
          self._queue.get(),
          timeout=timeout_seconds,
        )
      except asyncio.TimeoutError as exc:
        if merged_reply:
          return self._ensure_non_empty_reply(merged_reply, ignored_replies)
        raise UpstreamServiceError("等待 SecondMe 回复超时。") from exc

      if isinstance(event, UpstreamServiceError):
        raise event
      if isinstance(event, ReplyDone):
        if merged_reply:
          return self._ensure_non_empty_reply(merged_reply, ignored_replies)
        # Visitor Chat may emit a done/control event before the content event
        # that the official app eventually renders. Keep listening instead of
        # saving an empty question.
        if loop.time() >= deadline:
          raise UpstreamServiceError("SecondMe 实时回复为空，请稍后重试。", code="SECONDME_EMPTY_REPLY")
        continue
      if self._should_ignore_reply_text(event, ignored_replies):
        if self._is_ignored_reply_fragment(merged_reply, ignored_replies):
          merged_reply = ""
        continue

      next_reply = self._merge_reply_chunk(merged_reply, event)
      if self._should_ignore_reply_text(next_reply, ignored_replies):
        merged_reply = ""
        continue

      merged_reply = next_reply

      if loop.time() >= deadline:
        return self._ensure_non_empty_reply(merged_reply, ignored_replies)

  async def close(self) -> None:
    self._stop_event.set()

    app = self._app
    if app and app.sock and app.sock.connected:
      app.close()

    await asyncio.to_thread(self._join_thread, self._heartbeat_thread)
    await asyncio.to_thread(self._join_thread, self._socket_thread)

    self._app = None
    self._socket_thread = None
    self._heartbeat_thread = None
    self._connected = False

  def _run_socket_forever(self) -> None:
    if not self._app:
      return

    try:
      if self._origin:
        self._app.run_forever(origin=self._origin)
      else:
        self._app.run_forever()
    except Exception as exc:
      self._connect_error = exc
      self._connect_event.set()
      self._push_error("SecondMe 实时连接已异常中断。")

  def _run_heartbeat_loop(self) -> None:
    while not self._stop_event.wait(self._heartbeat_interval_seconds):
      if not self._app or not self._app.sock or not self._app.sock.connected:
        return

      try:
        self._app.send(json.dumps({"type": "ping", "wsId": self._ws_id}))
      except Exception:
        self._push_error("SecondMe 实时连接心跳发送失败。")
        return

  def _on_open(self, _: websocket.WebSocketApp) -> None:
    self._connected = True
    self._connect_event.set()

  def _on_message(self, _: websocket.WebSocketApp, raw_message: str) -> None:
    with contextlib.suppress(json.JSONDecodeError):
      payload = json.loads(raw_message)
      answer = self._extract_answer(payload)
      if answer:
        self._push_event(answer)
      if payload.get("sender") == "umm" and payload.get("index") == -1:
        self._push_event(ReplyDone())
        return

  def _on_error(self, _: websocket.WebSocketApp, error: Any) -> None:
    if not self._connected:
      self._connect_error = error if isinstance(error, BaseException) else RuntimeError(str(error))
      self._connect_event.set()
      return

    self._push_error("SecondMe 实时连接发生异常。")

  def _on_close(
    self,
    _: websocket.WebSocketApp,
    __: Any,
    ___: Any,
  ) -> None:
    if not self._connected:
      if not self._connect_error:
        self._connect_error = RuntimeError("realtime connection closed before open")
      self._connect_event.set()
      return

    if not self._stop_event.is_set():
      self._push_error("SecondMe 实时连接已断开。")

  def _push_event(self, event: RealtimeEvent) -> None:
    if self._loop and not self._loop.is_closed():
      self._loop.call_soon_threadsafe(self._queue.put_nowait, event)

  def _push_error(self, message: str) -> None:
    if self._stop_event.is_set():
      return
    self._push_event(UpstreamServiceError(message))

  def _extract_answer(self, payload: Dict[str, Any]) -> Optional[str]:
    sender = payload.get("sender")
    normalized_sender = str(sender or "").lower()
    if normalized_sender in {"umm", "assistant", "avatar", "agent", "bot", "ai", "secondme"}:
      return self._extract_text_answer(payload)

    send_user_id = payload.get("sendUserId") or payload.get("senderUserId") or payload.get("userId")
    if self._visitor_user_id and normalized_sender == "client" and send_user_id and send_user_id != self._visitor_user_id:
      return self._extract_text_answer(payload)

    return None

  def _extract_text_answer(self, payload: Dict[str, Any]) -> Optional[str]:
    return self._extract_text_from_payload(payload)

  def _extract_text_from_payload(self, payload: Any) -> Optional[str]:
    if isinstance(payload, str):
      normalized = payload.strip()
      return normalized or None

    if isinstance(payload, list):
      for item in payload:
        text = self._extract_text_from_payload(item)
        if text:
          return text
      return None

    if not isinstance(payload, dict):
      return None

    for key in ("answer", "content", "text", "message", "reply", "output", "delta"):
      value = payload.get(key)
      if isinstance(value, str) and value.strip():
        return value.strip()

    for key in ("modal", "data", "message", "payload", "body", "multipleData", "messages"):
      text = self._extract_text_from_payload(payload.get(key))
      if text:
        return text

    return None

  def _merge_reply_chunk(self, current: str, next_chunk: str) -> str:
    if not current:
      return next_chunk
    if current == next_chunk:
      return current
    if next_chunk.startswith(current):
      return next_chunk
    if current.startswith(next_chunk):
      return current
    if next_chunk in current:
      return current
    if current in next_chunk:
      return next_chunk

    max_overlap = min(len(current), len(next_chunk))
    for overlap in range(max_overlap, 0, -1):
      if current[-overlap:] == next_chunk[:overlap]:
        return f"{current}{next_chunk[overlap:]}"
    return f"{current}{next_chunk}"

  def _normalize_ignored_texts(self, ignored_texts: Optional[Sequence[str]]) -> tuple[str, ...]:
    if not ignored_texts:
      return ()

    return tuple(
      normalized
      for item in ignored_texts
      for normalized in [self._normalize_reply_for_compare(item)]
      if normalized
    )

  def _should_ignore_reply_text(self, reply: str, ignored_replies: Sequence[str]) -> bool:
    normalized = self._normalize_reply_for_compare(reply)
    if not normalized:
      return False

    if any(marker in normalized for marker in INTERNAL_PROMPT_MARKERS):
      return True

    for ignored_reply in ignored_replies:
      if normalized == ignored_reply:
        return True
      if self._is_ignored_reply_fragment(normalized, ignored_replies):
        return True
      if len(ignored_reply) >= 80 and ignored_reply in normalized:
        return True

    return False

  def _is_ignored_reply_fragment(self, reply: str, ignored_replies: Sequence[str]) -> bool:
    normalized = self._normalize_reply_for_compare(reply)
    if len(normalized) < 20:
      return False

    return any(ignored_reply.startswith(normalized) for ignored_reply in ignored_replies)

  def _normalize_reply_for_compare(self, reply: str) -> str:
    return " ".join(str(reply or "").split())

  def _ensure_non_empty_reply(self, reply: str, ignored_replies: Sequence[str]) -> str:
    normalized = reply.strip()
    if not normalized:
      raise UpstreamServiceError("SecondMe 实时回复为空，请稍后重试。", code="SECONDME_EMPTY_REPLY")
    if self._should_ignore_reply_text(normalized, ignored_replies):
      raise UpstreamServiceError("SecondMe 实时回复疑似回显了内部 Prompt，请稍后重试。", code="SECONDME_PROMPT_ECHO_REPLY")
    return normalized

  def _join_thread(self, thread: Optional[threading.Thread]) -> None:
    if thread and thread.is_alive():
      thread.join(timeout=2)
