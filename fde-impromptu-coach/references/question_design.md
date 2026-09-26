# Question Design Rubric — FDE Impromptu Practice

Use this whenever you write new practice questions (interactively or in the
scheduled run). The learner answers each question out loud, on camera, with
zero preparation and a hard 60-second limit.

## The role being trained

A Forward Deployed Engineer (FDE) embeds with customers to get a product (often
an AI/LLM platform) working inside real workflows. They write production code in
customer environments, scope use cases, earn trust with executives and frontline
users, deliver bad news, push back on scope, translate between the customer and
internal product/engineering/research/sales/security teams, and make judgment
calls with incomplete information — often on-site and under time pressure.

## What makes a great impromptu question

1. **One situation, one ask.** The last sentence tells the learner exactly what
   to do: "Respond.", "Tell her.", "Make the case.", "Decide and explain it."
2. **Speakable in 60 seconds.** Answerable without research or notes.
3. **Concrete and specific.** Named roles (CFO, CISO, frontline nurse), real
   numbers (40% usage drop, 3-hour outage), a real moment (mid-demo, all-hands).
4. **Tension, not trivia.** Competing interests, a skeptical listener, a cost to
   every option. There is no perfect answer — only a well-led one.
5. **Varied format.** Rotate: roleplay (speak directly to someone), explain
   (teach a concept), opinion (take and defend a side), story (behavioral
   "tell me about a time"), pitch (persuade).
6. **Fresh.** Never reuse or lightly reword a past question. Change the setting,
   the stakeholder, the stakes and the ask — not just the nouns.
7. **Plain words.** 15–45 words, one or two sentences, no lists, no line breaks.
   Use straight or curly quotes for dialogue; never angle brackets.

## Difficulty scale (1–5)

| Level | Feel | Ingredients |
|---|---|---|
| 1 | Warm-up | Familiar topic, low stakes, explain or reflect on your own work |
| 2 | Mild pressure | A realistic stakeholder question with a fairly clear good answer |
| 3 | Tension | Competing interests or a skeptical audience; must take a position |
| 4 | High stakes | Senior executive, conflict, bad news, ethics grey zone or real ambiguity |
| 5 | Crucible | Hostile/emotional/public setting, your own mistake involved, several pressures at once; must stay composed and lead |

A daily set ramps up: the first question is the easiest, the last is the hardest.

## Constraints (twists)

From difficulty 3 upward, add a one-line constraint to about half of the
questions (most of the 4s and 5s). Constraints train structure under pressure.
Examples: "Lead with your recommendation in the first sentence." · "No jargon:
your listener is non-technical." · "Use exactly three points." · "Include one
specific number." · "End with a clear ask." · "Acknowledge their perspective
before yours." · "Finish in 45 seconds, then hold the silence." · "Use one
analogy." · "Name one risk and how you will manage it." Keep it under 15 words
and make sure it fits the format (no "tell it as a story" on a roleplay).

## Competencies (category ids)

- `exec_comm` — Executive communication
- `tech_translation` — Technical translation
- `discovery` — Customer discovery
- `pushback` — Saying no & scope control
- `crisis` — Incidents & bad news
- `influence` — Influence without authority
- `prioritization` — Prioritization & trade-offs
- `ownership` — Ownership & failure
- `trust_ethics` — Trust, security & ethics
- `leadership` — Leadership & vision
- `commercial` — Commercial & negotiation
- `ambiguity` — Ambiguity & judgment calls

## Coach note

For each question write a `coach_note` (one or two sentences, max ~40 words)
describing what a strong answer does *for this specific question* — the
learner reads it in the speaker notes after recording, when reviewing.

## Output schema (exactly this JSON, nothing else)

```json
{
  "questions": [
    {
      "slot": 1,
      "category": "crisis",
      "difficulty": 3,
      "format": "roleplay",
      "text": "An outage has blocked the customer's support team for three hours during their busiest week. Their director calls you, angry. Respond.",
      "constraint": "Do not apologize more than once.",
      "coach_note": "Own it in the first sentence, give the current status and the next update time, and resist over-explaining the root cause before you know it."
    }
  ]
}
```

`constraint` may be an empty string. `slot`, `category` and `difficulty` must
match the plan you were given.

## Examples by difficulty (style reference only — never reuse)

- **1** "Explain what an API is to a hospital administrator who has never written code."
- **2** "A customer asks for 'just one more small feature' two days before go-live. Respond."
- **3** "The customer's procurement lead says: 'We like the product, but your competitor is 30% cheaper.' Respond."
- **4** "Renewal is in three weeks, usage is down 40%, and your executive sponsor has gone quiet. You get her on the phone. What do you say?"
- **5** "A critical incident was caused by a configuration change you made. In the post-mortem, the customer's CTO asks: 'Whose fault is this?' Answer."
