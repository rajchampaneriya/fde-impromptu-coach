"""Grader for Acme Fibre replies. YOU build this on day 5.

An output is a dict: {"intent": str, "reply": str, "needs_human": bool}.
A test case (data/acme/cases.jsonl) says what a correct output must contain.

The regular expressions below are given: they turn the rules in data/acme/policy.md
into patterns. Your job is the logic in policy_violations() and score().
Every later notebook uses this file, so keep it small and correct.
"""
from __future__ import annotations

import re
from typing import Dict, List

# Rule 2: an exact time or date for a fix ("within 2 hours", "by tonight", "by 5 pm")
TIME_PROMISE = re.compile(
    r"\b(within|in)\s+\d+\s*(hours?|hrs?|minutes?|mins?)\b"
    r"|\bby\s+(tonight|tomorrow|today|\d{1,2}(:\d{2})?\s*(am|pm))\b",
    re.IGNORECASE,
)
# Rule 4: asking the customer for a secret ("please share the OTP")
ASKS_SECRET = re.compile(
    r"\b(share|send|tell|give|provide)\b[^.?!]{0,40}\b(otp|password|card number|cvv)\b",
    re.IGNORECASE,
)
# Rule 3: words that sound like money was approved or paid out
APPROVAL_WORDS = re.compile(r"\b(approved|processed|refunded|credited)\b", re.IGNORECASE)
# Rupee amounts: "₹2,999", "Rs 500", "INR 1499"
AMOUNT = re.compile(r"(?:₹|\brs\.?|\binr)\s?(\d[\d,]*)", re.IGNORECASE)

CHECKS = ("intent_ok", "facts_ok", "policy_ok", "human_ok")


def amounts(text: str) -> List[int]:
    """All rupee amounts in the text: 'a refund of ₹2,999' -> [2999]."""
    return [int(a.replace(",", "")) for a in AMOUNT.findall(text or "")]


def policy_violations(reply: str) -> List[str]:
    """Names of the global policy rules this reply breaks (empty list = none)."""
    found: List[str] = []
    # TODO 1: if TIME_PROMISE finds a match in reply, add "exact_time_promise"
    # TODO 2: if ASKS_SECRET finds a match, add "asks_for_secret"
    # TODO 3: if APPROVAL_WORDS finds a match AND any amount in the reply is above 500, add "big_refund"
    return found


def score(case: Dict, output: Dict) -> Dict:
    """Grade one output against one test case."""
    output = output or {}
    reply = output.get("reply") or ""
    result = {"intent_ok": False, "facts_ok": False, "policy_ok": False, "human_ok": False,
              "violations": []}
    # TODO 4: intent_ok  -> the output's intent equals case["expected_intent"]
    # TODO 5: facts_ok   -> every phrase in case["must_include"] appears in the reply (ignore upper/lower case)
    # TODO 6: violations -> policy_violations(reply) plus "must_not: <phrase>" for each case["must_not"] phrase found
    #         policy_ok  -> no violations at all
    # TODO 7: human_ok   -> bool(output.get("needs_human")) equals case["needs_human"]
    result["passed"] = all(result[k] for k in CHECKS)
    return result


def summary(scores: List[Dict]) -> Dict[str, float]:
    """Share of outputs that pass each check, e.g. {"intent_ok": 0.8, ..., "passed": 0.5}."""
    n = max(1, len(scores))
    return {k: sum(bool(s[k]) for s in scores) / n for k in CHECKS + ("passed",)}
