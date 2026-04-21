from __future__ import annotations

from typing import Optional

import httpx
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import Response

from app.core.config import Settings, get_settings
from app.core.errors import BadRequestError
from app.dependencies import get_secondme_oauth_service
from app.services.secondme_oauth import SecondMeOAuthService

router = APIRouter(prefix="/api/auth/secondme", tags=["Auth"])
legacy_router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.get("/login")
def secondme_login(
  interviewerId: Optional[str] = None,
  inspect: bool = False,
  service: SecondMeOAuthService = Depends(get_secondme_oauth_service),
) -> RedirectResponse:
  if inspect:
    return RedirectResponse(service.build_inspect_login_url(interviewerId), status_code=302)
  return RedirectResponse(service.build_login_url(interviewerId), status_code=302)


@router.get("/callback")
async def secondme_callback(
  code: Optional[str] = None,
  state: Optional[str] = None,
  error: Optional[str] = None,
  error_description: Optional[str] = None,
  service: SecondMeOAuthService = Depends(get_secondme_oauth_service),
  settings: Settings = Depends(get_settings),
) -> Response:
  if error:
    return RedirectResponse(
      _merge_url_params(
        settings.frontend_auth_error_url,
        {
          "secondme": "error",
          "error": error,
          "message": error_description or error,
        },
      ),
      status_code=302,
    )

  if not code or not state:
    raise BadRequestError("SecondMe OAuth callback 缺少 code 或 state。")

  if service.is_inspect_state(state):
    result = await service.inspect_callback(code=code, state=state)
    return JSONResponse(
      {
        "secondme": "inspected",
        "interviewerId": result.interviewer_id,
        "grantedScopes": result.granted_scopes,
        "tokenResponseKeys": result.token_response_keys,
        "tokenKeyLikePaths": result.token_key_like_paths,
        "userInfoShape": result.user_info_shape,
        "userInfoCandidates": result.user_info_candidates,
        "userInfoKeyLikePaths": result.user_info_key_like_paths,
      }
    )

  result = await service.handle_callback(code=code, state=state)
  return RedirectResponse(
    _merge_url_params(
      settings.frontend_auth_success_url,
      {
        "secondme": "connected",
        "interviewerId": result.interviewer_id,
        "avatarId": result.avatar_id,
      },
    ),
    status_code=302,
  )


@legacy_router.get("/callback")
async def secondme_legacy_callback(
  code: Optional[str] = None,
  state: Optional[str] = None,
  error: Optional[str] = None,
  error_description: Optional[str] = None,
  service: SecondMeOAuthService = Depends(get_secondme_oauth_service),
  settings: Settings = Depends(get_settings),
) -> Response:
  return await secondme_callback(
    code=code,
    state=state,
    error=error,
    error_description=error_description,
    service=service,
    settings=settings,
  )


def _merge_url_params(url: str, params: dict[str, str]) -> str:
  return str(httpx.URL(url, params={**dict(httpx.URL(url).params), **params}))
