import os

from src.session_inventory import InfraiClient, SessionInventoryRequest, sign_out_other_devices


def main() -> None:
    user_id = os.environ.get("FIELD_USER_ID", "technician-42")
    current = os.environ.get("FIELD_CURRENT_SESSION", "session-current")
    revoked = sign_out_other_devices(SessionInventoryRequest(user_id, current), InfraiClient())
    print({"user_id": user_id, "revoked_session_ids": [s.id for s in revoked]})


if __name__ == "__main__":
    main()
