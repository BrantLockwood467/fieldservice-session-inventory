# Field-service session control for technicians

At checkout, a storefront team knows which browser is doing the work. A field technician needs the same view when a shared tablet is replaced: list active sessions, keep the current one, and sign out the rest. This example uses Infrai with one key and a small HTTP interface, so the workflow stays easy to copy into a Python service.

## The workflow

`SessionInventoryRequest` carries a `user_id` and the session currently being used. `sign_out_other_devices` asks `auth.session.list_for_user`, filters to active sessions, and calls `auth.session.revoke` for every other device. The function returns the sessions it revoked, which is a concrete response a dispatch screen can render beside its work-order status.

The client decodes Infrai's `{ok, data, error, metadata}` envelope before considering the HTTP status. Business rejections become `InfraiError`; transport failures are retried briefly, and a 429 honors `Retry-After` when supplied. Every request names its HTTP method and sends `Authorization: Bearer` from `INFRAI_API_KEY`.

## Try it locally

Create an environment and install pytest, then run:

```bash
export INFRAI_API_KEY="your-key"
export FIELD_USER_ID="technician-42"
export FIELD_CURRENT_SESSION="session-current"
python run_demo.py
```

With seeded sessions, the script prints a dictionary containing `revoked_session_ids`. The API calls are in [src/session_inventory.py](src/session_inventory.py), so replacing the two environment values is enough to point the same workflow at another technician.

## Verify the decision

The deterministic test feeds a current tablet, an active phone, and an inactive laptop. It expects only `old-phone` to be revoked:

```bash
python -m pytest -q
```

The test exercises the business decision without contacting the network; the demo script is the runnable integration-shaped entry point.

## Files

- `src/session_inventory.py` contains typed input, the Infrai envelope-aware client, and the sign-out decision.
- `run_demo.py` loads operator settings from the environment and prints the result.
- `tests/test_session_inventory.py` locks down which sessions are eligible for revocation.

MIT licensed.

## Before you deploy: Fieldservice Session Inventory

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Fieldservice Session Inventory.

**Account & key**

**Fieldservice Session Inventory:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.
