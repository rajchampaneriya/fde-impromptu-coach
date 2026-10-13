"""Version B: one model call with the right context. YOU fill this in on day 9.

Move your day 6 code here (copy and paste) so later notebooks can import it:
SYSTEM, user_message(case), SCHEMA and version_b(case).

Keep this exact signature. Later notebooks call it like this:

    from lab.version_b import version_b
    output = version_b(case, temperature=0.0, run=0)
    # -> {"intent": ..., "reply": ..., "needs_human": ..., "tokens_in": ..., "tokens_out": ..., "seconds": ...}

`temperature` and `run` are passed on to lab.llm.chat (project 6 uses them to measure randomness).
"""
from __future__ import annotations

from typing import Dict


def version_b(case: Dict, temperature: float = 0.0, run: int = 0, context: str = "oracle") -> Dict:
    # TODO (day 9): paste your day 6 version here. `context` is used in project 2:
    # "oracle" = the hand-picked articles (day 6), "retrieved" = articles from your own search (project 2).
    raise NotImplementedError("Day 9: paste your version B here")
