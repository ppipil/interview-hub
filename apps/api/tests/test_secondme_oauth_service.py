from __future__ import annotations

from contextlib import contextmanager
import json
import tempfile
import unittest

import httpx

from app.core.errors import UpstreamServiceError
from app.repositories.sqlite_persistence import SqlitePersistenceRepository
from app.services.secondme_oauth import SecondMeOAuthService
from app.services.secondme_oauth_client import SecondMeOAuthClient
from test_interview_service import build_settings


class SecondMeOAuthServiceTests(unittest.IsolatedAsyncioTestCase):
  async def test_callback_exchanges_code_creates_key_and_persists_secret(self) -> None:
    requests = []

    async def handler(request: httpx.Request) -> httpx.Response:
      requests.append(request)
      if str(request.url) == "https://api.mindverse.com/gate/lab/api/oauth/token/code":
        return httpx.Response(
          200,
          json={
            "code": 0,
            "data": {
              "accessToken": "lba_at_user",
              "refreshToken": "lba_rt_user",
              "expiresIn": 3600,
              "scope": ["userinfo", "chat.write", "avatar.read"],
            },
          },
        )
      if str(request.url) == "https://api.mindverse.com/gate/lab/api/secondme/user/info":
        return httpx.Response(200, json={"code": 0, "data": {"id": "user_1", "name": "测试用户"}})
      if str(request.url) == "https://api.mindverse.com/gate/lab/api/secondme/avatar/list?pageNo=1&pageSize=20":
        return httpx.Response(
          200,
          json={
            "code": 0,
            "data": {
              "records": [
                {
                  "id": 123,
                  "name": "我的分身",
                }
              ]
            },
          },
        )
      if str(request.url) == "https://api.mindverse.com/gate/lab/api/secondme/avatar/api-key/create":
        body = json.loads(request.content.decode("utf-8"))
        self.assertEqual(body["avatarId"], 123)
        return httpx.Response(
          200,
          json={
            "code": 0,
            "data": {
              "keyId": 200,
              "avatarId": 123,
              "name": "Interview Hub Test",
              "secretKey": "sk-created-from-oauth",
              "enabled": True,
            },
          },
        )
      return httpx.Response(404, json={"code": 404, "message": "not found"})

    settings = build_settings()
    with self.subTest("oauth callback sync"):
      with self._temp_repo() as repo:
        client = SecondMeOAuthClient(settings, transport=httpx.MockTransport(handler))
        service = SecondMeOAuthService(settings=settings, client=client, persistence=repo)

        login_url = service.build_login_url("secondme_tech")
        self.assertTrue(login_url.startswith("https://go.second-me.cn/oauth/?"))
        state = httpx.URL(login_url).params["state"]
        result = await service.handle_callback(code="auth_code", state=state)
        stored_secret = repo.get_interviewer_secret("secondme_tech")

        self.assertEqual(result.avatar_id, "123")
        self.assertEqual(result.avatar_name, "我的分身")
        self.assertIsNotNone(stored_secret)
        self.assertEqual(stored_secret.avatar_api_key, "sk-created-from-oauth")
        self.assertEqual(len(requests), 4)

  async def test_callback_fails_fast_when_avatar_read_scope_is_missing(self) -> None:
    requests = []

    async def handler(request: httpx.Request) -> httpx.Response:
      requests.append(request)
      if str(request.url) == "https://api.mindverse.com/gate/lab/api/oauth/token/code":
        return httpx.Response(
          200,
          json={
            "code": 0,
            "data": {
              "accessToken": "lba_at_user",
              "expiresIn": 3600,
              "scope": ["userinfo", "chat.write"],
            },
          },
        )
      if str(request.url) == "https://api.mindverse.com/gate/lab/api/secondme/user/info":
        return httpx.Response(200, json={"code": 0, "data": {"id": "user_1", "name": "测试用户"}})
      return httpx.Response(500, json={"code": 500, "message": "should not call avatar APIs"})

    settings = build_settings()
    with self._temp_repo() as repo:
      client = SecondMeOAuthClient(settings, transport=httpx.MockTransport(handler))
      service = SecondMeOAuthService(settings=settings, client=client, persistence=repo)

      state = httpx.URL(service.build_login_url("secondme_tech")).params["state"]
      with self.assertRaises(UpstreamServiceError) as ctx:
        await service.handle_callback(code="auth_code", state=state)

      self.assertEqual(ctx.exception.code, "SECONDME_OAUTH_SCOPE_MISSING")
      self.assertEqual(ctx.exception.details[2]["field"], "userInfoShape")
      self.assertIn("root keys: id, name", ctx.exception.details[2]["message"])
      self.assertEqual(ctx.exception.details[3]["field"], "userInfoCandidates")
      self.assertEqual(len(requests), 2)

  async def test_callback_uses_avatar_id_from_user_info_without_avatar_read_scope(self) -> None:
    requests = []

    async def handler(request: httpx.Request) -> httpx.Response:
      requests.append(request)
      if str(request.url) == "https://api.mindverse.com/gate/lab/api/oauth/token/code":
        return httpx.Response(
          200,
          json={
            "code": 0,
            "data": {
              "accessToken": "lba_at_user",
              "expiresIn": 3600,
              "scope": ["userinfo", "chat.write"],
            },
          },
        )
      if str(request.url) == "https://api.mindverse.com/gate/lab/api/secondme/user/info":
        return httpx.Response(
          200,
          json={
            "code": 0,
            "data": {
              "id": "user_1",
              "name": "测试用户",
              "avatarId": 456,
              "avatarName": "用户信息里的分身",
            },
          },
        )
      if str(request.url) == "https://api.mindverse.com/gate/lab/api/secondme/avatar/api-key/create":
        body = json.loads(request.content.decode("utf-8"))
        self.assertEqual(body["avatarId"], 456)
        return httpx.Response(
          200,
          json={
            "code": 0,
            "data": {
              "keyId": 201,
              "avatarId": 456,
              "name": "Interview Hub Test",
              "secretKey": "sk-created-from-user-info",
              "enabled": True,
            },
          },
        )
      return httpx.Response(500, json={"code": 500, "message": "should not call avatar list"})

    settings = build_settings()
    with self._temp_repo() as repo:
      client = SecondMeOAuthClient(settings, transport=httpx.MockTransport(handler))
      service = SecondMeOAuthService(settings=settings, client=client, persistence=repo)

      state = httpx.URL(service.build_login_url("secondme_tech")).params["state"]
      result = await service.handle_callback(code="auth_code", state=state)
      stored_secret = repo.get_interviewer_secret("secondme_tech")

      self.assertEqual(result.avatar_id, "456")
      self.assertEqual(result.avatar_name, "用户信息里的分身")
      self.assertIsNotNone(stored_secret)
      self.assertEqual(stored_secret.avatar_api_key, "sk-created-from-user-info")
      self.assertEqual(len(requests), 3)

  async def test_inspect_callback_only_reports_safe_oauth_shapes(self) -> None:
    requests = []

    async def handler(request: httpx.Request) -> httpx.Response:
      requests.append(request)
      if str(request.url) == "https://api.mindverse.com/gate/lab/api/oauth/token/code":
        return httpx.Response(
          200,
          json={
            "code": 0,
            "data": {
              "accessToken": "lba_at_user",
              "expiresIn": 3600,
              "scope": ["userinfo", "chat.write"],
              "secretKey": "sk-hidden-test-value",
            },
          },
        )
      if str(request.url) == "https://api.mindverse.com/gate/lab/api/secondme/user/info":
        return httpx.Response(
          200,
          json={
            "code": 0,
            "data": {
              "userId": "user_1",
              "name": "测试用户",
              "avatar": "https://example.com/avatar.png",
              "apiKey": "sk-hidden-user-info-value",
            },
          },
        )
      return httpx.Response(500, json={"code": 500, "message": "should not call avatar APIs"})

    settings = build_settings()
    with self._temp_repo() as repo:
      client = SecondMeOAuthClient(settings, transport=httpx.MockTransport(handler))
      service = SecondMeOAuthService(settings=settings, client=client, persistence=repo)

      login_url = service.build_inspect_login_url("secondme_tech")
      state = httpx.URL(login_url).params["state"]
      self.assertTrue(service.is_inspect_state(state))

      result = await service.inspect_callback(code="auth_code", state=state)

      self.assertIn("secretKey", result.token_response_keys)
      self.assertEqual(result.token_key_like_paths, ["secretKey: string(sk-like,len=20)"])
      self.assertEqual(result.user_info_key_like_paths, ["apiKey: string(sk-like,len=25)"])
      self.assertEqual(len(requests), 2)

  @contextmanager
  def _temp_repo(self):
    with tempfile.TemporaryDirectory() as tempdir:
      yield SqlitePersistenceRepository(f"sqlite:///{tempdir}/interview-hub.sqlite3")


if __name__ == "__main__":
  unittest.main()
