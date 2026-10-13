"""Tools the Acme agent can call (given on day 8).

Day 8 is about the loop, not the tools, so these are ready-made. Each tool is
1) a plain Python function and 2) a JSON schema that tells the model what it does.
The model never runs anything: it only writes "please call search_kb with {...}".
Your loop decides whether to run it.

search_kb() is deliberately simple (word overlap). In project 2 you build a real one.
"""
from __future__ import annotations

import re
from typing import Dict, List

from .acme import first_name, kb_by_id, load_customers, load_kb, outage_for

_WORD = re.compile(r"[a-z0-9]+")
_STOP = {"the", "a", "an", "is", "are", "my", "i", "to", "of", "and", "or", "in", "on", "for", "it",
         "me", "be", "can", "do", "how", "what", "with", "this", "that", "you", "your", "hai", "ka", "ki"}


def _words(text: str) -> set:
    return {w for w in _WORD.findall(text.lower()) if w not in _STOP}


def lookup_customer(customer_id: str) -> Dict:
    """Customer record plus any outage in their area right now."""
    customer = load_customers().get(str(customer_id).strip().upper())
    if customer is None:
        return {"error": f"No customer with id {customer_id!r}"}
    return dict(customer, first_name=first_name(customer), current_outage=outage_for(customer))


def search_kb(query: str, k: int = 2) -> List[Dict]:
    """The k help articles that share the most words with the query."""
    q = _words(query)
    scored = sorted(load_kb(), key=lambda a: -len(q & _words(a["title"] + " " + a["text"])))
    return [{"id": a["id"], "title": a["title"], "text": a["text"]} for a in scored[:max(1, int(k))]]


def get_article(article_id: str) -> Dict:
    """One help article by id, e.g. KB05."""
    return kb_by_id().get(str(article_id).strip().upper(), {"error": f"No article {article_id!r}"})


def escalate(reason: str) -> Dict:
    """Hand the case to a human agent."""
    return {"escalated": True, "reason": reason, "queue": "human-support"}


FUNCTIONS = {
    "lookup_customer": lookup_customer,
    "search_kb": search_kb,
    "get_article": get_article,
    "escalate": escalate,
}

TOOLS = [
    {"type": "function", "function": {
        "name": "lookup_customer",
        "description": "Get a customer's record (name, area, plan, tenure, balance, complaints) and any outage "
                       "in their area right now. Call this first for every email.",
        "parameters": {"type": "object", "properties": {
            "customer_id": {"type": "string", "description": "Customer id like AC1003"}},
            "required": ["customer_id"]}}},
    {"type": "function", "function": {
        "name": "search_kb",
        "description": "Search Acme Fibre's help articles (billing, outages, speed, plans, cancellation, "
                       "shifting, Wi-Fi, security, escalation). Returns the best matching articles.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "What to look for, in plain English"},
            "k": {"type": "integer", "description": "How many articles to return (default 2)"}},
            "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "get_article",
        "description": "Read one help article by its id (KB01 to KB16).",
        "parameters": {"type": "object", "properties": {
            "article_id": {"type": "string", "description": "Article id like KB05"}},
            "required": ["article_id"]}}},
    {"type": "function", "function": {
        "name": "escalate",
        "description": "Send this case to a human agent. Use for legal threats, threats to leave after repeated "
                       "complaints, refunds or credits above ₹500, and possible fraud.",
        "parameters": {"type": "object", "properties": {
            "reason": {"type": "string", "description": "One sentence: why a human is needed"}},
            "required": ["reason"]}}},
]
