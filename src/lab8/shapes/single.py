"""Shape B — one ReAct agent. Student work.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.

A decide() that trusts ticket text over the order row will fail hidden claims
where the customer overstates the delay or cites a superseded clause.

Per-order cap: an order may already have been refunded by an earlier claim.
The read tool `lookup_refund_history` shows how much. The host still enforces
the cap, so pass the full quote to `durability.issue_refund`, not a net amount.

Caps: stop at 8 steps. Count model calls in the Budget so cost stays comparable.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

from typing import Any

from lab8.db import connect
from lab8.durability import issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    """Run a bounded read-only agent, then let the host commit its quote."""
    budget = Budget()
    trace = Trace(make_run_id("single", claim_id, seed))
    conn = connect(store_path)
    try:
        budget.add_tool(tool_cost())
        claim = get_claim_view(conn, claim_id)
        trace.add("claim", {"found": claim["found"], "has_order_id": bool(claim.get("order_id"))})

        def decide(observation: dict[str, Any]) -> dict[str, Any]:
            last_tool = observation.get("last_tool")
            result = observation.get("last_result") or {}
            # MockLLM has no structured tool-call output. The adapter below
            # selects a read action from observations; model usage is still counted.
            complete(
                budget,
                seed=seed,
                purpose="decide",
                prompt=(
                    f"last_tool={last_tool};found={claim['found']};"
                    f"has_order_id={bool(claim.get('order_id'))};"
                    f"visible={result.get('visible')};amount_vnd={result.get('amount_vnd')}"
                ),
            )
            if not claim["found"]:
                action = {"final": {"status": "failed", "error_reason": "unknown_claim"}}
            elif not claim.get("order_id"):
                action = {"final": {"status": "needs_info", "error_reason": "missing_order_id"}}
            elif last_tool is None:
                action = {"tool": "lookup_order", "args": {
                    "order_id": claim["order_id"], "principal_id": claim["principal_id"],
                }}
            elif last_tool == "lookup_order":
                if not result["visible"]:
                    action = {"final": {"status": "escalated", "error_reason": result["reason"]}}
                else:
                    action = {"tool": "compute_compensation", "args": {"order": result["order"]}}
            elif last_tool == "compute_compensation":
                # The quote comes from the deterministic tool, never from model text.
                action = {"final": {"quote": result}}
            else:
                action = {"final": {"status": "failed", "error_reason": "unexpected_tool_result"}}

            # Never record tool arguments, raw observations, or ticket text.
            trace.add("react_action", {"tool": action.get("tool"), "final": "final" in action})
            return action

        react = run_react(
            conn,
            budget,
            observation={},
            decide=decide,
            max_steps=8,
            worker=True,
        )
        final = react["final"]
        quote = final.get("quote")
        proposal = 0
        if quote is None:
            status = final["status"]
            reason = final.get("error_reason")
        else:
            proposal = int(quote["amount_vnd"])
            trace.add("quote", {"amount_vnd": proposal})
            if proposal <= 0:
                status, reason = "denied", quote["reason"]
            else:
                # Only code outside ReAct may write. Pass the full quote so the
                # host can check approval, subtract prior refunds, and deduplicate.
                outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
                trace.add("issue_refund", {
                    "ok": outcome["ok"], "reason": outcome["reason"], "conflict": outcome["conflict"],
                })
                if outcome["ok"]:
                    status, reason = "resolved", None
                else:
                    status = "failed" if outcome["conflict"] else "denied"
                    reason = outcome["reason"]

        trace.add("decision", {"status": status, "proposal_amount": proposal})
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=reason,
        )
    finally:
        conn.close()
