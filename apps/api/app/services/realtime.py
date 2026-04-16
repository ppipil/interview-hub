from __future__ import annotations

import asyncio
import contextlib
import json
import threading
from typing import Any, Dict, Optional, Union

import websocket

from app.core.errors import UpstreamServiceError

RealtimeEvent = Union[str, UpstreamServiceError]


class SecondMeRealtimeChannel:
  def __init__(
    self,
    ws_id: str,
    visitor_user_id: str,
    origin: str,
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

    self._heartbeat_thread = threading.Thread(
      target=self._run_heartbeat_loop,
      name=f"secondme-heartbeat-{self._ws_id}",
      daemon=True,
    )
    self._heartbeat_thread.start()

  async def wait_for_reply(self) -> str:
    try:
      event = await asyncio.wait_for(
        self._queue.get(),
        timeout=self._reply_timeout_seconds,
      )
    except asyncio.TimeoutError as exc:
      raise UpstreamServiceError("等待 SecondMe 回复超时。") from exc

    if isinstance(event, UpstreamServiceError):
      raise event

    merged_reply = event
    while True:
      try:
        next_event = await asyncio.wait_for(
          self._queue.get(),
          timeout=self._stream_idle_timeout_seconds,
        )
      except asyncio.TimeoutError:
        return merged_reply.strip()

      if isinstance(next_event, UpstreamServiceError):
        raise next_event
      merged_reply = self._merge_reply_chunk(merged_reply, next_event)

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
      self._app.run_forever(origin=self._origin)
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
    if sender == "umm":
      return self._extract_multiple_data_answer(payload)

    if sender == "client" and payload.get("sendUserId") != self._visitor_user_id:
      return self._extract_multiple_data_answer(payload)

    return None

  def _extract_multiple_data_answer(self, payload: Dict[str, Any]) -> Optional[str]:
    multiple_data = payload.get("multipleData")
    if not isinstance(multiple_data, list) or not multiple_data:
      return None

    first_item = multiple_data[0]
    if not isinstance(first_item, dict):
      return None

    modal = first_item.get("modal")
    if not isinstance(modal, dict):
      return None

    answer = modal.get("answer")
    return str(answer).strip() if answer else None

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

  def _join_thread(self, thread: Optional[threading.Thread]) -> None:
    if thread and thread.is_alive():
      thread.join(timeout=2)
