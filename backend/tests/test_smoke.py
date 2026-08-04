import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./backend/test-suite.db"
os.environ["UPLOAD_DIR"] = "./backend/test-storage"
os.environ["DEMO_AI_ENABLED"] = "true"

from fastapi.testclient import TestClient
from app.main import app


def test_complete_product_flow():
    with TestClient(app) as client:
        email = "flow@example.com"
        registration = client.post("/api/v1/auth/register", json={"email": email, "password": "password123", "display_name": "Flow User"})
        if registration.status_code == 409:
            registration = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
        assert registration.status_code == 200
        headers = {"Authorization": f"Bearer {registration.json()['access_token']}"}

        meeting = client.post("/api/v1/meetings", headers=headers, data={"title": "产品周会"}, files={"file": ("meeting.mp3", b"demo audio", "audio/mpeg")})
        assert meeting.status_code == 200
        meeting = client.get(f"/api/v1/meetings/{meeting.json()['id']}", headers=headers)
        assert meeting.json()["status"] == "completed"

        report = client.post("/api/v1/reports/daily/generate", headers=headers, json={"report_date": "2026-08-04", "additional_notes": "完成联调"})
        assert report.status_code == 200
        assert report.json()["content"]["summary"]

        document = client.post("/api/v1/documents", headers=headers, data={"title": "差旅制度"}, files={"file": ("policy.txt", "员工出差住宿标准为每晚五百元。".encode(), "text/plain")})
        assert document.status_code == 200
        documents = client.get("/api/v1/documents", headers=headers)
        assert documents.json()[0]["status"] == "ready"

        conversation = client.post("/api/v1/conversations", headers=headers, json={"title": "制度问答"})
        answer = client.post(f"/api/v1/conversations/{conversation.json()['id']}/messages", headers=headers, json={"content": "住宿标准是多少？", "document_ids": []})
        assert answer.status_code == 200
        assert answer.json()["citations"]

        invitation = client.post("/api/v1/team/invitations", headers=headers, json={"email": "member@example.com", "role": "member"})
        assert invitation.status_code in (200, 409)
        assert client.get("/api/v1/team", headers=headers).status_code == 200
        analytics = client.get("/api/v1/analytics", headers=headers)
        assert analytics.status_code == 200
        assert analytics.json()["totals"]["meetings"] >= 1

        saved_key = client.put("/api/v1/settings/api-key", headers=headers, json={"api_key": "sk-test-abcdefghijklmnopqrstuvwxyz"})
        assert saved_key.status_code == 200
        assert saved_key.json()["key_hint"] != "sk-test-abcdefghijklmnopqrstuvwxyz"
        assert client.delete("/api/v1/settings/api-key", headers=headers).status_code == 200
