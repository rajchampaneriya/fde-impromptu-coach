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
| C · managed runtime (project 4) | | | | |
| B · one call, stronger model (project 4) | | | | |
| C · agent, stronger model (project 4) | | | | |

## 3. Decision
…

## 4. Why: the evidence
- Failure analysis and attribution (project 1, day 10): …
- Retrieval (project 2): recall@3 = …
- Calibrated judge and CI gate (project 3): kappa = … ; gate blocks …
- Randomness (project 5): consistency at temperature … = …
- Stronger model (project 4): paired difference = … ± … ; fixed …, still failing …

## 5. Safety and security
- Security review pack (project 6, step 2): …
- Cedar policy and red-team (project 4): …
- Human in the loop and operator console (project 4): …

## 6. Cost
Small model: ₹… per 1,000 emails. Stronger model: ₹… per 1,000 emails. Which one, and why: …

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
