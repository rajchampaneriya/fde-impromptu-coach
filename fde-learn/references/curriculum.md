# FDE First Principles: the curriculum

Generated from `fde-impromptu-coach/assets/learning_path.json` (the source of truth) by `fde-impromptu-coach/scripts/tools/build_curriculum.py`. 66 topics in 6 projects. Every project ends with an article on [rajc.work](https://rajc.work): that is the finish line, not a date.

Why this order: it starts from what you already do (calling models, building agents) and goes one layer deeper each time a project raises a question. Maths arrives only on the day a project needs it.

## Pace: plan on 4 to 5 months

| | |
|---|---|
| Your time | 8 hours a week: 80 minutes a morning, 6 mornings a week. Sunday is rest. |
| Total work | about 128 hours, estimated topic by topic below |
| Finish each topic early and pull the next one (`fde-coach learn next`) | about 16 weeks (3.7 months) |
| Use every morning the schedule allows | about 21 weeks (4.8 months) |

A topic drops in the morning and gets as many mornings as its estimate needs: one for most diagrams, two for most notebooks, three for an article. Ship it when it is done: the next topic drops the next morning, or straight away with `fde-coach learn next`. A missed deadline is never skipped: the topic comes back at minimum scope with half the mornings.

### How each topic's time is calculated

- **Learn**: the resource minutes × 1.5 (pausing, replaying and reading in a second language), rounded up to 5.
- **Build**: 12 minutes per build step for a notebook or code, 10 for a diagram, 15 for a document, 35 for an article; plus 10 if there is set-up and 10 if there is new maths. Day 3 adds 30 for reviewing 40 drafted test cases by hand.
- **Explain**: 25 minutes for "In my words" and two takes of a 5-minute video (10 for an article, where the video is optional).
- **Mornings**: the total ÷ 80 minutes, rounded up after a 10-minute grace.

If your real times differ after project 1, change the numbers in `pace` and run the tool again.

## Rules that save time

- **One-hour rule.** When unfamiliar maths appears, spend at most an hour on that one idea (the topic's maths note, a 3Blue1Brown lesson, a few Khan Academy exercises, or Claude explaining it with your own numbers), then go back to the code. Anything bigger goes in `later.md`.
- **Finish lines, not calendars.** A project is done when its article is live on rajc.work. The article starts with about 300 words written from memory, without notes: if you can't write them, that is the part to revisit.
- **Courses are references, not syllabi.** Each topic names the exact section to read or watch.
- **Skip what you know** (API integration, orchestration, cloud deployment) and **postpone** eigenvectors, advanced calculus, training large models and most research papers.
- **Keep it cheap.** All resources are free. Everything runs on your Mac with Ollama, and the GPT project can use free Colab time. The only paid step is the final run in project 6: a hard monthly spending cap first, an estimate before the run, cached answers so re-runs are free.

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
| 10 | Read the failures, not the averages | [A Field Guide to Rapidly Improving AI Products (Hamel Husain)](https://hamel.dev/blog/posts/field-guide/) | – | notebook | 105 min · 2 mornings |
| 11 | The recommendation, first draft (an ADR) | [Documenting Architecture Decisions (Michael Nygard)](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) | – | doc | 85 min · 1 morning |
| 12 | Article: measure before you believe | [What to blog about (Simon Willison): 'Write about your projects'](https://simonwillison.net/2022/Nov/6/what-to-blog-about/) | – | article | 235 min · 3 mornings |

## Project 2 · Meaning as numbers (days 13–22 · about 19 hours · 18 mornings)

Build semantic search from scratch with NumPy, measure it, and plug it into project 1.

Maths you will meet: vectors, length, dot product, cosine similarity, matrix × vector.

| Day | Topic | Learn (main resource) | Maths | Artifact | Time |
|---|---|---|---|---|---|
| 13 | Vectors: a list of numbers that points somewhere | [Vectors, what even are they? (3Blue1Brown, Linear Algebra chapter 1)](https://www.3blue1brown.com/lessons/vectors) | A vector and its length | notebook | 110 min · 2 mornings |
| 14 | Dot product and cosine: measuring 'alike' | [The Illustrated Word2vec (Jay Alammar): 'Personality Embeddings' only](https://jalammar.github.io/illustrated-word2vec/) | Dot product and cosine similarity | notebook | 115 min · 2 mornings |
| 15 | Real embeddings: let a model choose the numbers | [Embedding space and static embeddings (Google ML Crash Course)](https://developers.google.com/machine-learning/crash-course/embeddings/embedding-space) | Unit vectors | notebook | 130 min · 2 mornings |
| 16 | A search engine in 30 lines of NumPy | [Introducing Contextual Retrieval (Anthropic): 'A primer on RAG'](https://www.anthropic.com/news/contextual-retrieval) | Matrix × vector | notebook | 95 min · 2 mornings |
| 17 | Is retrieval any good? recall@k | [Evaluation measures in information retrieval (Pinecone)](https://www.pinecone.io/learn/offline-evaluation/) | recall@k and MRR | notebook | 120 min · 2 mornings |
| 18 | Chunking: same data, different answers | [Introducing Contextual Retrieval (Anthropic)](https://www.anthropic.com/news/contextual-retrieval) | – | notebook | 90 min · 1 morning |
| 19 | A vector database vs. your NumPy: what does it add? | [Chroma: getting started](https://docs.trychroma.com/docs/overview/getting-started) | Exact vs. approximate search | notebook | 110 min · 2 mornings |
| 20 | Plug retrieval into version B and measure again | [Your AI Product Needs Evals: 'Evaluating RAG'](https://hamel.dev/blog/posts/evals/) | – | notebook | 85 min · 1 morning |
| 21 | Explain it to a customer: what RAG can and cannot promise | [Introducing Contextual Retrieval: 'Further boosting performance with Reranking' and 'Cost and latency considerations'](https://www.anthropic.com/news/contextual-retrieval) | – | diagram | 80 min · 1 morning |
| 22 | Article: meaning as numbers | [Technical Writing One (Google): Active voice](https://developers.google.com/tech-writing/one/active-voice) | – | article | 220 min · 3 mornings |

## Project 3 · Learn a formula from data (days 23–32 · about 20 hours · 20 mornings)

Let the computer find your hosting-cost formula, then a yes/no classifier, by gradient descent.

Maths you will meet: lines and slopes, loss, derivatives, gradient descent, overfitting, sigmoid.

| Day | Topic | Learn (main resource) | Maths | Artifact | Time |
|---|---|---|---|---|---|
| 23 | Functions and slopes: your hosting bill as a line | [Linear regression (Google ML Crash Course): first page](https://developers.google.com/machine-learning/crash-course/linear-regression) | A line: y = w·x + b | notebook | 110 min · 2 mornings |
| 24 | Loss: one number for 'how wrong' | [Loss (Google ML Crash Course)](https://developers.google.com/machine-learning/crash-course/linear-regression/loss) | Mean squared error (MSE) | notebook | 100 min · 2 mornings |
| 25 | Derivative: how much the loss moves when you nudge | [The paradox of the derivative (3Blue1Brown, Calculus chapter 2)](https://www.3blue1brown.com/lessons/derivatives) | A derivative, by nudging | notebook | 115 min · 2 mornings |
| 26 | Gradient descent: walk downhill in small steps | [Gradient descent (Google ML Crash Course)](https://developers.google.com/machine-learning/crash-course/linear-regression/gradient-descent) | The gradient | notebook | 115 min · 2 mornings |
| 27 | Learning rate: too small, too big, just right | [Hyperparameters (Google ML Crash Course)](https://developers.google.com/machine-learning/crash-course/linear-regression/hyperparameters) | Scaling the inputs | notebook | 110 min · 2 mornings |
| 28 | From nudges to a formula: the chain rule, first taste | [Visualizing the chain rule and product rule (3Blue1Brown, Calculus)](https://www.3blue1brown.com/lessons/chain-rule-and-product-rule) | The chain rule | notebook | 110 min · 2 mornings |
| 29 | Overfitting: when the model memorises | [Dividing the original dataset (Google ML Crash Course)](https://developers.google.com/machine-learning/crash-course/overfitting/dividing-datasets) | Polynomials | notebook | 115 min · 2 mornings |
| 30 | From numbers to yes/no: will this customer escalate? | [Logistic regression: calculating a probability (Google ML Crash Course)](https://developers.google.com/machine-learning/crash-course/logistic-regression/sigmoid-function) | Sigmoid and log loss | notebook | 115 min · 2 mornings |
| 31 | Wrap-up: programming vs. learning, explained | [But what is a Neural Network? (3Blue1Brown, Neural Networks chapter 1): first part](https://www.3blue1brown.com/lessons/neural-networks) | – | diagram | 70 min · 1 morning |
| 32 | Article: learn a formula from data | [Technical Writing One (Google): Clear sentences](https://developers.google.com/tech-writing/one/clear-sentences) | – | article | 210 min · 3 mornings |

## Project 4 · Backprop by hand (micrograd) (days 33–42 · about 19 hours · 20 mornings)

Build a tiny autograd engine and neural-net library, then train it.

Maths you will meet: the chain rule.

| Day | Topic | Learn (main resource) | Maths | Artifact | Time |
|---|---|---|---|---|---|
| 33 | One neuron, explained with your escalation data | [But what is a Neural Network? (3Blue1Brown, Neural Networks chapter 1)](https://www.3blue1brown.com/lessons/neural-networks) | Weighted sum + activation | notebook | 115 min · 2 mornings |
| 34 | A number that remembers where it came from | [Building micrograd (Andrej Karpathy): 'starting the core Value object' (19:09) to 'manual backpropagation example #1' (32:10)](https://www.youtube.com/watch?v=VMj-3S1tku0&t=1149s) | An expression graph | code | 115 min · 2 mornings |
| 35 | Backprop by hand: the chain rule in action | [Building micrograd: 'manual backpropagation example #1' (32:10 to 51:10)](https://www.youtube.com/watch?v=VMj-3S1tku0&t=1930s) | Chain rule: local × upstream | notebook | 105 min · 2 mornings |
| 36 | Automate it: a _backward for every operation | [Building micrograd: 'implementing the backward function for each operation' (1:09:02 to 1:22:28)](https://www.youtube.com/watch?v=VMj-3S1tku0&t=4142s) | Topological order | code | 110 min · 2 mornings |
| 37 | The bug when a value is used twice | [Building micrograd: 'fixing a backprop bug when one node is used multiple times' (1:22:28 to 1:39:31)](https://www.youtube.com/watch?v=VMj-3S1tku0&t=4948s) | Gradients add up | code | 105 min · 2 mornings |
| 38 | Same thing in PyTorch: what the library does for you | [Building micrograd: 'doing the same thing but in PyTorch' (1:39:31 to 1:43:55)](https://www.youtube.com/watch?v=VMj-3S1tku0&t=5971s) | Tensors | notebook | 115 min · 2 mornings |
| 39 | A tiny neural-net library: Neuron, Layer, MLP | [Building micrograd: 'building out a neural net library' (1:43:55 to 1:57:56)](https://www.youtube.com/watch?v=VMj-3S1tku0&t=6235s) | Layers | code | 110 min · 2 mornings |
| 40 | The training loop: forward, backward, update, repeat | [Building micrograd: 'collecting all of the parameters' to 'summary' (1:57:56 to 2:14:03)](https://www.youtube.com/watch?v=VMj-3S1tku0&t=7076s) | – | notebook | 100 min · 2 mornings |
| 41 | Wrap-up: what training really is | [What is backpropagation really doing? (3Blue1Brown)](https://www.3blue1brown.com/lessons/backpropagation) | – | diagram | 80 min · 1 morning |
| 42 | Article: backprop by hand | [Technical Writing One (Google): Paragraphs](https://developers.google.com/tech-writing/one/paragraphs) | – | article | 210 min · 3 mornings |

## Project 5 · Tiny GPT (days 43–56 · about 27 hours · 29 mornings)

Go from counting letters to a small Transformer that writes Shakespeare-like text.

Maths you will meet: probability, logarithms, softmax, matrix multiplication, attention.

| Day | Topic | Learn (main resource) | Maths | Artifact | Time |
|---|---|---|---|---|---|
| 43 | Probability: counting what comes next | [Building makemore (Andrej Karpathy): 'reading and exploring the dataset' (03:03) to 'deleting spurious tokens' (24:02)](https://www.youtube.com/watch?v=PaCmpygFfXo&t=183s) | Conditional probability | notebook | 120 min · 2 mornings |
| 44 | Sampling: let the counts write new names | [Building makemore: 'sampling from the model' (24:02 to 36:17)](https://www.youtube.com/watch?v=PaCmpygFfXo&t=1442s) | A probability distribution | notebook | 115 min · 2 mornings |
| 45 | A loss for language: negative log likelihood | [Building makemore: 'loss function (the negative log likelihood…)' (50:14 to 1:02:57)](https://www.youtube.com/watch?v=PaCmpygFfXo&t=3014s) | Logarithms | notebook | 95 min · 2 mornings |
| 46 | Softmax and temperature: from scores to probabilities | [Building makemore: 'one-hot encodings' to 'softmax' (1:10:01 to 1:26:17)](https://www.youtube.com/watch?v=PaCmpygFfXo&t=4201s) | Softmax | notebook | 120 min · 2 mornings |
| 47 | The neural bigram: the same answer, learned | [Building makemore: 'vectorized loss' to 'sampling from the neural net' (1:35:49 to 1:56:16)](https://www.youtube.com/watch?v=PaCmpygFfXo&t=5749s) | One-hot × matrix = picking a row | notebook | 115 min · 2 mornings |
| 48 | Tokens: what the model reads, and why Hinglish costs more | [Deep Dive into LLMs (Andrej Karpathy): 'tokenization' (07:47 to 14:27)](https://www.youtube.com/watch?v=7xTGNNLPyMI&t=467s) | Ratios | notebook | 115 min · 2 mornings |
| 49 | From text to training batches: the shift-by-one trick | [Let's build GPT (Andrej Karpathy): 'reading and exploring the data' to 'data loader' (07:52 to 22:11)](https://www.youtube.com/watch?v=kCc8FmEb1nY&t=472s) | Shapes | notebook | 110 min · 2 mornings |
| 50 | Averaging the past with one matrix multiply | [Let's build GPT: 'version 1' to 'minor code cleanup' (42:13 to 58:26)](https://www.youtube.com/watch?v=kCc8FmEb1nY&t=2533s) | Matrix multiply as weighted averages | notebook | 110 min · 2 mornings |
| 51 | Attention by hand: queries, keys and values | [Attention in transformers, step-by-step (3Blue1Brown)](https://www.3blue1brown.com/lessons/attention) | Query · key = relevance | diagram | 95 min · 2 mornings |
| 52 | One self-attention head in code | [Let's build GPT: 'THE CRUX OF THE VIDEO: version 4: self-attention' to note 6 (1:02:00 to 1:19:11)](https://www.youtube.com/watch?v=kCc8FmEb1nY&t=3720s) | Scaling by √head_size | notebook | 105 min · 2 mornings |
| 53 | Multi-head, feed-forward, residual: a Transformer block | [Let's build GPT: 'inserting a single self-attention block' to 'layernorm' (1:19:11 to 1:37:49)](https://www.youtube.com/watch?v=kCc8FmEb1nY&t=4751s) | Residual connections | notebook | 115 min · 2 mornings |
| 54 | Scale it up a little and count the cost | [Let's build GPT: 'scaling up the model' to 'nanoGPT walkthrough' (1:37:49 to 1:48:53)](https://www.youtube.com/watch?v=kCc8FmEb1nY&t=5869s) | Counting parameters | notebook | 115 min · 2 mornings |
| 55 | From tiny GPT to ChatGPT: where hallucinations come from | [Let's build GPT: 'back to ChatGPT… pretraining vs. finetuning, RLHF' (1:48:53 to 1:54:32)](https://www.youtube.com/watch?v=kCc8FmEb1nY&t=6533s) | – | diagram | 100 min · 2 mornings |
| 56 | Article: tiny GPT | [Technical Writing One (Google): Audience](https://developers.google.com/tech-writing/one/audience) | – | article | 210 min · 3 mornings |

## Project 6 · Back to the customer (days 57–66 · about 17 hours · 15 mornings)

Explain project 1's failures from first principles, check them against a stronger model, harden the agent, and make the final recommendation like an FDE.

Maths you will meet: paired differences; everything else you reuse.

| Day | Topic | Learn (main resource) | Maths | Artifact | Time |
|---|---|---|---|---|---|
| 57 | Temperature, revisited with evidence | [A statistical approach to model evaluations: Recommendation #3 'Reduce variance within questions'](https://www.anthropic.com/research/statistical-approach-to-model-evals) | Consistency rate | notebook | 85 min · 1 morning |
| 58 | Why did it fail? Root causes from first principles | [A Field Guide to Rapidly Improving AI Products: 'Bottom-Up vs. Top-Down Analysis'](https://hamel.dev/blog/posts/field-guide/) | – | diagram | 75 min · 1 morning |
| 59 | What a tool call really is | [Writing effective tools for agents (Anthropic)](https://www.anthropic.com/engineering/writing-tools-for-agents) | – | notebook | 90 min · 1 morning |
| 60 | Context engineering: what the model sees is all it knows | [Effective context engineering for AI agents (Anthropic)](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | Budgets | notebook | 100 min · 2 mornings |
| 61 | Prompt injection: attack your own agent | [The lethal trifecta for AI agents (Simon Willison)](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/) | – | notebook | 90 min · 1 morning |
| 62 | Human in the loop: where the approval step belongs | [Building effective agents: 'Appendix 1: Agents in practice, A. Customer support'](https://www.anthropic.com/engineering/building-effective-agents) | Expected cost | notebook | 95 min · 2 mornings |
| 63 | The final run: same test, a stronger model | [A statistical approach to model evaluations (Anthropic): Recommendation #4 'Analyze paired differences'](https://www.anthropic.com/research/statistical-approach-to-model-evals) | Paired differences | notebook | 130 min · 2 mornings |
| 64 | The architecture recommendation (final) | [Building effective agents: 'Summary'](https://www.anthropic.com/engineering/building-effective-agents) | – | doc | 80 min · 1 morning |
| 65 | Customer readout: present it like an FDE | [A Field Guide to Rapidly Improving AI Products: 'Your AI Roadmap Should Count Experiments, Not Features'](https://hamel.dev/blog/posts/field-guide/) | – | diagram | 70 min · 1 morning |
| 66 | Article: back to the customer | [Technical Writing One (Google): Documents](https://developers.google.com/tech-writing/one/documents) | – | article | 225 min · 3 mornings |
