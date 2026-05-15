import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services import external_settings
from app.services.external_standards import ExternalStandardsAdapter


class ExternalStandardsAdapterKcscTest(unittest.TestCase):
    def setUp(self) -> None:
        self.original_key = ExternalStandardsAdapter.KCSC_API_KEY
        ExternalStandardsAdapter.KCSC_API_KEY = ""
        self.tmp = tempfile.TemporaryDirectory()
        self.patches = [
            patch.object(external_settings, "SETTINGS_PATH", Path(self.tmp.name) / "external_settings.json"),
            patch.object(external_settings, "DEFAULT_KCSC_API_KEY", ""),
            patch.dict(os.environ, {"KCSC_API_KEY": ""}, clear=False),
        ]
        for item in self.patches:
            item.start()

    def tearDown(self) -> None:
        for item in reversed(self.patches):
            item.stop()
        self.tmp.cleanup()
        ExternalStandardsAdapter.KCSC_API_KEY = self.original_key

    def test_kcsc_returns_official_search_handoff_when_samples_do_not_match(self) -> None:
        adapter = ExternalStandardsAdapter()

        query = "zzzxqv12345"

        result = adapter.search_kcsc(query, limit=5)

        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 1)
        item = result["items"][0]
        self.assertEqual(item["source"], "kcsc")
        self.assertIn(query, item["title"])
        self.assertIn("kcsc.re.kr/standardCode/search", item["source_url"])
        self.assertEqual(item["source_url"], item["official_url"])

    def test_kcsc_sample_results_include_clickable_source_url(self) -> None:
        adapter = ExternalStandardsAdapter()

        result = adapter.search_kcsc("배관", limit=5)

        self.assertGreaterEqual(result["count"], 1)
        for item in result["items"]:
            self.assertEqual(item["source"], "kcsc")
            self.assertTrue(item.get("source_url") or item.get("official_url"))


if __name__ == "__main__":
    unittest.main()
