import sys
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.external_standards import ExternalStandardsAdapter


class ExternalStandardsAdapterKcscTest(unittest.TestCase):
    def setUp(self) -> None:
        self.original_key = ExternalStandardsAdapter.KCSC_API_KEY
        ExternalStandardsAdapter.KCSC_API_KEY = ""

    def tearDown(self) -> None:
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
