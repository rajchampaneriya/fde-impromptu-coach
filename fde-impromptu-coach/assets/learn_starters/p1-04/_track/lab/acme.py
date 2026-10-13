"""Acme Fibre data loaders (given on day 4: plumbing, not the lesson).

Everything reads from data/acme/. Results of each version (A, B, C, …) are saved
as JSON lines in data/results/ so later notebooks can compare them.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "acme"
RESULTS = ROOT / "data" / "results"

INTENTS = ["billing", "outage", "speed", "cancel", "upgrade", "relocation", "other"]

# "Oracle" context: the help articles a perfect search would find for each intent.
# Version B uses this on day 6. Project 2 replaces it with real retrieval.
INTENT_KB = {
    "billing": ["KB01", "KB02", "KB04"],
    "outage": ["KB05", "KB06"],
    "speed": ["KB07", "KB08"],
    "cancel": ["KB10", "KB11"],
    "upgrade": ["KB09"],
    "relocation": ["KB12"],
    "other": ["KB13", "KB15", "KB16"],
}


def load_cases(path: Optional[Path] = None) -> List[Dict]:
    lines = (path or DATA / "cases.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def load_customers() -> Dict[str, Dict]:
    return {c["id"]: c for c in json.loads((DATA / "customers.json").read_text(encoding="utf-8"))}


def load_outages() -> Dict[str, Dict]:
    return {o["area"]: o for o in json.loads((DATA / "outages.json").read_text(encoding="utf-8"))}


def load_kb() -> List[Dict]:
    """[{"id": "KB01", "title": "Billing cycle and due dates", "text": "..."}, ...]"""
    articles = []
    for block in re.split(r"^# ", (DATA / "kb.md").read_text(encoding="utf-8"), flags=re.M):
        if not block.strip():
            continue
        head, _, body = block.partition("\n")
        kb_id, _, title = head.partition(" · ")
        articles.append({"id": kb_id.strip(), "title": title.strip(), "text": body.strip()})
    return articles


def kb_by_id() -> Dict[str, Dict]:
    return {a["id"]: a for a in load_kb()}


def first_name(customer: Dict) -> str:
    return customer["name"].split()[0]


def outage_for(customer: Dict) -> Optional[Dict]:
    """The outage in the customer's area right now, or None."""
    return load_outages().get(customer["area"])


def customer_card(customer: Dict) -> str:
    """A short text description of one customer, for prompts."""
    lines = [
        f"Customer: {customer['name']} (first name: {first_name(customer)}, id {customer['id']})",
        f"Area: {customer['area']} · Plan: {customer['plan']} · Status: {customer['status']}",
        f"Tenure: {customer['tenure_months']} months · Balance due: ₹{customer['balance_due']}",
        f"Complaints in the last 30 days: {customer['complaints_last_30_days']}",
    ]
    outage = outage_for(customer)
    if outage:
        lines.append(f"Outage in {outage['area']}: ticket {outage['ticket']}, since {outage['since']}. "
                     f"Cause: {outage['cause']}. Status: {outage['status']}")
    else:
        lines.append(f"No known outage in {customer['area']}.")
    return "\n".join(lines)


def save_results(version: str, rows: List[Dict]) -> Path:
    """Save one version's outputs (one dict per case) to data/results/<version>.jsonl."""
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"{version}.jsonl"
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    return path


def load_results(version: str) -> List[Dict]:
    path = RESULTS / f"{version}.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"No saved results for version {version!r} yet ({path})")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
