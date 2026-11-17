"""Orchestrator ablation without the read-only refund-history investigator."""

from __future__ import annotations

from lab8.db import connect
from lab8.shapes.orchestrator import _run
from lab8.schemas import RunResult

ALLOWED_TOOLS = ["lookup_order", "lookup_policy", "compute_compensation"]


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(
            conn,
            claim_id,
            seed=seed,
            crash_at=crash_at,
            shape="orchestrator_no_history",
            allowed_tools=ALLOWED_TOOLS,
        )
    finally:
        conn.close()
