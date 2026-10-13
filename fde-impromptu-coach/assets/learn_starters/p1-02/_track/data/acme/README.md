# Acme Fibre: the project brief (fictional)

**Acme Fibre** is a made-up broadband company in Pune. It has about 40,000 home customers. Its
support team of 25 people answers around 1,200 customer emails a day. Many emails are in English,
many in Hinglish (Hindi written in English letters).

The head of support says:

> "We want an AI agent to answer customer emails. Our competitors are doing it."

Your job in project 1 is to find out what they really need, build it three ways
(rules, one model call, an agent), measure all three, and recommend one with evidence.

## The files

| File | What it is |
|---|---|
| `customers.json` | 12 sample customers: area, plan, tenure, balance |
| `outages.json` | Outages happening right now, by area |
| `kb.md` | 16 short help articles the support team uses |
| `policy.md` | Rules every reply must follow |
| `cases.jsonl` | Test cases: an email plus what a correct reply must contain (from day 3) |
| `queries.jsonl` | Search tests: a question plus the right help article (from project 2) |

Plans: **Basic** 100 Mbps ₹699/month · **Plus** 300 Mbps ₹999/month · **Pro** 1 Gbps ₹1,499/month.

All names, numbers and policies here are invented for learning. Real customer data never goes
into this public repository.
