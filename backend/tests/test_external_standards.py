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

    def test_kcsc_result_source_url_prefers_document_name_search(self) -> None:
        # KCSC OpenAPI의 코드(순수 숫자 fullCode)는 KCSC 공개 사이트 검색과
        # 형식이 안 맞아 0건이 나오므로, 문서명(title)을 검색어로 사용한다.
        from urllib.parse import quote

        result = ExternalStandardsAdapter._decorate_kcsc_results(
            [
                {
                    "id": "KCS-31-20-15",
                    "source": "kcsc",
                    "code": "2020312015",
                    "full_code": "2020312015",
                    "title": "기계설비 배관공사",
                    "official_url": "https://www.kcsc.re.kr/StandardCode/Viewer/12345",
                }
            ],
            "배관",
            limit=5,
        )

        self.assertEqual(len(result), 1)
        self.assertIn("kcsc.re.kr/standardCode/search", result[0]["source_url"])
        # 문서명 기반 검색어 (코드가 아닌 title)
        self.assertIn(f"kcsc_cd={quote('기계설비 배관공사', safe='')}", result[0]["source_url"])
        self.assertNotIn("/Viewer/", result[0]["source_url"])


if __name__ == "__main__":
    unittest.main()
