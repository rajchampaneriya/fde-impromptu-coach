#!/usr/bin/env python3
"""Stand-in for the `claude` CLI used by the tests: reads the slot plan from the
prompt and answers with a Claude-Code-style JSON envelope.

FAKE_CLAUDE_MODE: ok (default) | error | garbage | dupes | partial | fenced
"""
import json
import os
import random
import re
import sys

SCENES = ["a logistics customer", "a regional bank", "a hospital network", "a retail chain", "an insurer",
          "a utility company", "a biotech lab", "a city transit agency", "an airline", "a law firm",
          "a manufacturing plant", "a telecom operator", "a university", "a shipping port", "a food distributor"]
PEOPLE = ["COO", "CISO", "head of claims", "night-shift supervisor", "procurement director", "general counsel",
          "VP of engineering", "chief nursing officer", "plant manager", "data protection officer"]
TWISTS = ["the pilot missed its accuracy target by 7%", "their board meets tomorrow morning",
          "a competitor just offered a free proof of concept", "the integration exposed a data-retention gap",
          "two of their teams want opposite things", "your own estimate slipped by three weeks",
          "the champion who sponsored you just resigned", "usage fell 35% after the last release"]


def main() -> int:
    prompt = sys.argv[sys.argv.index("-p") + 1] if "-p" in sys.argv else sys.stdin.read()
    mode = os.environ.get("FAKE_CLAUDE_MODE", "ok")
    if mode == "error":
        print(json.dumps({"type": "result", "is_error": True, "result": "usage limit reached"}))
        return 0
    if mode == "garbage":
        print("I cannot help with that")
        return 0
    slots = re.findall(r"- slot (\d+): category `([a-z_]+)`[^\n]*difficulty (\d)", prompt)
    rng = random.Random(prompt[-4000:] + os.environ.get("FAKE_CLAUDE_SALT", ""))
    questions = []
    for n, (slot, cat, diff) in enumerate(slots):
        if mode == "partial" and n % 2:
            continue
        if mode == "dupes":
            text = ("An outage has blocked the customer's support team for three hours during their busiest "
                    "week. Their director calls you, angry. Respond.")
        else:
            text = (f"You are embedded with {rng.choice(SCENES)} ({rng.randint(100, 999)} staff) and "
                    f"{rng.choice(TWISTS)}. Their {rng.choice(PEOPLE)} asks what you recommend "
                    f"in case {rng.randint(1000, 9999)}. Respond.")
        questions.append({"slot": int(slot), "category": cat, "difficulty": int(diff), "format": "roleplay",
                          "text": text, "constraint": "Lead with your recommendation." if int(diff) >= 3 else "",
                          "coach_note": "Recommendation first, one fact, one risk, one clear next step."})
    body = json.dumps({"questions": questions})
    if mode == "fenced":
        body = "Here you go:\n```json\n" + body + "\n```"
    print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": body}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
