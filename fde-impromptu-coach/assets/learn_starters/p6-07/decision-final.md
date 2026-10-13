# ADR-002: Acme Fibre email assistant (final recommendation)

**Status:** Proposed · **Date:** … · **Author:** … · **Replaces:** ADR-001 (project 1)

## 1. Context
What Acme asked for, what they actually need, volumes, constraints (cost, Hinglish, policy, privacy).

## 2. Options considered
| Option | Pass rate (± 2 se) | p95 s | ₹ per 1,000 emails | Main failure |
|---|---|---|---|---|
| A · rules | | | | |
| B · one call, oracle context | | | | |
| B · one call, retrieved context | | | | |
| C · agent with tools | | | | |

## 3. Decision
…

## 4. Why: the evidence
- Failure analysis (project 6, step 2): …
- Retrieval (project 2): recall@3 = …
- Randomness (project 6, step 1): consistency at temperature … = …

## 5. Safety and security
- Trust boundary and guard (project 6, step 5): …
- Human in the loop (project 6, step 6): …

## 6. Cost
…

## 7. Rollout plan
| Stage | What happens | Go to the next stage when |
|---|---|---|
| Shadow mode | The assistant drafts; humans send their own reply | pass rate ≥ … on … real emails |
| 10% | Drafts for low-risk intents are sent after a quick human check | … |
| All | … | … |

## 8. What we watch in production
…

## 9. What would change my mind
…
