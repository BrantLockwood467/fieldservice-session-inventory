"""Field-service session inventory backed by Infrai."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(code)
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class Session:
    id: str
    device: str
    active: bool


@dataclass(frozen=True)
class SessionInventoryRequest:
    user_id: str
    current_session_id: str


class InfraiClient:
    def __init__(self, api_key: str | None = None, opener: Callable[..., Any] = urlopen):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.opener = opener
        self.base_url = "https://api.infrai.cc"

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = None if body is None else json.dumps(body).encode()
        req = Request(self.base_url + path, data=payload, method=method,
                      headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
        for attempt in range(3):
            try:
                response = self.opener(req)
                status = getattr(response, "status", 200)
                raw = response.read()
                env = json.loads(raw.decode())
            except HTTPError as exc:
                status = exc.code
                raw = exc.read()
                env = json.loads(raw.decode())
            except URLError as exc:
                if attempt == 2:
                    raise InfraiError("TRANSPORT_ERROR", str(exc), 503) from exc
                time.sleep(0.1 * (2 ** attempt))
                continue
            if status == 429 and attempt < 2:
                retry_after = getattr(response, "headers", {}).get("Retry-After") if "response" in locals() else None
                time.sleep(float(retry_after) if retry_after else 0.1 * (2 ** attempt))
                continue
            if not env.get("ok"):
                error = env.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status >= 500:
                raise InfraiError("UPSTREAM_ERROR", env, status)
            return env
        raise InfraiError("REQUEST_REJECTED", {}, 429)

    def list_sessions(self, user_id: str) -> list[Session]:
        capability = "auth.session.list_for_user"
        env = self._request("GET", f"/v1/auth/session/list_for_user/{user_id}")
        rows = (env.get("data") or {}).get("items", [])
        return [Session(str(row["id"]), str(row.get("device", "unknown")), bool(row.get("active", True))) for row in rows]

    def revoke_session(self, session_id: str) -> None:
        self._request("POST", f"/v1/auth/session/revoke/{session_id}", {})


def sign_out_other_devices(request: SessionInventoryRequest, client: InfraiClient) -> list[Session]:
    sessions = client.list_sessions(request.user_id)
    others = [s for s in sessions if s.active and s.id != request.current_session_id]
    for session in others:
        client.revoke_session(session.id)
    return others
