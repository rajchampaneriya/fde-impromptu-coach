# FDE First Principles: the curriculum

Generated from `fde-impromptu-coach/assets/learning_path.json` (the source of truth) by `fde-impromptu-coach/scripts/tools/build_curriculum.py`. 53 topics in 6 projects. Every project ends with an article on [rajc.work](https://rajc.work): that is the finish line, not a date.

Why this order: it follows what U.S. employers hire Forward Deployed and full-stack AI engineers for. Measure first, ground the agent in the customer's context, make the evals run without you, ship a production-shaped agent, open the model only where it changes a decision, then rehearse the whole customer engagement. Maths arrives only on the day a project needs it.

## Pace: plan on 3 to 4 months

| | |
|---|---|
| Your time | 8 hours a week: 80 minutes a morning, 6 mornings a week. Sunday is rest. |
| Total work | about 114 hours, estimated topic by topic below |
| Finish each topic early and pull the next one (`fde-coach learn next`) | about 14 weeks (3.3 months) |
| Use every morning the schedule allows | about 18 weeks (4.1 months) |

A topic drops in the morning and gets as many mornings as its estimate needs: one for most diagrams, two for most notebooks, three for an article. Ship it when it is done: the next topic drops the next morning, or straight away with `fde-coach learn next`. A missed deadline is never skipped: the topic comes back at minimum scope with half the mornings.

### How each topic's time is calculated

- **Learn**: the resource minutes × 1.5 (pausing, replaying and reading in a second language), rounded up to 5.
- **Build**: 12 minutes per build step for a notebook or code, 10 for a diagram, 15 for a document, 35 for an article; plus 10 if there is set-up and 10 if there is new maths. Day 3 adds 30 for reviewing 40 drafted test cases by hand. Day 52 adds 45 for recording the 45-minute rehearsal.
- **Explain**: 25 minutes for "In my words" and two takes of a 5-minute video (10 for an article, where the video is optional).
- **Mornings**: the total ÷ 80 minutes, rounded up after a 10-minute grace.

If your real times differ after project 1, change the numbers in `pace` and run the tool again.

## Rules that save time

- **One-hour rule.** When unfamiliar maths appears, spend at most an hour on that one idea (the topic's maths note, a 3Blue1Brown lesson, a few Khan Academy exercises, or Claude explaining it with your own numbers), then go back to the code. Anything bigger goes in `later.md`.
- **Finish lines, not calendars.** A project is done when its article is live on rajc.work. The article starts with about 300 words written from memory, without notes: if you can't write them, that is the part to revisit.
- **Courses are references, not syllabi.** Each topic names the exact section to read or watch.
- **Re-check the platforms every quarter.** Managed agent runtimes, MCP gateways and cloud eval services changed the deployment baseline in 2026, so cloud deployment is part of the path, not something to skip. **Postpone** eigenvectors, advanced calculus, pretraining and most research papers: the from-scratch builds are in the optional track below.
- **One capped cloud budget per project, from project 3.** Ollama on your Mac stays the default for fast iteration. Managed runtimes, cloud evaluators and the frontier run each get a hard monthly spending cap first, an estimate under a fifth of the cap before the run, and cached answers so re-runs are free.
- **Provenance on every run.** Every script writes `model_id`, `prompt_sha`, `grader_sha` and `dataset_sha` into the run file automatically. A number you cannot trace back is not evidence.
- **Lab depth is a topic, not a miss.** When an experiment grows beyond the day's topic, park the scheduled topic and log the lab work as its own step with a merged pull request and a 2-minute walkthrough, so the tracker shows the real work.
- **A 30-minute market radar at every project boundary.** Read the release notes from Microsoft Foundry, AWS Bedrock, Google Cloud, OpenAI and Anthropic, and adjust the next project before it starts.

## Project 1 · Measure before you believe (days 1–12 · about 25 hours · 24 mornings)

Build one customer-support assistant three ways (rules, one model call, an agent loop), measure all three, and recommend one with evidence.

Maths you will meet: fractions and averages, error bars, percentiles.

| Day | Topic | Learn (main resource) | Maths | Artifact | Time |
|---|---|---|---|---|---|
| 1 | One model call: tokens, time and randomness | [Ollama API: generate a chat message](https://docs.ollama.com/api/chat) | – | notebook | 110 min · 2 mornings |
| 2 | Workflow or agent? Map the decisions first | [Building effective agents (Anthropic)](https://www.anthropic.com/engineering/building-effective-agents) | – | diagram | 105 min · 2 mornings |
| 3 | Write the test set before the system | [Your AI Product Needs Evals (Hamel Husain)](https://hamel.dev/blog/posts/evals/) | Counting and proportions | notebook | 145 min · 2 mornings |
| 4 | Version A: rules and templates (the honest baseline) | [Building effective agents: 'Appendix 1, A. Customer support'](https://www.anthropic.com/engineering/building-effective-agents) | Accuracy | notebook | 115 min · 2 mornings |
| 5 | A grader you can trust | [Define success criteria and build evaluations (Claude docs)](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests) | – | code | 100 min · 2 mornings |
| 6 | Version B: one model call with the right context | [Ollama: structured outputs](https://docs.ollama.com/capabilities/structured-outputs) | – | notebook | 110 min · 2 mornings |
| 7 | Why 30 test cases can lie: error bars | [A statistical approach to model evaluations (Anthropic)](https://www.anthropic.com/research/statistical-approach-to-model-evals) | Standard error and a 95% range | notebook | 140 min · 2 mornings |
| 8 | Version C: an agent loop from scratch | [Ollama: tool calling](https://docs.ollama.com/capabilities/tool-calling) | – | notebook | 115 min · 2 mornings |
| 9 | Run all three: success, cost, latency | [Your AI Product Needs Evals: 'Logging Traces' and 'Looking At Your Traces'](https://hamel.dev/blog/posts/evals/) | Mean, median and 95th percentile | notebook | 120 min · 2 mornings |
| 10 | Read the failures, not the averages | [A Field Guide to Rapidly Improving AI Products (Hamel Husain)](https://hamel.dev/blog/posts/field-guide/) | – | notebook | 130 min · 2 mornings |
| 11 | The recommendation, first draft (an ADR) | [Documenting Architecture Decisions (Michael Nygard)](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) | – | doc | 85 min · 1 morning |
| 12 | Article: measure before you believe | [What to blog about (Simon Willison): 'Write about your projects'](https://simonwillison.net/2022/Nov/6/what-to-blog-about/) | – | article | 235 min · 3 mornings |

## Project 2 · Grounding: meaning as numbers and enterprise context (days 13–22 · about 20 hours · 19 mornings)

Build semantic search from scratch with NumPy, measure it, plug it into versions B and C, and test it against an ontology of Acme's own terms: vectors alone, the ontology alone, or both.

Maths you will meet: vectors, dot product, cosine similarity, matrix × vector, recall@k.

| Day | Topic | Learn (main resource) | Maths | Artifact | Time |
|---|---|---|---|---|---|
| 13 | Vectors, dot product and cosine: measuring 'alike' | [Vectors, what even are they? (3Blue1Brown, Linear Algebra chapter 1)](https://www.3blue1brown.com/lessons/vectors) | Dot product and cosine similarity | notebook | 115 min · 2 mornings |
| 14 | Real embeddings: let a model choose the numbers | [Embedding space and static embeddings (Google ML Crash Course)](https://developers.google.com/machine-learning/crash-course/embeddings/embedding-space) | Unit vectors | notebook | 130 min · 2 mornings |
| 15 | A search engine in 30 lines of NumPy | [Introducing Contextual Retrieval (Anthropic): 'A primer on RAG'](https://www.anthropic.com/news/contextual-retrieval) | Matrix × vector | notebook | 95 min · 2 mornings |
| 16 | Is retrieval any good? recall@k | [Evaluation measures in information retrieval (Pinecone)](https://www.pinecone.io/learn/offline-evaluation/) | recall@k and MRR | notebook | 120 min · 2 mornings |
| 17 | Chunking: same data, different answers | [Introducing Contextual Retrieval (Anthropic)](https://www.anthropic.com/news/contextual-retrieval) | – | notebook | 90 min · 1 morning |
| 18 | A vector database vs. your NumPy: what does it add? | [Chroma: getting started](https://docs.trychroma.com/docs/overview/getting-started) | Exact vs. approximate search | notebook | 110 min · 2 mornings |
| 19 | Plug retrieval into versions B and C and measure again | [Your AI Product Needs Evals: 'Evaluating RAG'](https://hamel.dev/blog/posts/evals/) | – | notebook | 95 min · 2 mornings |
| 20 | Ontology, vectors or both? A grounding ablation | [What are ontologies? (Ontotext)](https://www.ontotext.com/knowledgehub/fundamentals/what-are-ontologies/) | – | notebook | 115 min · 2 mornings |
| 21 | Explain it to a customer: what grounding can and cannot promise | [Introducing Contextual Retrieval: 'Further boosting performance with Reranking' and 'Cost and latency considerations'](https://www.anthropic.com/news/contextual-retrieval) | – | diagram | 80 min · 1 morning |
| 22 | Article: grounding, meaning as numbers | [Technical Writing One (Google): Active voice](https://developers.google.com/tech-writing/one/active-voice) | – | article | 220 min · 3 mornings |

## Project 3 · Evals that run without you (days 23–31 · about 20 hours · 19 mornings)

Turn project 1's hand-run tests into a pipeline: a judge calibrated against your own labels, paired comparisons, simulated customers, broken tools, traces, a CI gate that blocks regressions and drift alerts.

Maths you will meet: Cohen's kappa, bootstrap intervals, McNemar's test, pass^k, population stability index.

| Day | Topic | Learn (main resource) | Maths | Artifact | Time |
|---|---|---|---|---|---|
| 23 | Calibrate an LLM judge against your own labels | [Creating a LLM-as-a-Judge That Drives Business Results (Hamel Husain)](https://hamel.dev/blog/posts/llm-judge/) | Cohen's kappa | notebook | 150 min · 2 mornings |
| 24 | Paired comparisons: did the change really help? | [A statistical approach to model evaluations (Anthropic): Recommendation #4 'Analyze paired differences'](https://www.anthropic.com/research/statistical-approach-to-model-evals) | Bootstrap intervals and McNemar's test | code | 115 min · 2 mornings |
| 25 | Simulated customers: tests that talk back | [τ-bench: benchmarking AI agents for the real world (Sierra)](https://sierra.ai/blog/benchmarking-ai-agents) | pass^k | notebook | 110 min · 2 mornings |
| 26 | Break the tools on purpose | [Writing effective tools for agents (Anthropic)](https://www.anthropic.com/engineering/writing-tools-for-agents) | – | notebook | 105 min · 2 mornings |
| 27 | Trace every step with OpenTelemetry | [Semantic conventions for generative AI spans (OpenTelemetry)](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/) | – | code | 135 min · 2 mornings |
| 28 | A CI gate that blocks regressions | [Building and testing Python (GitHub Docs)](https://docs.github.com/en/actions/use-cases-and-examples/building-and-testing/building-and-testing-python) | – | code | 125 min · 2 mornings |
| 29 | Drift: notice when the emails change | [What is data drift in ML, and how to detect and handle it (Evidently AI)](https://www.evidentlyai.com/ml-in-production/data-drift) | Population stability index (PSI) | notebook | 110 min · 2 mornings |
| 30 | Your evals on a managed platform | [Evaluate your generative AI application locally with the Azure AI Evaluation SDK (Microsoft Learn)](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/evaluate-sdk) | – | notebook | 115 min · 2 mornings |
| 31 | Article: evals that run without you | [Technical Writing One (Google): Clear sentences](https://developers.google.com/tech-writing/one/clear-sentences) | – | article | 220 min · 3 mornings |

## Project 4 · A production-shaped full-stack agent (days 32–39 · about 19 hours · 17 mornings)

Ship version C the way a customer would run it: tools behind an MCP server, the grader as an Agent Skill, a managed cloud runtime, a React operator console with human approval for big refunds, its own identity and a Cedar policy, a red-team, and one capped run on a frontier model.

Maths you will meet: paired differences; everything else you reuse.

| Day | Topic | Learn (main resource) | Maths | Artifact | Time |
|---|---|---|---|---|---|
| 32 | Your tools as an MCP server | [Build an MCP server (Model Context Protocol)](https://modelcontextprotocol.io/docs/develop/build-server) | – | code | 140 min · 2 mornings |
| 33 | Package your grader as an Agent Skill | [Equipping agents for the real world with Agent Skills (Anthropic)](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) | – | code | 115 min · 2 mornings |
| 34 | Port the agent to a managed runtime | [What is Azure AI Foundry Agent Service? (Microsoft Learn)](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview) | – | code | 140 min · 2 mornings |
| 35 | An operator console: stream the agent, approve the refunds | [Next.js App Router quickstart (AI SDK)](https://ai-sdk.dev/docs/getting-started/nextjs-app-router) | – | code | 140 min · 2 mornings |
| 36 | Agent identity and policy as code (Cedar) | [Basic policy construction in Cedar (Cedar docs)](https://docs.cedarpolicy.com/policies/syntax-policy.html) | – | code | 150 min · 2 mornings |
| 37 | Prompt injection: red-team your own agent | [The lethal trifecta for AI agents (Simon Willison)](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/) | – | notebook | 115 min · 2 mornings |
| 38 | The capped frontier run: same test, a stronger model | [A statistical approach to model evaluations (Anthropic): Recommendation #4 'Analyze paired differences'](https://www.anthropic.com/research/statistical-approach-to-model-evals) | Paired differences | notebook | 130 min · 2 mornings |
| 39 | Article: a production-shaped agent | [Technical Writing One (Google): Paragraphs](https://developers.google.com/tech-writing/one/paragraphs) | – | article | 220 min · 3 mornings |

## Project 5 · Inside the model: mechanics that change decisions (days 40–46 · about 15 hours · 15 mornings)

Open the model only where it changes a customer decision: tokens and cost, temperature, long context, hallucinations, what training changes, and build vs. tune vs. retrieve. Six executive diagrams and a cost and latency calculator.

Maths you will meet: ratios, softmax, query · key, loss and gradient descent, latency and cost formulas.

| Day | Topic | Learn (main resource) | Maths | Artifact | Time |
|---|---|---|---|---|---|
| 40 | Tokens: what the model reads, and why Hinglish costs more | [Deep Dive into LLMs (Andrej Karpathy): 'tokenization' (07:47 to 14:27)](https://www.youtube.com/watch?v=7xTGNNLPyMI&t=467s) | Ratios | notebook | 125 min · 2 mornings |
| 41 | Softmax and temperature: should a support bot be creative? | [Transformers, the tech behind LLMs (3Blue1Brown): 'Softmax'](https://www.3blue1brown.com/lessons/gpt) | Softmax with temperature | notebook | 100 min · 2 mornings |
| 42 | Attention and long context: why more context can make it worse | [Attention in transformers, step-by-step (3Blue1Brown)](https://www.3blue1brown.com/lessons/attention) | Query · key = relevance | diagram | 110 min · 2 mornings |
| 43 | Where hallucinations come from | [Deep Dive into LLMs: 'hallucinations, tool use, knowledge/working memory' (1:20:32 to 1:41:46)](https://www.youtube.com/watch?v=7xTGNNLPyMI&t=4832s) | – | diagram | 105 min · 2 mornings |
| 44 | Training in one notebook: what fine-tuning can change | [Gradient descent (Google ML Crash Course)](https://developers.google.com/machine-learning/crash-course/linear-regression/gradient-descent) | Loss and gradient descent | notebook | 125 min · 2 mornings |
| 45 | Build, tune or retrieve? A cost and latency calculator | [Optimizing LLMs for accuracy (OpenAI)](https://platform.openai.com/docs/guides/optimizing-llm-accuracy) | Latency = TTFT + tokens out × time per token | notebook | 130 min · 2 mornings |
| 46 | Article: inside the model, for decision makers | [Technical Writing One (Google): Audience](https://developers.google.com/tech-writing/one/audience) | – | article | 220 min · 3 mornings |

## Project 6 · The 6-week enterprise engagement rehearsal (days 47–53 · about 15 hours · 13 mornings)

Rehearse a whole customer engagement on Acme: discovery, a security review pack, the final architecture decision, a headline-first executive readout, a handover kit, and one recorded 45-minute live simulation.

Maths you will meet: none new; you reuse everything.

| Day | Topic | Learn (main resource) | Maths | Artifact | Time |
|---|---|---|---|---|---|
| 47 | Discovery: scope the use case with the customer | [Claude Frontier Academy (Anthropic)](https://www.anthropic.com/news/claude-frontier-academy) | – | doc | 115 min · 2 mornings |
| 48 | Threat model and security review pack | [Microsoft Threat Modeling Tool threats: STRIDE (Microsoft Learn)](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats) | – | doc | 125 min · 2 mornings |
| 49 | The architecture recommendation (final) | [Building effective agents: 'Summary'](https://www.anthropic.com/engineering/building-effective-agents) | – | doc | 80 min · 1 morning |
| 50 | Executive readout: headline first, then evidence | [A Field Guide to Rapidly Improving AI Products: 'Your AI Roadmap Should Count Experiments, Not Features'](https://hamel.dev/blog/posts/field-guide/) | – | diagram | 80 min · 1 morning |
| 51 | Handover: runbook, SLOs and owners | [Service level objectives (Google SRE book)](https://sre.google/sre-book/service-level-objectives/) | – | doc | 130 min · 2 mornings |
| 52 | Live rehearsal: the 6-week engagement in 45 minutes | [Building effective agents (Anthropic): 'When (and when not) to use agents'](https://www.anthropic.com/engineering/building-effective-agents) | – | doc | 140 min · 2 mornings |
| 53 | Article: the 6-week engagement | [Technical Writing One (Google): Documents](https://developers.google.com/tech-writing/one/documents) | – | article | 225 min · 3 mornings |

## Optional track: from scratch, for curiosity and video

Not scheduled and not on the hiring path. Build these on a free weekend, for your own understanding or for the Build2Understand channel. Bring them back into the main path only if a target interview loop tests ML internals, or a customer self-hosts and fine-tunes open-weight models.

| Build | Why |
|---|---|
| [micrograd: backprop by hand (about 19 hours)](https://www.youtube.com/watch?v=VMj-3S1tku0) | A tiny autograd engine and neural-net library: the chain rule in code. |
| [makemore: from counting letters to a neural bigram](https://www.youtube.com/watch?v=PaCmpygFfXo) | Probability, negative log likelihood and softmax on real names. |
| [Tiny GPT: a character-level Transformer (about 27 hours)](https://www.youtube.com/watch?v=kCc8FmEb1nY) | Self-attention, Transformer blocks and pretraining, end to end. |
