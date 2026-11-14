"""Tests for lab/mcp_server.py. Run from your fde-first-principles folder:
    uv run pytest 4-production-shaped-agent/01-mcp-server/test_mcp_server.py -v
"""
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "lab").is_dir())
sys.path.insert(0, str(ROOT))

from lab import mcp_server  # noqa: E402


def setup_function():
    mcp_server.REFUNDS.clear()
    mcp_server.PAID.clear()


def test_same_key_never_pays_twice():
    first = mcp_server.issue_refund("AC1002", 100, "late fee", "key-1")
    second = mcp_server.issue_refund("AC1002", 100, "late fee", "key-1")
    assert first == second
    assert len(mcp_server.PAID) == 1


def test_big_refund_is_never_paid():
    result = mcp_server.issue_refund("AC1006", 2999, "outage", "key-2")
    assert result["status"] == "pending_approval"
    assert mcp_server.PAID == []


# TODO: a test that lookup_customer on an unknown id returns an error instead of raising
