# Exec Answer Key Rubric — model answers after the session

Use this whenever you write the model answers the learner reads straight after
recording (interactively or in the scheduled run). The learner has just answered
each question out loud with no preparation. Their habit, as a strong engineer,
is a deep and well-reasoned answer, which technical peers appreciate. Executives
and account leaders need something else: **what has to happen (or has
happened), why it matters to them, what you need, and an offer to go into
detail.** The answer key shows that response for every question, so the learner
can read it, say it back, and build the habit.

## The answer ladder (one per question)

1. **One breath** (`headline`): the single sentence this listener must
   remember. 6–18 words. Outcome first: what has to happen or has happened,
   and when. No background, no hedging, no "so basically".
2. **The exec answer** (`answer`): 3 or 4 short spoken sentences, each tagged
   with its move, 20–70 words in total (about 25 seconds aloud):
   - `headline`: the outcome (may repeat the one-breath line).
   - `so_what`: why it matters to *this* listener, in their terms (money,
     risk, customers, time, what they tell their own boss).
   - `ask`: the decision or action you need: who, what, by when. Leave it out
     only when nothing is needed (a story question, a pure explanation).
   - `offer`: offer the specific detail you are holding back, then stop
     ("Happy to walk you through the root cause if that helps.").
   The first move is `headline`, the last is `offer`, each move appears once.
3. **Hold back, offer if asked** (`detail`): 2–4 bullets, at most 20 words
   each: the depth a technical peer would want, which this listener only gets
   on request. Concrete (names, numbers, mechanisms), not "more context".
4. **The trap** (`trap`): one sentence, at most 30 words, naming what a
   technically strong answer that is wrong for *this listener* would do here,
   and what the listener hears instead. Example: "Opening with how the retry
   queue works: the CFO hears risk and no plan."
5. **After their reply** (`reply_answer`): only for slots that list a reply.
   "What's the biggest risk?" → one risk and how you will handle it.
   "What do you need from me?" → the ask: who, what, by when. At most 45
   words, then stop. Omit for slots without a reply.

## Rules

- Written to be **spoken by the learner**: first person, plain words,
  contractions welcome, short sentences, no jargon the listener would not use.
- **Use only facts in the question.** When a fact is needed but missing (a date,
  a number), use a plausible, specific placeholder ("by Friday", "two weeks");
  never invent a dramatic new fact.
- **Every listener gets the exec answer**, technical peers and interviewers
  too: the headline-first summary is always the opening. For those listeners
  the `detail` bullets are what they will usually ask for next.
- **Story questions** ("Tell me about a time…"): the headline is the result and
  the lesson in one line; `so_what` is what you did; no `ask`.
- **Honest**: bad news goes in the headline, plainly. Never promise what the
  question says cannot be delivered. Respect any constraint on the question.
- No markdown inside strings, no angle brackets, no lists inside `answer`
  texts.

## Output schema (exactly this JSON, nothing else)

```json
{
  "answers": [
    {
      "slot": 1,
      "headline": "We're on track for the 15th; one integration needs your IT team this week.",
      "answer": [
        {"move": "headline", "text": "We're on track for go-live on the 15th, with one risk."},
        {"move": "so_what", "text": "The payment integration needs a firewall change from your IT team by the 28th, or we slip a week."},
        {"move": "ask", "text": "Could you ask your IT director to prioritise it this week?"},
        {"move": "offer", "text": "Happy to walk you through the integration plan if that's useful."}
      ],
      "detail": [
        "The change opens one outbound port to the payment gateway; the ticket has been open nine days.",
        "Every other integration passed end-to-end tests on Tuesday.",
        "Fallback: launch without card payments and switch them on a week later."
      ],
      "trap": "Walking through each integration's test status: the sponsor hears a list and misses the one thing she must do.",
      "reply_answer": "The firewall ticket. If it isn't done by the 28th, go-live moves a week. I've escalated it once; one note from you would settle it."
    }
  ]
}
```

`slot` must match the slot numbers you were given; write one item per slot.
