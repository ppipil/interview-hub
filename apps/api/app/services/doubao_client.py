from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import Settings
from app.core.errors import UpstreamServiceError

RETRYABLE_HTTP_STATUS_CODES = {408, 429, 500, 502, 503, 504}
RETRYABLE_ERROR_CODES = {
  "DOUBAO_TIMEOUT_ERROR",
  "DOUBAO_CONNECT_ERROR",
  "DOUBAO_NETWORK_ERROR",
  "DOUBAO_PROTOCOL_ERROR",
  "DOUBAO_HTTP_RETRYABLE_ERROR",
}


class DoubaoClient:
  def __init__(self, settings: Settings) -> None:
    self._api_key = settings.doubao_api_key
    self._base_url = settings.doubao_base_url.rstrip("/")
    self._model = settings.doubao_model
    self._timeout = settings.doubao_request_timeout_seconds
    self._max_retries = max(0, settings.doubao_max_retries)

  @property
  def configured(self) -> bool:
    return bool(self._api_key and self._model and self._base_url)

  @property
  def model(self) -> str:
    return self._model

  async def chat(self, messages: List[Dict[str, str]], max_tokens: Optional[int] = None) -> str:
    if not self.configured:
      raise UpstreamServiceError(
        "豆包配置缺失，请先补齐 DOUBAO_API_KEY、DOUBAO_MODEL 和 DOUBAO_BASE_URL。",
        code="DOUBAO_NOT_CONFIGURED",
      )

    last_error: Optional[UpstreamServiceError] = None
    for attempt in range(self._max_retries + 1):
      try:
        payload = await self._request_chat(messages, max_tokens=max_tokens)
        return self._extract_content(payload)
      except UpstreamServiceError as exc:
        last_error = exc
        if attempt >= self._max_retries or not self._is_retryable(exc):
          raise
        await asyncio.sleep(min(2.0, 0.4 * (attempt + 1)))

    if last_error:
      raise last_error
    raise UpstreamServiceError("豆包请求失败。", code="DOUBAO_UNKNOWN_ERROR")

  async def _request_chat(self, messages: List[Dict[str, str]], max_tokens: Optional[int]) -> Dict[str, Any]:
    request_body: Dict[str, Any] = {
      "model": self._model,
      "messages": messages,
      "stream": False,
      "temperature": 0.3,
    }
    if max_tokens is not None:
      request_body["max_tokens"] = max_tokens

    try:
      async with httpx.AsyncClient(timeout=self._timeout, trust_env=False) as client:
        response = await client.post(
          f"{self._base_url}/chat/completions",
          headers={
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
          },
          json=request_body,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
      status_code = exc.response.status_code
      code = "DOUBAO_HTTP_RETRYABLE_ERROR" if status_code in RETRYABLE_HTTP_STATUS_CODES else "DOUBAO_HTTP_ERROR"
      raise UpstreamServiceError(
        f"豆包请求失败，HTTP {status_code}",
        code=code,
        details=self._error_details(exc, status_code=status_code),
      ) from exc
    except httpx.TimeoutException as exc:
      raise UpstreamServiceError(
        "豆包请求超时。当前模型响应较慢，请稍后重试，或调大 DOUBAO_REQUEST_TIMEOUT_SECONDS。",
        code="DOUBAO_TIMEOUT_ERROR",
        details=self._error_details(exc, timeout_seconds=self._timeout),
      ) from exc
    except httpx.ConnectError as exc:
      raise UpstreamServiceError(
        "当前无法建立到豆包服务的连接，请稍后重试。",
        code="DOUBAO_CONNECT_ERROR",
        details=self._error_details(exc),
      ) from exc
    except httpx.NetworkError as exc:
      raise UpstreamServiceError(
        "豆包连接中途异常中断，请稍后重试。",
        code="DOUBAO_NETWORK_ERROR",
        details=self._error_details(exc),
      ) from exc
    except httpx.RemoteProtocolError as exc:
      raise UpstreamServiceError(
        "豆包服务连接协议异常，请稍后重试。",
        code="DOUBAO_PROTOCOL_ERROR",
        details=self._error_details(exc),
      ) from exc
    except httpx.HTTPError as exc:
      raise UpstreamServiceError(
        "豆包 HTTP 客户端请求失败，请稍后重试。",
        code="DOUBAO_CLIENT_ERROR",
        details=self._error_details(exc),
      ) from exc
    except ValueError as exc:
      raise UpstreamServiceError(
        "豆包返回了无法解析的响应内容。",
        code="DOUBAO_RESPONSE_PARSE_ERROR",
        details=self._error_details(exc),
      ) from exc

  def _extract_content(self, payload: Dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
      raise UpstreamServiceError("豆包响应格式异常，缺少 choices。", code="DOUBAO_RESPONSE_FORMAT_ERROR")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
      raise UpstreamServiceError("豆包响应格式异常，choices[0] 不是对象。", code="DOUBAO_RESPONSE_FORMAT_ERROR")

    message = first_choice.get("message")
    if not isinstance(message, dict) or not isinstance(message.get("content"), str):
      raise UpstreamServiceError("豆包响应格式异常，缺少 message.content。", code="DOUBAO_RESPONSE_FORMAT_ERROR")

    return message["content"].strip()

  def _is_retryable(self, exc: UpstreamServiceError) -> bool:
    return exc.code in RETRYABLE_ERROR_CODES

  def _error_details(
    self,
    exc: BaseException,
    *,
    status_code: Optional[int] = None,
    timeout_seconds: Optional[float] = None,
  ) -> List[Dict[str, str]]:
    details = [{"field": "exception", "message": type(exc).__name__}]
    if status_code is not None:
      details.append({"field": "statusCode", "message": str(status_code)})
    if timeout_seconds is not None:
      details.append({"field": "timeoutSeconds", "message": str(timeout_seconds)})
    return details
