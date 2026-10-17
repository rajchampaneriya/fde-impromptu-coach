#!/usr/bin/env python3
"""Stand-in for the `claude` CLI used by the tests: reads the slot plan from the
prompt and answers with a Claude-Code-style JSON envelope.

FAKE_CLAUDE_MODE: ok (default) | error | garbage | dupes | partial | fenced | wrong_listener
Also answers the pronunciation annotation prompts (library mode) and the exec
answer key prompt (FAKE_CLAUDE_ANSWERS: ok (default) | long | error | garbage | partial).
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
LISTENERS = {"exec": [("CFO", "cost and return"), ("COO", "operations on time"), ("CEO", "growth and risk")],
             "account_leader": [("account executive", "the renewal"), ("account director", "the deal")]}
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
    if "# Answer key slots" in prompt:
        return answer_key(prompt)
    if "pronunciation annotation" in prompt.lower():
        return annotate(prompt)
    if "pronunciation practice" in prompt.lower():
        return pronounce(prompt, mode)
    slots = re.findall(r"- slot (\d+): category `([a-z_]+)`[^\n]*difficulty (\d)(?:, listener `([a-z_]+)`)?", prompt)
    rng = random.Random(prompt[-4000:] + os.environ.get("FAKE_CLAUDE_SALT", ""))
    questions = []
    for n, (slot, cat, diff, aud) in enumerate(slots):
        if mode == "partial" and n % 2:
            continue
        if mode == "dupes":
            text = ("An outage has blocked the customer's support team for three hours during their busiest "
                    "week. Their director calls you, angry. Respond.")
        else:
            calm = [x for x in PEOPLE if x not in ("COO", "CISO", "VP of engineering", "chief nursing officer")]
            person = (rng.choice(LISTENERS[aud])[0] if aud in LISTENERS else
                      rng.choice(calm if f"slot {slot}: " in prompt and "not an executive" in
                                 prompt.split(f"slot {slot}: ", 1)[1].split("\n", 1)[0] else PEOPLE))
            who = f"Your {person}" if aud == "account_leader" else f"Their {person}"
            text = (f"You are embedded with {rng.choice(SCENES)} ({rng.randint(100, 999)} staff) and "
                    f"{rng.choice(TWISTS)}. {who} asks what you recommend "
                    f"in case {rng.randint(1000, 9999)}. Respond.")
        item = {"slot": int(slot), "category": cat, "difficulty": int(diff), "format": "roleplay",
                "text": text, "constraint": "Lead with your recommendation." if int(diff) >= 3 else "",
                "coach_note": "Recommendation first, one fact, one risk, one clear next step."}
        if aud in LISTENERS and mode != "dupes":
            listener, cares = next((p, c) for p, c in LISTENERS[aud] if p in text)
            item.update(audience="technical_peer" if mode == "wrong_listener" else aud,
                        listener=listener[0].upper() + listener[1:], cares=cares)
        questions.append(item)
    body = json.dumps({"questions": questions})
    if mode == "fenced":
        body = "Here you go:\n```json\n" + body + "\n```"
    print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": body}))
    return 0


def answer_key(prompt: str) -> int:
    """Model answers that pass the rubric: 'long' writes an 87-word exec answer (rejected),
    'partial' answers only the first slot."""
    mode = os.environ.get("FAKE_CLAUDE_ANSWERS", "ok")
    if mode == "error":
        print(json.dumps({"type": "result", "is_error": True, "result": "usage limit reached"}))
        return 0
    if mode == "garbage":
        print("Sorry, no.")
        return 0
    body_text = prompt.split("# Answer key slots", 1)[1]
    blocks = re.split(r"\n(?=- slot \d+ )", body_text)
    answers = []
    for block in blocks:
        m = re.match(r"- slot (\d+) \u00b7 listener: ([^(\n]+)", block.strip())
        if not m:
            continue
        slot, listener = int(m.group(1)), m.group(2).strip()
        so_what = "It keeps your launch date safe and your team out of firefighting next week."
        if mode == "long":
            so_what += (" There is also a long technical story about queues, retries, certificates, regions, "
                        "caches, failover drills, the batch scheduler and the way the vendor's model handles "
                        "context windows, which matters a great deal to anyone who runs it in production.")
        item = {
            "slot": slot,
            "headline": f"The pilot works; I need one decision from you by Friday, {listener}.",
            "answer": [
                {"move": "headline", "text": "The pilot works, and we can go live on the 15th."},
                {"move": "so_what", "text": so_what},
                {"move": "ask", "text": "I need your approval for the data access by Friday."},
                {"move": "offer", "text": "Happy to walk you through the numbers if useful."},
            ],
            "detail": ["Accuracy rose from 81% to 93% on 400 reviewed cases.",
                       "The access request covers two read-only tables."],
            "trap": "Opening with the model architecture: the listener hears complexity, not a decision.",
        }
        if "write `reply_answer`" in block:
            item["reply_answer"] = "The data access. Without it by Friday, go-live moves a week."
        answers.append(item)
        if mode == "partial":
            break
    print(json.dumps({"type": "result", "subtype": "success", "is_error": False,
                      "result": json.dumps({"answers": answers})}))
    return 0


def pronounce(prompt: str, mode: str) -> int:
    """Valid paragraph for the pronunciation rubric; 'dupes' always returns the
    same paragraph so the novelty check rejects it."""
    if mode == "dupes":
        words = ["hierarchy", "prioritize", "verdict", "threshold", "algorithm"]
    else:
        words = re.findall(r"^- ([a-z']+)$", prompt, re.MULTILINE)
        if len(words) < 5:
            words = (words + ["colleague", "articulate", "rhythm", "paradigm", "suite"])[:5]
    rng = random.Random(prompt[-2000:] + os.environ.get("FAKE_CLAUDE_SALT", ""))
    leads = ["This morning the customer asked about", "Yesterday's review surfaced",
             "The quarterly plan hinges on", "Their lead engineer questioned our",
             "The migration checklist starts with", "Nobody on the call could settle the"]
    tails = ["before the board call", "during the pilot review", "after the incident drill",
             "in front of the auditors", "before Friday's demo", "during the vendor call"]
    sentences = ["Let me give you the short version of where we stand this week."]
    for i, w in enumerate(words):
        sentences.append(f"{rng.choice(leads)} the {w} question, and the same {w} concern returned "
                         f"{rng.choice(tails)}.")
        if i == 2:
            sentences.append("I wrote the numbers down twice, checked them twice, and kept the slide to one line.")
    sentences.append("That is the whole update: clear words, plain numbers, and a decision we can defend.")
    body = json.dumps({
        "paragraph": " ".join(sentences),
        "target_words": [{"word": w, "respelling": w.upper(), "stress": w.upper(),
                          "tip": "Slow down on this word."} for w in words],
        "focus_sounds": ["th"],
    })
    print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": body}))
    return 0


def annotate(prompt: str) -> int:
    """Library mode: Claude only marks up words. Passage mode picks the five
    longest words of the passage; word mode annotates the listed words."""
    if "# Passage (copy words exactly from here)" in prompt:
        text = prompt.split("# Passage (copy words exactly from here)", 1)[1].split("Return only")[0]
        words = []
        for w in sorted(set(re.findall(r"[A-Za-z]{4,}", text)), key=lambda x: (-len(x), x)):
            if w.lower() not in words:
                words.append(w.lower())
        words = words[:5]
    else:
        block = prompt.split("# Words to annotate", 1)[1].split("Return only")[0]
        words = re.findall(r"^- ([a-z']+)$", block, re.MULTILINE)
    body = json.dumps({"target_words": [{"word": w, "respelling": w.upper(), "stress": w.upper(),
                                         "tip": "Slow down on this word."} for w in words],
                       "focus_sounds": ["stress"]})
    print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": body}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
