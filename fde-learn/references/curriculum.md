# FDE First Principles: the curriculum

Generated from `fde-impromptu-coach/assets/learning_path.json` (the source of truth). 59 daily topics in 6 projects. Each topic is about 75 minutes: learn ~20, build ~40, record ≤ 10. Topics drop Monday to Saturday; Sunday is rest.

Why this order: it starts from what you already do (calling models, building agents) and goes one layer deeper each time a project raises a question. Maths arrives only on the day a project needs it.

## Project 1 · Measure before you believe (days 1–11)

Build one customer-support assistant three ways (rules, one model call, an agent loop), measure all three, and recommend one with evidence.

Maths you will meet: fractions and averages, error bars, percentiles.

| Day | Topic | Learn (main resource) | Maths | Artifact |
|---|---|---|---|---|
| 1 | An LLM call is just an HTTP request | [Ollama API: generate a chat message](https://docs.ollama.com/api/chat) | – | notebook |
| 2 | Workflow or agent? Map the decisions first | [Building effective agents (Anthropic)](https://www.anthropic.com/engineering/building-effective-agents) | – | diagram |
| 3 | Write the test set before the system | [Your AI Product Needs Evals (Hamel Husain)](https://hamel.dev/blog/posts/evals/) | Counting and proportions | notebook |
| 4 | Version A: rules and templates (the honest baseline) | [Building effective agents: 'Appendix 1, A. Customer support'](https://www.anthropic.com/engineering/building-effective-agents) | Accuracy | notebook |
| 5 | A grader you can trust | [Define success criteria and build evaluations (Claude docs)](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests) | – | code |
| 6 | Version B: one model call with the right context | [Ollama: structured outputs](https://docs.ollama.com/capabilities/structured-outputs) | – | notebook |
| 7 | Why 30 test cases can lie: error bars | [A statistical approach to model evaluations (Anthropic)](https://www.anthropic.com/research/statistical-approach-to-model-evals) | Standard error and a 95% range | notebook |
| 8 | Version C: an agent loop from scratch | [Ollama: tool calling](https://docs.ollama.com/capabilities/tool-calling) | – | notebook |
| 9 | Run all three: success, cost, latency | [Your AI Product Needs Evals: 'Logging Traces' and 'Looking At Your Traces'](https://hamel.dev/blog/posts/evals/) | Mean, median and 95th percentile | notebook |
| 10 | Read the failures, not the averages | [A Field Guide to Rapidly Improving AI Products (Hamel Husain)](https://hamel.dev/blog/posts/field-guide/) | – | notebook |
| 11 | The recommendation, first draft (an ADR) | [Documenting Architecture Decisions (Michael Nygard)](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) | – | doc |

## Project 2 · Meaning as numbers (days 12–20)

Build semantic search from scratch with NumPy, measure it, and plug it into project 1.

Maths you will meet: vectors, length, dot product, cosine similarity, matrix × vector.

| Day | Topic | Learn (main resource) | Maths | Artifact |
|---|---|---|---|---|
| 12 | Vectors: a list of numbers that points somewhere | [Vectors, what even are they? (3Blue1Brown, Linear Algebra chapter 1)](https://www.3blue1brown.com/lessons/vectors) | A vector and its length | notebook |
| 13 | Dot product and cosine: measuring 'alike' | [The Illustrated Word2vec (Jay Alammar): 'Personality Embeddings' only](https://jalammar.github.io/illustrated-word2vec/) | Dot product and cosine similarity | notebook |
| 14 | Real embeddings: let a model choose the numbers | [Embedding space and static embeddings (Google ML Crash Course)](https://developers.google.com/machine-learning/crash-course/embeddings/embedding-space) | Unit vectors | notebook |
| 15 | A search engine in 30 lines of NumPy | [Introducing Contextual Retrieval (Anthropic): 'A primer on RAG'](https://www.anthropic.com/news/contextual-retrieval) | Matrix × vector | notebook |
| 16 | Is retrieval any good? recall@k | [Evaluation measures in information retrieval (Pinecone)](https://www.pinecone.io/learn/offline-evaluation/) | recall@k and MRR | notebook |
| 17 | Chunking: same data, different answers | [Introducing Contextual Retrieval (Anthropic)](https://www.anthropic.com/news/contextual-retrieval) | – | notebook |
| 18 | A vector database vs. your NumPy: what does it add? | [Chroma: getting started](https://docs.trychroma.com/docs/overview/getting-started) | Exact vs. approximate search | notebook |
| 19 | Plug retrieval into version B and measure again | [Your AI Product Needs Evals: 'Evaluating RAG'](https://hamel.dev/blog/posts/evals/) | – | notebook |
| 20 | Explain it to a customer: what RAG can and cannot promise | [Introducing Contextual Retrieval: 'Further boosting performance with Reranking' and 'Cost and latency considerations'](https://www.anthropic.com/news/contextual-retrieval) | – | diagram |

## Project 3 · Learn a formula from data (days 21–29)

Let the computer find your hosting-cost formula, then a yes/no classifier, by gradient descent.

Maths you will meet: lines and slopes, loss, derivatives, gradient descent, overfitting, sigmoid.

| Day | Topic | Learn (main resource) | Maths | Artifact |
|---|---|---|---|---|
| 21 | Functions and slopes: your hosting bill as a line | [Linear regression (Google ML Crash Course): first page](https://developers.google.com/machine-learning/crash-course/linear-regression) | A line: y = w·x + b | notebook |
| 22 | Loss: one number for 'how wrong' | [Loss (Google ML Crash Course)](https://developers.google.com/machine-learning/crash-course/linear-regression/loss) | Mean squared error (MSE) | notebook |
| 23 | Derivative: how much the loss moves when you nudge | [The paradox of the derivative (3Blue1Brown, Calculus chapter 2)](https://www.3blue1brown.com/lessons/derivatives) | A derivative, by nudging | notebook |
| 24 | Gradient descent: walk downhill in small steps | [Gradient descent (Google ML Crash Course)](https://developers.google.com/machine-learning/crash-course/linear-regression/gradient-descent) | The gradient | notebook |
| 25 | Learning rate: too small, too big, just right | [Hyperparameters (Google ML Crash Course)](https://developers.google.com/machine-learning/crash-course/linear-regression/hyperparameters) | Scaling the inputs | notebook |
| 26 | From nudges to a formula: the chain rule, first taste | [Visualizing the chain rule and product rule (3Blue1Brown, Calculus)](https://www.3blue1brown.com/lessons/chain-rule-and-product-rule) | The chain rule | notebook |
| 27 | Overfitting: when the model memorises | [Dividing the original dataset (Google ML Crash Course)](https://developers.google.com/machine-learning/crash-course/overfitting/dividing-datasets) | Polynomials | notebook |
| 28 | From numbers to yes/no: will this customer escalate? | [Logistic regression: calculating a probability (Google ML Crash Course)](https://developers.google.com/machine-learning/crash-course/logistic-regression/sigmoid-function) | Sigmoid and log loss | notebook |
| 29 | Wrap-up: programming vs. learning, explained | [But what is a Neural Network? (3Blue1Brown, Neural Networks chapter 1): first part](https://www.3blue1brown.com/lessons/neural-networks) | – | diagram |

## Project 4 · Backprop by hand (micrograd) (days 30–38)

Build a tiny autograd engine and neural-net library, then train it.

Maths you will meet: the chain rule.

| Day | Topic | Learn (main resource) | Maths | Artifact |
|---|---|---|---|---|
| 30 | One neuron, explained with your escalation data | [But what is a Neural Network? (3Blue1Brown, Neural Networks chapter 1)](https://www.3blue1brown.com/lessons/neural-networks) | Weighted sum + activation | notebook |
| 31 | A number that remembers where it came from | [Building micrograd (Andrej Karpathy): 'starting the core Value object' (19:09) to 'manual backpropagation example #1' (32:10)](https://www.youtube.com/watch?v=VMj-3S1tku0&t=1149s) | An expression graph | code |
| 32 | Backprop by hand: the chain rule in action | [Building micrograd: 'manual backpropagation example #1' (32:10 to 51:10)](https://www.youtube.com/watch?v=VMj-3S1tku0&t=1930s) | Chain rule: local × upstream | notebook |
| 33 | Automate it: a _backward for every operation | [Building micrograd: 'implementing the backward function for each operation' (1:09:02 to 1:22:28)](https://www.youtube.com/watch?v=VMj-3S1tku0&t=4142s) | Topological order | code |
| 34 | The bug when a value is used twice | [Building micrograd: 'fixing a backprop bug when one node is used multiple times' (1:22:28 to 1:39:31)](https://www.youtube.com/watch?v=VMj-3S1tku0&t=4948s) | Gradients add up | code |
| 35 | Same thing in PyTorch: what the library does for you | [Building micrograd: 'doing the same thing but in PyTorch' (1:39:31 to 1:43:55)](https://www.youtube.com/watch?v=VMj-3S1tku0&t=5971s) | Tensors | notebook |
| 36 | A tiny neural-net library: Neuron, Layer, MLP | [Building micrograd: 'building out a neural net library' (1:43:55 to 1:57:56)](https://www.youtube.com/watch?v=VMj-3S1tku0&t=6235s) | Layers | code |
| 37 | The training loop: forward, backward, update, repeat | [Building micrograd: 'collecting all of the parameters' to 'summary' (1:57:56 to 2:14:03)](https://www.youtube.com/watch?v=VMj-3S1tku0&t=7076s) | – | notebook |
| 38 | Wrap-up: what training really is | [What is backpropagation really doing? (3Blue1Brown)](https://www.3blue1brown.com/lessons/backpropagation) | – | diagram |

## Project 5 · Tiny GPT (days 39–51)

Go from counting letters to a small Transformer that writes Shakespeare-like text.

Maths you will meet: probability, logarithms, softmax, matrix multiplication, attention.

| Day | Topic | Learn (main resource) | Maths | Artifact |
|---|---|---|---|---|
| 39 | Probability: counting what comes next | [Building makemore (Andrej Karpathy): 'reading and exploring the dataset' (03:03) to 'deleting spurious tokens' (24:02)](https://www.youtube.com/watch?v=PaCmpygFfXo&t=183s) | Conditional probability | notebook |
| 40 | Sampling: let the counts write new names | [Building makemore: 'sampling from the model' (24:02 to 36:17)](https://www.youtube.com/watch?v=PaCmpygFfXo&t=1442s) | A probability distribution | notebook |
| 41 | A loss for language: negative log likelihood | [Building makemore: 'loss function (the negative log likelihood…)' (50:14 to 1:02:57)](https://www.youtube.com/watch?v=PaCmpygFfXo&t=3014s) | Logarithms | notebook |
| 42 | Softmax and temperature: from scores to probabilities | [Building makemore: 'one-hot encodings' to 'softmax' (1:10:01 to 1:26:17)](https://www.youtube.com/watch?v=PaCmpygFfXo&t=4201s) | Softmax | notebook |
| 43 | The neural bigram: the same answer, learned | [Building makemore: 'vectorized loss' to 'sampling from the neural net' (1:35:49 to 1:56:16)](https://www.youtube.com/watch?v=PaCmpygFfXo&t=5749s) | One-hot × matrix = picking a row | notebook |
| 44 | Tokens: what the model reads, and why Hinglish costs more | [Deep Dive into LLMs (Andrej Karpathy): 'tokenization' (07:47 to 14:27)](https://www.youtube.com/watch?v=7xTGNNLPyMI&t=467s) | Ratios | notebook |
| 45 | From text to training batches: the shift-by-one trick | [Let's build GPT (Andrej Karpathy): 'reading and exploring the data' to 'data loader' (07:52 to 22:11)](https://www.youtube.com/watch?v=kCc8FmEb1nY&t=472s) | Shapes | notebook |
| 46 | Averaging the past with one matrix multiply | [Let's build GPT: 'version 1' to 'minor code cleanup' (42:13 to 58:26)](https://www.youtube.com/watch?v=kCc8FmEb1nY&t=2533s) | Matrix multiply as weighted averages | notebook |
| 47 | Attention by hand: queries, keys and values | [Attention in transformers, step-by-step (3Blue1Brown)](https://www.3blue1brown.com/lessons/attention) | Query · key = relevance | diagram |
| 48 | One self-attention head in code | [Let's build GPT: 'THE CRUX OF THE VIDEO: version 4: self-attention' to note 6 (1:02:00 to 1:19:11)](https://www.youtube.com/watch?v=kCc8FmEb1nY&t=3720s) | Scaling by √head_size | notebook |
| 49 | Multi-head, feed-forward, residual: a Transformer block | [Let's build GPT: 'inserting a single self-attention block' to 'layernorm' (1:19:11 to 1:37:49)](https://www.youtube.com/watch?v=kCc8FmEb1nY&t=4751s) | Residual connections | notebook |
| 50 | Scale it up a little and count the cost | [Let's build GPT: 'scaling up the model' to 'nanoGPT walkthrough' (1:37:49 to 1:48:53)](https://www.youtube.com/watch?v=kCc8FmEb1nY&t=5869s) | Counting parameters | notebook |
| 51 | From tiny GPT to ChatGPT: where hallucinations come from | [Let's build GPT: 'back to ChatGPT… pretraining vs. finetuning, RLHF' (1:48:53 to 1:54:32)](https://www.youtube.com/watch?v=kCc8FmEb1nY&t=6533s) | – | diagram |

## Project 6 · Back to the customer (days 52–59)

Explain project 1's failures from first principles, harden the agent, and make the final recommendation like an FDE.

Maths you will meet: nothing new: you reuse everything.

| Day | Topic | Learn (main resource) | Maths | Artifact |
|---|---|---|---|---|
| 52 | Temperature, revisited with evidence | [A statistical approach to model evaluations: Recommendation #3 'Reduce variance within questions'](https://www.anthropic.com/research/statistical-approach-to-model-evals) | Consistency rate | notebook |
| 53 | Why did it fail? Root causes from first principles | [A Field Guide to Rapidly Improving AI Products: 'Bottom-Up vs. Top-Down Analysis'](https://hamel.dev/blog/posts/field-guide/) | – | diagram |
| 54 | What a tool call really is | [Writing effective tools for agents (Anthropic)](https://www.anthropic.com/engineering/writing-tools-for-agents) | – | notebook |
| 55 | Context engineering: what the model sees is all it knows | [Effective context engineering for AI agents (Anthropic)](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | Budgets | notebook |
| 56 | Prompt injection: attack your own agent | [The lethal trifecta for AI agents (Simon Willison)](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/) | – | notebook |
| 57 | Human in the loop: where the approval step belongs | [Building effective agents: 'Appendix 1: Agents in practice, A. Customer support'](https://www.anthropic.com/engineering/building-effective-agents) | Expected cost | notebook |
| 58 | The architecture recommendation (final) | [Building effective agents: 'Summary'](https://www.anthropic.com/engineering/building-effective-agents) | – | doc |
| 59 | Customer readout: present it like an FDE | [A Field Guide to Rapidly Improving AI Products: 'Your AI Roadmap Should Count Experiments, Not Features'](https://hamel.dev/blog/posts/field-guide/) | – | diagram |
