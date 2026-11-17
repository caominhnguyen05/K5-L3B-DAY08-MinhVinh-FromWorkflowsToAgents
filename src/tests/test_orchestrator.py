"""Regression tests for orchestrator control flow and host authorization."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lab8.db import connect
from lab8.shapes.orchestrator import run_claim


def test_unknown_claim_returns_failed_with_trace(public_db):
    result = run_claim("C-UNKNOWN", seed=11, store_path=str(public_db))

    assert result.status == "failed"
    assert result.error_reason == "unknown_claim"
    assert result.trace_path


def test_missing_order_returns_needs_info_before_handoff(public_db):
    result = run_claim("C-004", seed=11, store_path=str(public_db))
    events = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))["events"]

    assert result.status == "needs_info"
    assert not any(event["kind"] == "handoff" for event in events)


def test_zero_quote_is_denied_without_refund(public_db):
    result = run_claim("C-002", seed=11, store_path=str(public_db))

    assert result.status == "denied"
    assert result.proposal_amount == 0
    assert result.refund_effects == []


@pytest.mark.parametrize(
    ("sql", "expected_reason"),
    [
        ("UPDATE approvals SET status='revoked' WHERE approval_id='A-001'", "approval_revoked"),
        ("UPDATE claims SET approval_id='A-007' WHERE claim_id='C-001'", "approval_claim_mismatch"),
    ],
)
def test_denial_paths_write_policy_audit(public_db, sql, expected_reason):
    conn = connect(public_db)
    try:
        conn.execute(sql)
        conn.commit()
    finally:
        conn.close()

    result = run_claim("C-001", seed=11, store_path=str(public_db))
    conn = connect(public_db)
    try:
        audit = conn.execute(
            "SELECT details_json FROM audit_events "
            "WHERE claim_id='C-001' AND event_type='policy_denied'"
        ).fetchone()
    finally:
        conn.close()

    assert result.status == "denied"
    assert audit is not None and expected_reason in audit["details_json"]
