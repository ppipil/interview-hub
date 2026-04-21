from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from app.core.config import get_settings


class ConfigTests(unittest.TestCase):
  def test_avatar_api_key_falls_back_to_legacy_secondme_api_key(self) -> None:
    with patch.dict(
      os.environ,
      {
        "SECONDME_API_KEY": "sk-legacy-slot",
        "SECONDME_AVATAR_API_KEY": "",
      },
      clear=False,
    ):
      get_settings.cache_clear()
      try:
        settings = get_settings()
      finally:
        get_settings.cache_clear()

    self.assertEqual(settings.secondme_avatar_api_key, "sk-legacy-slot")


if __name__ == "__main__":
  unittest.main()
