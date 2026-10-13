"""Version C: the agent loop. YOU fill this in on day 9.

Move your day 8 code here (copy and paste): SYSTEM_C, MAX_STEPS and run_agent(case).

Keep this exact signature. Later notebooks call it like this:

    from lab.agent import run_agent
    output, trace = run_agent(case, temperature=0.0, run=0)
    # output -> {"intent": ..., "reply": ..., "needs_human": ...}
    # trace  -> one dict per model call: {"step": i, "tokens_in": ..., "tokens_out": ...,
    #                                     "seconds": ..., "tool_calls": [(name, args, result), ...]}
"""
from __future__ import annotations

from typing import Dict, List, Tuple

MAX_STEPS = 6


def run_agent(case: Dict, temperature: float = 0.0, run: int = 0) -> Tuple[Dict, List[Dict]]:
    # TODO (day 9): paste your day 8 loop here.
    raise NotImplementedError("Day 9: paste your agent loop here")
