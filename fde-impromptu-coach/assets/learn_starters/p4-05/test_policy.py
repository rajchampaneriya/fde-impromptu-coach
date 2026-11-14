"""Tests for policy/refunds.cedar. Run: uv run pytest 4-production-shaped-agent/05-identity-and-policy/test_policy.py -v"""
from pathlib import Path

import cedarpy

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "policy").is_dir())
POLICIES = (ROOT / "policy" / "refunds.cedar").read_text()


def decide(principal, amount, customer, email_customer):
    request = {"principal": principal, "action": 'Action::"issue_refund"', "resource": 'Refund::"r1"',
               "context": {"email_customer_id": email_customer}}
    entities = [{"uid": {"type": "Refund", "id": "r1"},
                 "attrs": {"amount_inr": amount, "customer_id": customer}, "parents": []}]
    return cedarpy.is_authorized(request, POLICIES, entities).decision == cedarpy.Decision.Allow


def test_agent_small_refund_allowed():
    assert decide('Agent::"acme-support-agent"', 300, "AC1002", "AC1002")


def test_agent_big_refund_denied():
    assert not decide('Agent::"acme-support-agent"', 900, "AC1002", "AC1002")


# TODO: at least 6 more: another customer, exactly ₹500, a billing approver above ₹500, an unknown principal …
