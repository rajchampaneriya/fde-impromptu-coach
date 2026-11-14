"""Acme's tools as an MCP server. YOU fill this in (project 4, step 1).

Run it:            uv run lab/mcp_server.py
Inspect it:        npx @modelcontextprotocol/inspector uv run lab/mcp_server.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp.server.mcpserver import MCPServer  # noqa: E402

from lab import acme_tools  # noqa: E402

mcp = MCPServer("acme-fibre")
REFUNDS: Dict[str, Dict] = {}      # idempotency_key -> the first result (a real server keeps this in a database)
PAID: list = []                    # what was actually paid; tests read it


@mcp.tool()
def lookup_customer(customer_id: str) -> Dict:
    """Get a customer's record and any outage in their area right now. Call this first for every email."""
    return acme_tools.lookup_customer(customer_id)


# TODO: search_kb(query: str, k: int = 2), get_article(article_id: str) and escalate(reason: str), the same way


@mcp.tool()
def issue_refund(customer_id: str, amount_inr: int, reason: str, idempotency_key: str) -> Dict:
    """Refund money to a customer. Above ₹500 the refund waits for a human: it is never paid here."""
    # TODO 1: if idempotency_key is in REFUNDS, return the stored result (never pay twice)
    # TODO 2: above 500, result = {"status": "pending_approval", ...}; otherwise append to PAID and
    #         result = {"status": "refunded", "amount_inr": amount_inr}
    # TODO 3: store the result under idempotency_key and return it
    raise NotImplementedError


if __name__ == "__main__":
    mcp.run()
