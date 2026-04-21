from __future__ import annotations

import unittest

from app.main import app


class AuthRouteTests(unittest.TestCase):
  def test_secondme_callback_routes_include_legacy_console_uri(self) -> None:
    paths = {route.path for route in app.routes}

    self.assertIn("/api/auth/secondme/callback", paths)
    self.assertIn("/api/auth/callback", paths)


if __name__ == "__main__":
  unittest.main()
