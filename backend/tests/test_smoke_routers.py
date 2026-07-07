"""
test_smoke_routers.py — 핵심 라우터 스모크 테스트.

세션 중 KCSC URL 회귀 등이 실제 발생했기에, 배포 전 GitHub Actions에서
주요 엔드포인트가 살아 있는지 최소 검증한다. 외부 API(Gemini/KCSC live)는
호출하지 않고, 로컬에서 결정되는 응답만 확인한다.
"""
import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app  # noqa: E402
from app.services.synonyms import synonym_terms  # noqa: E402

client = TestClient(app)


class SmokeRouterTest(unittest.TestCase):
    def test_health(self):
        r = client.get("/api/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json().get("ok"))

    def test_auth_sites_not_empty(self):
        r = client.get("/api/auth/sites")
        self.assertEqual(r.status_code, 200)
        sites = r.json().get("sites", [])
        self.assertGreater(len(sites), 0, "현장 목록이 비어 있음")

    def test_login_wrong_credentials(self):
        r = client.post("/api/auth/login", json={
            "name": "존재하지않는사람", "sabun": "0000000", "site_name": ""
        })
        self.assertEqual(r.status_code, 401)

    def test_login_missing_fields(self):
        r = client.post("/api/auth/login", json={"name": "", "sabun": "", "site_name": ""})
        self.assertEqual(r.status_code, 400)

    def test_checklist_trades(self):
        r = client.get("/api/checklists/trades")
        self.assertEqual(r.status_code, 200)
        trades = r.json().get("trades", [])
        self.assertEqual(len(trades), 5, "공종은 5개여야 함")

    def test_checklist_record_requires_site(self):
        # site_id 비면 400 (default 공용공간 혼입 차단)
        r = client.post("/api/checklists/record", json={
            "trade": "배관공사", "item_id": "x", "status": "적합", "site_id": ""
        })
        self.assertEqual(r.status_code, 400)

    def test_rag_search(self):
        r = client.get("/api/rag/search", params={"q": "배관", "limit": 3})
        self.assertEqual(r.status_code, 200)
        self.assertIn("results", r.json())

    def test_notices_list(self):
        r = client.get("/api/notices")
        self.assertEqual(r.status_code, 200)

    def test_synonym_expansion(self):
        # 단계1 동의어: '행거' → '지지' 포함
        expanded = synonym_terms(["행거"])
        self.assertIn("지지", expanded)


if __name__ == "__main__":
    unittest.main()
