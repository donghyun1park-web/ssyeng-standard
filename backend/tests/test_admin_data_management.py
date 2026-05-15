import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import quote
from unittest.mock import patch

from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app
from app.routers import auth, notices, site_issues
from app.services import external_settings


class AdminDataManagementTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.auth_path = Path(self.tmp.name) / "auth_users.json"
        self.sites_path = Path(self.tmp.name) / "sites.json"
        self.notices_path = Path(self.tmp.name) / "notices.json"
        self.notice_files_dir = Path(self.tmp.name) / "notice_files"
        self.external_settings_path = Path(self.tmp.name) / "external_settings.json"
        self.auth_path.write_text(
            json.dumps(
                {
                    "users": [
                        {"name": "현장사용자", "sabun": "1001"},
                        {"name": "관리사용자", "sabun": "9001", "can_manage_all": True},
                    ],
                    "sites": ["설비팀", "건축기술팀", "A현장"],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        self.sites_path.write_text(
            json.dumps({"sites": [], "drawing_reviews": [], "site_issues": []}, ensure_ascii=False),
            encoding="utf-8",
        )
        self.notices_path.write_text(json.dumps({"notices": []}, ensure_ascii=False), encoding="utf-8")
        self.patches = [
            patch.object(auth, "AUTH_PATH", self.auth_path),
            patch.object(site_issues, "SITES_PATH", self.sites_path),
            patch.object(notices, "NOTICES_PATH", self.notices_path),
            patch.object(notices, "FILES_DIR", self.notice_files_dir),
            patch.object(external_settings, "SETTINGS_PATH", self.external_settings_path),
            patch.object(external_settings, "DEFAULT_KCSC_API_KEY", "default-kcsc-key-1234567890"),
            patch.dict(os.environ, {"ADMIN_TOKEN": "secret", "KCSC_API_KEY": ""}, clear=False),
        ]
        for item in self.patches:
            item.start()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        for item in reversed(self.patches):
            item.stop()
        self.tmp.cleanup()

    def test_admin_token_required_for_auth_database_management(self) -> None:
        unauthorized = self.client.get("/api/admin/auth-data")
        self.assertEqual(unauthorized.status_code, 401)

        authorized = self.client.get("/api/admin/auth-data", headers={"X-Admin-Token": "secret"})
        self.assertEqual(authorized.status_code, 200)
        data = authorized.json()
        self.assertIn("설비팀", data["sites"])
        self.assertIn("건축기술팀", data["sites"])

    def test_admin_can_manage_sites_and_login_users(self) -> None:
        headers = {"X-Admin-Token": "secret"}

        site_resp = self.client.post("/api/admin/auth-sites", headers=headers, json={"name": "B현장"})
        self.assertEqual(site_resp.status_code, 201)

        user_resp = self.client.post(
            "/api/admin/auth-users",
            headers=headers,
            json={"name": "공지담당", "sabun": "9002", "can_manage_all": True},
        )
        self.assertEqual(user_resp.status_code, 201)

        login_resp = self.client.post(
            "/api/auth/login",
            json={"name": "공지담당", "sabun": "9002", "site_name": "B현장"},
        )
        self.assertEqual(login_resp.status_code, 200)
        self.assertTrue(login_resp.json()["user"]["can_manage_all"])

    def test_admin_can_manage_kcsc_api_key_setting(self) -> None:
        unauthorized = self.client.get("/api/admin/external-settings")
        self.assertEqual(unauthorized.status_code, 401)

        headers = {"X-Admin-Token": "secret"}
        status = self.client.get("/api/admin/external-settings", headers=headers)
        self.assertEqual(status.status_code, 200)
        self.assertTrue(status.json()["kcsc"]["configured"])
        self.assertEqual(status.json()["kcsc"]["source"], "bundled-default")

        updated = self.client.put(
            "/api/admin/external-settings",
            headers=headers,
            json={"kcsc_api_key": "custom-kcsc-key-1234567890"},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["kcsc"]["source"], "custom")
        self.assertTrue(updated.json()["kcsc"]["has_custom_key"])
        self.assertNotIn("custom-kcsc-key-1234567890", str(updated.json()))

        reset = self.client.put("/api/admin/external-settings", headers=headers, json={"kcsc_api_key": ""})
        self.assertEqual(reset.status_code, 200)
        self.assertEqual(reset.json()["kcsc"]["source"], "bundled-default")

    def test_master_site_user_and_checked_manager_can_manage_drawing_reviews(self) -> None:
        create_resp = self.client.post(
            "/api/drawing-reviews",
            headers={
                "X-User-Name": quote("현장사용자"),
                "X-User-Sabun": "1001",
                "X-User-Site": quote("A현장"),
            },
            json={"site_id": "A현장", "review_content": "슬리브 위치 확인"},
        )
        self.assertEqual(create_resp.status_code, 201)
        review_id = create_resp.json()["review"]["id"]

        blocked = self.client.put(
            f"/api/drawing-reviews/{review_id}",
            headers={
                "X-User-Name": quote("현장사용자"),
                "X-User-Sabun": "1001",
                "X-User-Site": quote("다른현장"),
            },
            json={"review_content": "수정 시도"},
        )
        self.assertEqual(blocked.status_code, 403)

        manager_update = self.client.put(
            f"/api/drawing-reviews/{review_id}",
            headers={
                "X-User-Name": quote("관리사용자"),
                "X-User-Sabun": "9001",
                "X-User-Site": quote("다른현장"),
            },
            json={"review_content": "관리자 수정"},
        )
        self.assertEqual(manager_update.status_code, 200)
        self.assertEqual(manager_update.json()["review"]["review_content"], "관리자 수정")

    def test_checked_manager_can_create_notice_without_admin_token(self) -> None:
        blocked = self.client.post(
            "/api/notices",
            headers={"X-User-Name": quote("현장사용자"), "X-User-Sabun": "1001"},
            data={"title": "공지", "content": "내용", "poster": "현장사용자"},
        )
        self.assertEqual(blocked.status_code, 403)

        created = self.client.post(
            "/api/notices",
            headers={"X-User-Name": quote("관리사용자"), "X-User-Sabun": "9001"},
            data={"title": "관리 공지", "content": "전체 공지", "poster": "관리사용자"},
        )
        self.assertEqual(created.status_code, 200)
        self.assertEqual(created.json()["notice"]["title"], "관리 공지")


if __name__ == "__main__":
    unittest.main()
