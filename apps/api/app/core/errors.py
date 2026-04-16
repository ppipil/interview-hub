from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
  def __init__(
    self,
    status_code: int,
    code: str,
    message: str,
    details: Optional[List[Dict[str, Any]]] = None,
  ) -> None:
    super().__init__(message)
    self.status_code = status_code
    self.code = code
    self.message = message
    self.details = details or []


class BadRequestError(AppError):
  def __init__(self, message: str) -> None:
    super().__init__(400, "BAD_REQUEST", message)


class NotFoundError(AppError):
  def __init__(self, message: str, field: Optional[str] = None) -> None:
    details = [{"field": field, "message": message}] if field else []
    super().__init__(404, "NOT_FOUND", message, details)


class ConflictError(AppError):
  def __init__(self, message: str) -> None:
    super().__init__(409, "CONFLICT", message)


class ValidationError(AppError):
  def __init__(self, message: str, field: Optional[str] = None) -> None:
    details = [{"field": field, "message": message}] if field else []
    super().__init__(422, "VALIDATION_ERROR", message, details)


class ConfigError(AppError):
  def __init__(self, message: str) -> None:
    super().__init__(503, "CONFIG_ERROR", message)


class UpstreamServiceError(AppError):
  def __init__(
    self,
    message: str,
    code: str = "UPSTREAM_ERROR",
    details: Optional[List[Dict[str, Any]]] = None,
  ) -> None:
    super().__init__(502, code, message, details)


def register_exception_handlers(app: FastAPI) -> None:
  @app.exception_handler(AppError)
  async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
      status_code=exc.status_code,
      content={
        "error": {
          "code": exc.code,
          "message": exc.message,
          "details": exc.details or None,
        }
      },
    )
