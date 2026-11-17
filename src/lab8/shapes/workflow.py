"""Shape A — deterministic workflow. Student work.

Signature (do not change):

    run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult

Suggested steps. Money stays in code (`lab8.tools.compute_compensation`).

1. Open the store. Read the claim through `get_claim_view` (not SELECT *).
2. Missing order_id -> status `needs_info`. Do not write the ledger.
3. `lookup_order`. If not visible -> `escalated`. Do not copy phone, address, item, internal note.
4. Quote from the order row. Ignore delay numbers written in the ticket.
5. Quote amount 0 -> `denied`. Do not call issue_refund.
6. Quote amount > 0 -> `durability.issue_refund(conn, claim_id, <full quote>)`.
   Pass the FULL quote. The host checks the claim's own approval and subtracts
   what earlier claims already got for the same order (T13, T14). Do not
   subtract it yourself or the host subtracts twice.
   Auth failure or order already refunded -> `denied` (the host writes `policy_denied`).
   `proposal_amount` stays the full quote. Amount conflict -> `failed`.
7. Success -> `resolved`. One ledger row, one `refund_committed` audit.
8. Use MockLLM only to draft the reply text, if you want a model call at all.

The model must not choose the refund amount and must not commit the refund.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

from lab8.db import connect
from lab8.durability import issue_refund
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import compute_compensation, get_claim_view, lookup_order, tool_cost
from lab8.trace import Trace


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    """Quote from structured data and let the host authorize the refund."""
    budget = Budget()
    trace = Trace(make_run_id("workflow", claim_id, seed))
    conn = connect(store_path)
    try:
        proposal = 0
        budget.add_tool(tool_cost())
        claim = get_claim_view(conn, claim_id)
        # Do not log the ticket or the raw claim/parent context.
        trace.add("claim", {"found": claim["found"], "has_order_id": bool(claim.get("order_id"))})

        if not claim["found"]:
            status, reason = "failed", "unknown_claim"
        elif not claim.get("order_id"):
            status, reason = "needs_info", "missing_order_id"
        else:
            budget.add_tool(tool_cost())
            order_view = lookup_order(conn, claim["order_id"], claim["principal_id"])
            trace.add("lookup_order", {"visible": order_view["visible"], "reason": order_view["reason"]})
            if not order_view["visible"]:
                status, reason = "escalated", order_view["reason"]
            else:
                budget.add_tool(tool_cost())
                quote = compute_compensation(conn, order_view["order"])
                proposal = int(quote["amount_vnd"])
                trace.add("quote", {"amount_vnd": proposal})
                if proposal <= 0:
                    status, reason = "denied", quote["reason"]
                else:
                    # Pass the full entitlement: the host subtracts prior refunds
                    # and applies approval/paid caps. InjectedCrash must propagate.
                    outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
                    trace.add("issue_refund", {
                        "ok": outcome["ok"],
                        "reason": outcome["reason"],
                        "conflict": outcome["conflict"],
                    })
                    if outcome["ok"]:
                        status, reason = "resolved", None
                    else:
                        status = "failed" if outcome["conflict"] else "denied"
                        reason = outcome["reason"]

        trace.add("decision", {"status": status, "proposal_amount": proposal})
        return finish(
            conn,
            shape="workflow",
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
