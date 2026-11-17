"""Orchestrator with a bounded, read-only investigator handoff."""

from __future__ import annotations

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.handoff import make_handoff
from lab8.mock_llm import complete
from lab8.runtime import run_readonly_investigators
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace

ALLOWED_INVESTIGATOR_TOOLS = [
    "lookup_order",
    "lookup_policy",
    "lookup_refund_history",
    "compute_compensation",
]


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run(
    conn,
    claim_id: str,
    *,
    seed: int,
    crash_at: str | None,
    shape: str = "orchestrator",
    allowed_tools: list[str] | None = None,
) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id(shape, claim_id, seed))
    budget.add_tool(tool_cost())
    claim = get_claim_view(conn, claim_id)
    if not claim.get("found"):
        trace.add("error", {"reason": "unknown_claim"})
        return finish(conn, shape=shape, claim_id=claim_id, seed=seed,
                      status="failed", proposal_amount=0, budget=budget, trace=trace,
                      error_reason="unknown_claim")

    complete(budget, seed=seed, purpose="plan", prompt="check claim and current policy")
    if not claim.get("order_id"):
        complete(budget, seed=seed, purpose="draft", prompt="needs_info")
        trace.add("decision", {"status": "needs_info"})
        return finish(conn, shape=shape, claim_id=claim_id, seed=seed,
                      status="needs_info", proposal_amount=0, budget=budget, trace=trace,
                      error_reason="missing_order_id")

    handoff = make_handoff(
        request_id=f"REQ-{claim_id}",
        claim_id=claim_id,
        task="check_applicable_policy_and_quote_compensation",
        facts={},
        allowed_tools=(
            ALLOWED_INVESTIGATOR_TOOLS if allowed_tools is None else allowed_tools
        ),
    )
    trace.add("handoff", safe_dump(handoff))
    investigated = run_readonly_investigators(
        conn, budget, handoff, principal_id=claim["principal_id"]
    )
    tools = investigated["tools"]
    order_view = tools.get("lookup_order", {})
    trace.add("investigator", {
        "lookup_order": order_view,
        "policy_count": len((tools.get("lookup_policy") or {}).get("policies") or []),
        "refund_history": tools.get("lookup_refund_history"),
    })
    if not order_view.get("visible"):
        complete(budget, seed=seed, purpose="draft", prompt="escalated")
        trace.add("decision", {"status": "escalated"})
        return finish(conn, shape=shape, claim_id=claim_id, seed=seed,
                      status="escalated", proposal_amount=0, budget=budget, trace=trace,
                      error_reason=order_view.get("reason"))

    quote_payload = tools.get("compute_compensation") or {"amount_vnd": 0, "reason": "quote_unavailable"}
    proposal = int(quote_payload.get("amount_vnd", 0))
    trace.add("quote", quote_payload)
    complete(budget, seed=seed, purpose="draft", prompt=f"proposal={proposal}")
    if proposal == 0:
        trace.add("decision", {"status": "denied"})
        return finish(conn, shape=shape, claim_id=claim_id, seed=seed,
                      status="denied", proposal_amount=0, budget=budget, trace=trace,
                      error_reason=quote_payload.get("reason"))

    try:
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise
    if outcome["ok"]:
        status = "resolved"
    elif outcome.get("conflict"):
        status = "failed"
    else:
        status = "denied"
    trace.add("decision", {"status": status, "reason": outcome.get("reason")})
    return finish(conn, shape=shape, claim_id=claim_id, seed=seed,
                  status=status, proposal_amount=proposal, budget=budget, trace=trace,
                  error_reason=None if outcome["ok"] else outcome.get("reason"))
