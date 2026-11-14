"""The API behind the operator console. YOU fill this in (project 4, step 4).

Run it:  uv run uvicorn lab.approvals:app --reload --port 8000
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "data" / "audit" / "approvals.jsonl"

app = FastAPI()
PENDING: Dict[str, Dict] = {}      # approval id -> the refund the agent asked for
DECIDED: Dict[str, Dict] = {}      # approval id -> the decision (makes Approve idempotent)


@app.get("/run/{case_id}")
def run(case_id: str):
    """Stream version C's steps as server-sent events: one `data: {...}` line per step."""
    def events():
        # TODO: run the agent step by step; yield f"data: {json.dumps(step)}\n\n" for each model and tool call.
        #       A refund above ₹500 goes into PENDING instead of being paid.
        yield f"data: {json.dumps({'todo': 'stream the agent here'})}\n\n"
    return StreamingResponse(events(), media_type="text/event-stream")


@app.get("/approvals")
def approvals():
    return list(PENDING.values())


@app.post("/approvals/{approval_id}/{decision}")
def decide(approval_id: str, decision: str, user: str = "support-lead"):
    # TODO: if approval_id is already in DECIDED, return that decision (a double click pays once).
    #       Otherwise record {"id", "decision", "user", "at": time.time()} in DECIDED, append it to AUDIT,
    #       remove it from PENDING and return it.
    raise NotImplementedError
