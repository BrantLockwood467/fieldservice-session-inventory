import json

from src.session_inventory import InfraiClient, Session, SessionInventoryRequest, sign_out_other_devices


class FakeClient:
    def __init__(self):
        self.revoked = []

    def list_sessions(self, user_id):
        assert user_id == "tech-7"
        return [Session("current", "tablet", True), Session("old-phone", "phone", True), Session("expired", "laptop", False)]

    def revoke_session(self, session_id):
        self.revoked.append(session_id)


def test_sign_out_other_devices_keeps_current_and_inactive_sessions():
    client = FakeClient()
    revoked = sign_out_other_devices(SessionInventoryRequest("tech-7", "current"), client)
    assert [s.id for s in revoked] == ["old-phone"]
    assert client.revoked == ["old-phone"]


def test_list_sessions_reads_live_items_shape():
    class Response:
        status = 200

        def read(self):
            return json.dumps({"ok": True, "data": {"items": [
                {"id": "current", "device": "tablet", "active": True},
                {"id": "expired", "device": "laptop", "active": False},
            ]}}).encode()

    client = InfraiClient(api_key="test", opener=lambda request: Response())
    assert client.list_sessions("tech-7") == [
        Session("current", "tablet", True), Session("expired", "laptop", False)
    ]
