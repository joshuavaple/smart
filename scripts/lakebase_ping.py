"""Ping Lakebase before starting the agent server.

Re-enables a disabled autoscaling endpoint, then opens one real connection.
That first connection also restores an archived branch (Free Edition archives
branches after a period of inactivity). Exits non-zero on failure so
`make server` stops before the server's pool hides the cause behind a
PoolTimeout.

Usage: python scripts/lakebase_ping.py
"""

import sys
import time
from pathlib import Path

import psycopg
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.postgres import Endpoint, EndpointSpec, EndpointType
from databricks_ai_bridge.lakebase import _LakebaseBase
from dotenv import load_dotenv
from google.protobuf.field_mask_pb2 import FieldMask

from smart_agent.utils_memory import init_lakebase_config

ROOT = Path(__file__).resolve().parent.parent
CONNECT_DEADLINE_SECONDS = 90
RETRY_INTERVAL_SECONDS = 10


def _log(msg: str) -> None:
    print(f"[lakebase-ping] {msg}", flush=True)


def _ensure_endpoint_enabled(w: WorkspaceClient, endpoint_name: str) -> None:
    endpoint = w.postgres.get_endpoint(name=endpoint_name)
    if not endpoint.status.disabled:
        return

    _log(f"endpoint {endpoint_name} is disabled, re-enabling...")
    w.postgres.update_endpoint(
        name=endpoint_name,
        endpoint=Endpoint(
            name=endpoint_name,
            spec=EndpointSpec(endpoint_type=EndpointType.ENDPOINT_TYPE_READ_WRITE, disabled=False),
        ),
        update_mask=FieldMask(paths=["spec.disabled"]),
    ).wait()
    _log("endpoint re-enabled")


def _connect_with_retry(lakebase: _LakebaseBase) -> float:
    """Connect and run SELECT 1, retrying until the deadline. Returns elapsed seconds."""
    start = time.monotonic()
    token = lakebase._mint_token()
    while True:
        try:
            with psycopg.connect(lakebase._conninfo(), password=token, connect_timeout=30) as conn:
                conn.execute("SELECT 1")
            return time.monotonic() - start
        except psycopg.OperationalError as exc:
            reason = str(exc).strip().splitlines()[0]
            elapsed = time.monotonic() - start
            if elapsed + RETRY_INTERVAL_SECONDS > CONNECT_DEADLINE_SECONDS:
                raise RuntimeError(f"could not connect after {elapsed:.0f}s: {reason}") from exc
            _log(f"not ready yet ({reason}), retrying in {RETRY_INTERVAL_SECONDS}s...")
            time.sleep(RETRY_INTERVAL_SECONDS)


def main() -> int:
    load_dotenv(ROOT / ".env")
    load_dotenv(ROOT / "src" / "smart_agent" / "memory.env")
    config = init_lakebase_config()

    try:
        w = WorkspaceClient()
        w.current_user.me()
    except Exception as exc:
        _log(f"Databricks auth failed: {exc}\nRe-run `databricks auth login` for your profile.")
        return 1

    try:
        lakebase = _LakebaseBase(
            instance_name=config.instance_name,
            autoscaling_endpoint=config.autoscaling_endpoint,
            project=config.autoscaling_project,
            branch=config.autoscaling_branch,
            workspace_client=w,
        )
        # Only autoscaling endpoints can be disabled/archived; provisioned instances skip this.
        if lakebase._endpoint_name:
            _ensure_endpoint_enabled(w, lakebase._endpoint_name)
        elapsed = _connect_with_retry(lakebase)
    except Exception as exc:
        _log(f"FAILED for {config.description}: {exc}")
        return 1

    status = ""
    if lakebase._endpoint_name:
        branch_name = lakebase._endpoint_name.rsplit("/endpoints/", 1)[0]
        branch_state = w.postgres.get_branch(name=branch_name).status.current_state
        endpoint_state = w.postgres.get_endpoint(name=lakebase._endpoint_name).status.current_state
        status = f": branch {branch_state.value}, endpoint {endpoint_state.value}"
    _log(f"OK{status} ({elapsed:.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
