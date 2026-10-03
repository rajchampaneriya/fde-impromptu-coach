**Daily video series**

# Software Factory: the learning path

35 videos from 10 October 2026 · one concept a day · source: https://github.com/gastownhall/gascity (verified at e244b16f3a)

Generated from `assets/factory_curriculum.json` by `fde-coach factory plan --markdown --write references/factory_learning_path.md`. Dates assume one video a day; a missed day carries its topic over, so no concept is skipped.

Rule for every video: one video, one concept, one clear takeaway, under three minutes. Understand → Explain → Demonstrate → Publish → Repeat.

Every video teaches Greg Tang style: **see it** (a real demo with real output), **group it** (one picture of the pattern), **name it** (the takeaway). Days 1–7 run in a file-based demo city; from Day 8 the demos use the default setup (bd + Dolt). Your face is never recorded.

Video format (2:50): intro 4 s · what & why 25 s · demo 100 s · picture 22 s · takeaway 12 s · outro 7 s.

## All days at a glance

| Day | Date | Topic | Demo | Takeaway |
|---|---|---|---|---|
| 1 | Sat 10 Oct | [Software Factory vs. Coding Agent](#day-1-software-factory-vs-coding-agent) | Describe the job once, come back to finished work | A coding agent gives you faster hands; a software factory gives you finished work without you in the loop. |
| 2 | Sun 11 Oct | [Gas City: Zero Hardcoded Roles](#day-2-gas-city-zero-hardcoded-roles) | Roles are just files you can read | Gas City hardcodes zero roles, so you can build the factory your team actually needs. |
| 3 | Mon 12 Oct | [The Six Primitives](#day-3-the-six-primitives) | One command per primitive | Who, what, how, where, configure, observe: six primitives hold the whole system. |
| 4 | Tue 13 Oct | [The Machinery Underneath](#day-4-the-machinery-underneath) | Kill the session, keep the work | The orchestrator never waits for a callback; it reads shared state, so work survives a crash on either side. |
| 5 | Wed 14 Oct | [Why Not a Bash Loop or CI?](#day-5-why-not-a-bash-loop-or-ci) | A loop forgets; the store remembers | A loop repeats; an orchestrator remembers. |
| 6 | Thu 15 Oct | [The Toolbelt: gc, bd, tmux, Dolt](#day-6-the-toolbelt-gc-bd-tmux-dolt) | The toolbelt, one command each | Learn which tool owns which job, and every error message gets easier to read. |
| 7 | Fri 16 Oct | [City and Rig: The Factory Floor](#day-7-city-and-rig-the-factory-floor) | A city and a rig in four commands | The city is your factory floor; a rig is a project you bring onto it. |
| 8 | Sat 17 Oct | [Your First Sling: The Work Lifecycle](#day-8-your-first-sling-the-work-lifecycle) | One sling, start to finish | One sling sets the whole loop in motion: bead, session, work, close. |
| 9 | Sun 18 Oct | [The Bead: Work That Survives a Crash](#day-9-the-bead-work-that-survives-a-crash) | A bead from open to closed | Sessions are disposable; beads are not. |
| 10 | Mon 19 Oct | [Everything Is a Bead](#day-10-everything-is-a-bead) | Mail, sessions and tasks in one list | When everything is a bead, one set of tools works on everything. |
| 11 | Tue 20 Oct | [Dependencies: Order Without a Scheduler](#day-11-dependencies-order-without-a-scheduler) | Watch blocked work appear when it's ready | Agents only see ready work, so the right order emerges from the graph. |
| 12 | Wed 21 Oct | [Convoys: Track a Batch as One](#day-12-convoys-track-a-batch-as-one) | A convoy that closes itself | A convoy groups work without making the pieces wait on each other. |
| 13 | Thu 22 Oct | [The Pull Model: How Agents Find Work](#day-13-the-pull-model-how-agents-find-work) | Routing picks the queue; the agent pulls | Routing decides which queue a bead lands in; readiness decides whether anyone can see it. |
| 14 | Fri 23 Oct | [Demo: A Tiny Work Graph by Hand](#day-14-demo-a-tiny-work-graph-by-hand) | A tiny work graph by hand | A formula simply creates this graph for you, and now you know exactly what it builds. |
| 15 | Sat 24 Oct | [Agents: A Role Is a Prompt](#day-15-agents-a-role-is-a-prompt) | Create a reviewer in two files | A reviewer is nothing more than the prompt you wrote for it. |
| 16 | Sun 25 Oct | [Harnesses: One Fleet, Many Coding Agents](#day-16-harnesses-one-fleet-many-coding-agents) | Swap the model with one line | In Gas City, a mixed fleet of coding agents is just configuration. |
| 17 | Mon 26 Oct | [Sessions: On-Demand vs. Always-On](#day-17-sessions-on-demand-vs-always-on) | Peek, nudge and read a live session | Agents are definitions; sessions are the live processes, and they're disposable by design. |
| 18 | Tue 27 Oct | [Agents Talk Only Through the Store](#day-18-agents-talk-only-through-the-store) | Mail the mayor; watch the work move | No agent holds a reference to another, so any of them can crash, scale or swap. |
| 19 | Wed 28 Oct | [Hooks: Wiring a Coding Agent Into the City](#day-19-hooks-wiring-a-coding-agent-into-the-city) | The hooks that wire Claude into the city | Hooks turn a bare coding agent into a member of the city. |
| 20 | Thu 29 Oct | [Pools: Scaling Workers to Demand](#day-20-pools-scaling-workers-to-demand) | One worker definition, several sessions | A pool turns one agent definition into exactly as many workers as the work needs. |
| 21 | Fri 30 Oct | [Demo: Build a Reviewer and Sling a Review](#day-21-demo-build-a-reviewer-and-sling-a-review) | Build a reviewer and sling a review | A role, a prompt and one sling: that's a new specialist on your factory floor. |
| 22 | Sat 31 Oct | [Formulas: Write the Method Down Once](#day-22-formulas-write-the-method-down-once) | Pancakes as a graph | Write the method down once, and the orchestrator can run it again and again. |
| 23 | Sun 01 Nov | [From TOML to Beads: Cook vs. Sling](#day-23-from-toml-to-beads-cook-vs-sling) | Cook it, then sling it | A formula is the method; applying it prints the work as beads that outlive everything. |
| 24 | Mon 02 Nov | [Variables: One Method, Many Runs](#day-24-variables-one-method-many-runs) | One method, two different runs | Variables turn one written method into a method for every situation. |
| 25 | Tue 03 Nov | [v1 vs. v2 Formulas: Who Is the Engine?](#day-25-v1-vs-v2-formulas-who-is-the-engine) | Same steps, two engines | In v2 the orchestrator, not a single agent, is the engine. |
| 26 | Wed 04 Nov | [Check and Retry: Work That Verifies Itself](#day-26-check-and-retry-work-that-verifies-itself) | A step that is done only when a script agrees | With check, done means verified, not just claimed. |
| 27 | Thu 05 Nov | [Drain: Fan Out Over a Convoy](#day-27-drain-fan-out-over-a-convoy) | Fan a convoy out into parallel runs | Drain turns a convoy of any size into parallel, isolated runs. |
| 28 | Fri 06 Nov | [Demo: Write and Run the Pancakes Formula](#day-28-demo-write-and-run-the-pancakes-formula) | Write the formula, run it, watch it finish | Write the method, preview it, run it, and the orchestrator drives it to done. |
| 29 | Sat 07 Nov | [Orders: When, Not How](#day-29-orders-when-not-how) | An order that fires by itself | Formulas say how; orders say when, and then nobody has to press go. |
| 30 | Sun 08 Nov | [Exec Orders: Automation Without an LLM](#day-30-exec-orders-automation-without-an-llm) | A chore with no model at all | Use agents for judgment and scripts for chores. |
| 31 | Mon 09 Nov | [Health Patrol: Let It Crash](#day-31-health-patrol-let-it-crash) | Kill the mayor; patrol brings it back | Gas City doesn't prevent crashes; it makes them cheap. |
| 32 | Tue 10 Nov | [Events: Watching the Fleet](#day-32-events-watching-the-fleet) | Watch the event stream while work happens | Events let humans watch the factory, and let the factory react to itself. |
| 33 | Wed 11 Nov | [Packs: What Configures the Factory](#day-33-packs-what-configures-the-factory) | Make a tiny pack | A pack turns how your team works into versioned, shareable files. |
| 34 | Thu 12 Nov | [Imports: Reuse Without Copying](#day-34-imports-reuse-without-copying) | Import the pack; the name gets qualified | Import packs, pin versions, patch the differences, and never fork. |
| 35 | Fri 13 Nov | [The Whole Job, End to End](#day-35-the-whole-job-end-to-end) | The whole factory, from one formula | Write the method once, and the factory turns it into finished work. |

## Module 1: The Big Picture

Know what a software factory is and the shape of Gas City.

### Day 1: Software Factory vs. Coding Agent

Saturday 10 October 2026 · concept: **Software factory** · builds on: Nothing — this is where the path starts.

> Takeaway: A coding agent gives you faster hands; a software factory gives you finished work without you in the loop.

**WHAT** — A software factory runs a written-down method across a fleet of coding agents, without you steering every step.

- A fleet, not one agent
- A written-down method
- Runs without you in the loop

**WHY** — One coding agent is a faster pair of hands, but it works alone, needs you watching, and loses context when it crashes.

- One session, one train of thought
- You hover and steer
- A crash loses the context

**HOW** — You write the method once; an orchestrator splits the job into tracked work, runs independent pieces in parallel and retries failures.

- Write the method once
- Orchestrator splits the job into tracked units
- Parallel where possible, wait where needed
- Retry until the job is done

**See it — demo: Describe the job once, come back to finished work** (file-based demo city (no Dolt); uses Claude Code (tokens), slow parts become time-lapse cuts)

```
gc sling hello-factory/claude "Create hello.py that prints Hello, factory"
gc beads show <bead>   # time-lapse until 'closed'
python3 hello.py
```

- One command. I describe the job and walk away.
- No steering: an agent picks it up and closes it.
- Finished work, in the repo.

**Group it — picture:** Side by side: Interactive session vs. Software factory (Faster hands vs. a system that produces finished work).

**Say it simply:** A great chef cooks one meal fast. A restaurant kitchen has recipes, stations and tickets, so dinner is served even when one cook goes home.

- **orchestrator** — the program that hands out work, tracks it and keeps it moving
- **fleet** — many coding agents working at the same time

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Software factory** · A fleet, not one agent · A written-down method · why: One session, one train of thought |
| 0:29–2:09 | See it | Demo: Describe the job once, come back to finished work. One command. I describe the job and walk away. → No steering: an agent picks it up and closes it. → Finished work, in the repo. |
| 2:09–2:31 | Group it | Write the method once → Orchestrator splits the job into tracked units → Parallel where possible, wait where needed → Retry until the job is done (on screen: Side by side: Interactive session vs. Software factory) |
| 2:31–2:43 | Name it | “A coding agent gives you faster hands; a software factory gives you finished work without you in the loop.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** Sketch two columns on paper: interactive session vs. software factory. The HOW slide is that sketch.

**Repository references:**

- [docs/index.mdx](https://github.com/gastownhall/gascity/blob/main/docs/index.mdx)
- [docs/getting-started/faq.md](https://github.com/gastownhall/gascity/blob/main/docs/getting-started/faq.md)

**Verify before Take 1:**

- [ ] docs/index.mdx describes Gas City as the platform for building software factories.
- [ ] The FAQ promise: describe a feature once and come back to a finished branch.

### Day 2: Gas City: Zero Hardcoded Roles

Sunday 11 October 2026 · concept: **Gas City** · builds on: Day 1: Software Factory vs. Coding Agent

> Takeaway: Gas City hardcodes zero roles, so you can build the factory your team actually needs.

**WHAT** — Gas City is an open-source toolkit for building software factories: orchestration infrastructure for multi-agent coding.

- Open source, MIT licence
- Extracted from Gas Town
- A toolkit, not one fixed bot

**WHY** — Hardcoded roles lock you into someone else's team shape. Gas City makes every role configuration, so one engine runs many designs.

- No built-in manager or reviewer
- Roles are config plus prompts
- One engine, many orchestrators

**HOW** — The engine only knows primitives; packs supply the roles. Swap the packs and you get a different factory, Gas Town included.

- The engine knows primitives only
- Packs bring the roles
- Gas Town is one pack on top
- Your team shape is your pack

**See it — demo: Roles are just files you can read** (file-based demo city (no Dolt); no agent, fast)

```
ls agents
head -12 agents/mayor/prompt.template.md
gc prime mayor | head -10
```

- Every role in this city is a folder.
- The mayor is a prompt, not code.
- gc prime shows exactly what the agent starts with.

**Group it — picture:** Layers: Your factory / Packs / Gas City engine (Roles live in packs, not in the binary).

**Say it simply:** Like a game engine: the engine handles physics and drawing; each game brings its own characters.

- **SDK** — a toolkit you build your own product with
- **pack** — a folder of config that defines agents, methods and schedules

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Gas City** · Open source, MIT licence · Extracted from Gas Town · why: No built-in manager or reviewer |
| 0:29–2:09 | See it | Demo: Roles are just files you can read. Every role in this city is a folder. → The mayor is a prompt, not code. → gc prime shows exactly what the agent starts with. |
| 2:09–2:31 | Group it | The engine knows primitives only → Packs bring the roles → Gas Town is one pack on top → Your team shape is your pack (on screen: Layers: Your factory / Packs / Gas City engine) |
| 2:31–2:43 | Name it | “Gas City hardcodes zero roles, so you can build the factory your team actually needs.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** Open the Gas Town role table in coming-from-gastown.md and pick two roles to mention: Mayor and Polecat.

**Repository references:**

- [README.md](https://github.com/gastownhall/gascity/blob/main/README.md)
- [docs/getting-started/how-gas-city-works.md](https://github.com/gastownhall/gascity/blob/main/docs/getting-started/how-gas-city-works.md)
- [docs/getting-started/coming-from-gastown.md](https://github.com/gastownhall/gascity/blob/main/docs/getting-started/coming-from-gastown.md)
- [diagram: gastown-agents-by-scope](https://github.com/gastownhall/gascity/blob/main/docs/diagrams/excalidraw-rendered/gastown-agents-by-scope.svg)

**Verify before Take 1:**

- [ ] how-gas-city-works.md: the orchestrator hardcodes zero roles.
- [ ] README and FAQ: Gas City is MIT-licensed.
- [ ] coming-from-gastown.md: every Gas Town role maps to a configured agent.

### Day 3: The Six Primitives

Monday 12 October 2026 · concept: **Six primitives** · builds on: Day 2: Gas City: Zero Hardcoded Roles

> Takeaway: Who, what, how, where, configure, observe: six primitives hold the whole system.

**WHAT** — Everything in Gas City is built from six primitives: Agent, Bead, Formula, Rig, Pack and Event.

- Agent = who · Bead = what
- Formula = how · Rig = where
- Pack = configures · Event = observe

**WHY** — Six words give you a map. Every feature you meet later is one of them, or a combination of them.

- Small vocabulary, big system
- New features slot into the map
- Easier to explain and debug

**HOW** — Packs declare agents and formulas; a formula operates over beads; agents execute beads in a rig; events fire so everyone can watch.

- Pack configures agents and formulas
- Formula operates over beads
- Agents execute beads in a rig
- Events let humans and agents observe

**See it — demo: One command per primitive** (file-based demo city (no Dolt); no agent, fast)

```
ls agents formulas orders
gc rig list
gc beads list --all | head -8
head -8 pack.toml
gc events --since 24h | tail -4
```

- Agents, formulas, orders: declared by the pack.
- Rig: where the work happens.
- Beads: the work itself.
- Pack: what configures all of it.
- Events: how we observe it.

**Group it — picture:** Gas City diagram `primitives` (The six primitives and how they relate).

**Say it simply:** Who, what, how and where are the questions every news story answers. Add who set it up and how you hear about it.

- **primitive** — a basic building block that isn't made of smaller blocks

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Six primitives** · Agent = who · Bead = what · Formula = how · Rig = where · why: Small vocabulary, big system |
| 0:29–2:09 | See it | Demo: One command per primitive. Agents, formulas, orders: declared by the pack. → Rig: where the work happens. → Beads: the work itself. → Pack: what configures all of it. → Events: how we observe it. |
| 2:09–2:31 | Group it | Pack configures agents and formulas → Formula operates over beads → Agents execute beads in a rig → Events let humans and agents observe (on screen: Gas City diagram `primitives`) |
| 2:31–2:43 | Name it | “Who, what, how, where, configure, observe: six primitives hold the whole system.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** The primitives diagram. Practise pointing at each box in order: Pack, Formula, Bead, Agent, Rig, Event.

**Repository references:**

- [docs/getting-started/how-gas-city-works.md](https://github.com/gastownhall/gascity/blob/main/docs/getting-started/how-gas-city-works.md)
- [diagram: primitives](https://github.com/gastownhall/gascity/blob/main/docs/diagrams/excalidraw-rendered/primitives.svg)

**Verify before Take 1:**

- [ ] The six-primitives table in how-gas-city-works.md: Agent WHO, Bead WHAT, Formula HOW, Rig WHERE, Pack CONFIGURES, Event OBSERVE.

### Day 4: The Machinery Underneath

Tuesday 13 October 2026 · concept: **Orchestrator, store, event bus** · builds on: Day 3: The Six Primitives

> Takeaway: The orchestrator never waits for a callback; it reads shared state, so work survives a crash on either side.

**WHAT** — Three pieces of plumbing run the primitives: the orchestrator, the bead store and the event bus.

- Orchestrator runs the work
- Bead store remembers it
- Event bus announces it

**WHY** — If progress lived inside an agent's memory, one crash would erase it. In shared state, work survives a crash on either side.

- Agents crash
- Orchestrators restart
- Shared state survives both

**HOW** — The orchestrator starts and stops sessions, but reads their progress from the store and event bus instead of waiting for callbacks.

- Orchestrator acts on sessions
- Sessions record progress in beads
- Orchestrator reads the store, not callbacks
- After a crash, resume from the store

**See it — demo: Kill the session, keep the work** (file-based demo city (no Dolt); uses Claude Code (tokens), slow parts become time-lapse cuts)

```
gc sling hello-factory/claude "Add a docstring and a main() function to hello.py"
gc session list --template hello-factory/claude   # time-lapse until 'hello-factory/claude'
gc session kill <session>
gc beads show <bead>
gc beads show <bead>   # time-lapse until 'closed'
```

- Give the city some work.
- A session starts for it.
- Now I kill that session on purpose.
- The work is still in the store, not lost with the agent.
- A fresh session resumes it from the store.

**Group it — picture:** Flow: Orchestrator → Sessions → Bead store + events (loops back) (The loop closes through shared state).

**Say it simply:** A kitchen ticket rail: cooks come and go, but the tickets on the rail say exactly what is done and what is next.

- **bead store** — the database where every unit of work is recorded
- **event bus** — a running feed of 'this just happened' messages

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Orchestrator, store, event bus** · Orchestrator runs the work · Bead store remembers it · why: Agents crash |
| 0:29–2:09 | See it | Demo: Kill the session, keep the work. Give the city some work. → A session starts for it. → Now I kill that session on purpose. → The work is still in the store, not lost with the agent. → A fresh session resumes it from the store. |
| 2:09–2:31 | Group it | Orchestrator acts on sessions → Sessions record progress in beads → Orchestrator reads the store, not callbacks → After a crash, resume from the store (on screen: Flow: Orchestrator → Sessions → Bead store + events (loops back)) |
| 2:31–2:43 | Name it | “The orchestrator never waits for a callback; it reads shared state, so work survives a crash on either side.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** Draw the loop by hand once: orchestrator, sessions, store, back to the orchestrator.

**Repository references:**

- [docs/getting-started/how-gas-city-works.md](https://github.com/gastownhall/gascity/blob/main/docs/getting-started/how-gas-city-works.md)
- [engdocs/architecture/nine-concepts.md](https://github.com/gastownhall/gascity/blob/main/engdocs/architecture/nine-concepts.md)

**Verify before Take 1:**

- [ ] how-gas-city-works.md, 'The machinery underneath': Orchestrator, Bead store, Event bus.
- [ ] Same page: 'The loop closes through shared state'.

### Day 5: Why Not a Bash Loop or CI?

Wednesday 14 October 2026 · concept: **Orchestrator vs. loop** · builds on: Day 4: The Machinery Underneath

> Takeaway: A loop repeats; an orchestrator remembers.

**WHAT** — An orchestrator runs work as a graph with a durable memory. A bash loop only restarts an agent; CI only checks a finished change.

- Loop: restart blindly
- CI: verify afterwards
- Orchestrator: plan, run, remember

**WHY** — A loop has no model of the work. Every round starts blind, and a crash loses whatever the last round knew.

- No model of the work
- A crash loses knowledge
- CI doesn't produce the change

**HOW** — The orchestrator holds each step until its dependencies close, fans ready steps out, retries failures and stores every unit durably.

- Steps wait for their dependencies
- Ready steps fan out
- Failures are retried
- Everything is stored durably

**See it — demo: A loop forgets; the store remembers** (file-based demo city (no Dolt); no agent, fast)

```
for round in 1 2 3; do echo "round $round: starting from nothing"; done
gc beads list --all | head -8
gc events --since 48h | tail -5
```

- A bash loop: every round starts blind.
- The city keeps every unit of work it has ever done.
- And a history of what happened, in order.

**Group it — picture:** Side by side: Bash loop vs. Orchestrator (CI is complementary: it verifies the change a formula produces).

**Say it simply:** A loop is an alarm clock that keeps waking you up. An orchestrator is a project manager with a checklist.

- **graph** — steps joined by 'this finishes before that' arrows
- **durable** — saved, so it survives crashes and restarts

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Orchestrator vs. loop** · Loop: restart blindly · CI: verify afterwards · why: No model of the work |
| 0:29–2:09 | See it | Demo: A loop forgets; the store remembers. A bash loop: every round starts blind. → The city keeps every unit of work it has ever done. → And a history of what happened, in order. |
| 2:09–2:31 | Group it | Steps wait for their dependencies → Ready steps fan out → Failures are retried → Everything is stored durably (on screen: Side by side: Bash loop vs. Orchestrator) |
| 2:31–2:43 | Name it | “A loop repeats; an orchestrator remembers.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** Write the naive loop on a sticky note as the 'before' picture.

**Repository references:**

- [docs/getting-started/faq.md](https://github.com/gastownhall/gascity/blob/main/docs/getting-started/faq.md)

**Verify before Take 1:**

- [ ] FAQ: 'Couldn't I get the same thing from a bash loop or CI?'

### Day 6: The Toolbelt: gc, bd, tmux, Dolt

Thursday 15 October 2026 · concept: **Supporting tools** · builds on: Day 5: Why Not a Bash Loop or CI?

> Takeaway: Learn which tool owns which job, and every error message gets easier to read.

**WHAT** — Gas City runs on a small toolbelt: gc drives the city, bd manages beads, tmux hosts sessions and Dolt stores the beads.

- gc = the city CLI
- bd = the beads CLI
- tmux = sessions · Dolt = storage

**WHY** — When something breaks, knowing which tool owns which job tells you exactly where to look.

- Each tool has one job
- Errors point at a tool
- A lighter start is possible

**HOW** — brew install gascity brings the dependencies, and gc init checks them. Set GC_BEADS=file to skip Dolt and bd while you learn.

- brew install gascity
- gc init and gc start check prerequisites
- Every agent session lives in tmux
- GC_BEADS=file for a light start

**See it — demo: The toolbelt, one command each** (file-based demo city (no Dolt); no agent, fast)

```
gc version
tmux -V && tmux ls 2>/dev/null | head -3
grep -A1 '\[beads\]' city.toml
bd --version; dolt version | head -1
```

- gc drives the city.
- tmux hosts every agent session.
- This demo city uses the file store: no Dolt needed.
- bd and Dolt are the default store; we switch to it next week.

**Group it — picture:** Layers: gc / bd / tmux / Dolt (One job per tool).

**Say it simply:** A workshop: the foreman's clipboard, the job tickets, the workbenches and the filing cabinet.

- **tmux** — a tool that keeps many terminals running, even in the background
- **Dolt** — a SQL database with Git-style version history

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Supporting tools** · gc = the city CLI · bd = the beads CLI · why: Each tool has one job |
| 0:29–2:09 | See it | Demo: The toolbelt, one command each. gc drives the city. → tmux hosts every agent session. → This demo city uses the file store: no Dolt needed. → bd and Dolt are the default store; we switch to it next week. |
| 2:09–2:31 | Group it | brew install gascity → gc init and gc start check prerequisites → Every agent session lives in tmux → GC_BEADS=file for a light start (on screen: Layers: gc / bd / tmux / Dolt) |
| 2:31–2:43 | Name it | “Learn which tool owns which job, and every error message gets easier to read.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** The prerequisites table from the README: tmux, git, jq, dolt, bd, flock.

**Repository references:**

- [README.md](https://github.com/gastownhall/gascity/blob/main/README.md)
- [docs/getting-started/installation.md](https://github.com/gastownhall/gascity/blob/main/docs/getting-started/installation.md)
- [docs/getting-started/faq.md](https://github.com/gastownhall/gascity/blob/main/docs/getting-started/faq.md)

**Verify before Take 1:**

- [ ] README prerequisites table and the GC_BEADS=file note.
- [ ] FAQ: agent sessions run in tmux.

### Day 7: City and Rig: The Factory Floor

Friday 16 October 2026 · concept: **City and rig** · builds on: Day 6: The Toolbelt: gc, bd, tmux, Dolt

> Takeaway: The city is your factory floor; a rig is a project you bring onto it.

**WHAT** — A city is the directory holding your agents, formulas and settings. A rig is a project, usually a Git repo, registered with it.

- City = the factory floor
- Rig = a project brought in
- Each rig gets its own bead prefix

**WHY** — Work needs a home and a boundary: the city holds the method, and each rig keeps its work apart from other projects.

- One home for definitions
- Projects stay isolated
- Repos can live anywhere

**HOW** — gc init creates and starts a city. gc rig add registers a project, gives it a bead prefix and keeps its path in .gc/site.toml.

- gc init ~/my-city
- pack.toml and city.toml
- gc rig add ~/my-project
- Bead prefix such as mp-

**See it — demo: A city and a rig in four commands** (file-based demo city (no Dolt); no agent, fast)

```
gc init --template gascity --default-provider claude ./demo-city | tail -4
ls demo-city
mkdir demo-app && git -C demo-app init -q && cd demo-city && gc rig add ../demo-app
cd demo-city && gc rig list
```

- gc init creates and starts a city.
- pack.toml is the portable part; city.toml is this deployment.
- Bring a project in as a rig. Note its prefix.
- The city now knows where work can happen.

**Group it — picture:** Code (shell), 8 lines (One city, one rig).

**Say it simply:** The city is the factory building; each rig is a production line for one product.

- **rig** — a project directory registered with the city
- **prefix** — the two letters on every bead ID that show which project it belongs to

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **City and rig** · City = the factory floor · Rig = a project brought in · why: One home for definitions |
| 0:29–2:09 | See it | Demo: A city and a rig in four commands. gc init creates and starts a city. → pack.toml is the portable part; city.toml is this deployment. → Bring a project in as a rig. Note its prefix. → The city now knows where work can happen. |
| 2:09–2:31 | Group it | gc init ~/my-city → pack.toml and city.toml → gc rig add ~/my-project → Bead prefix such as mp- (on screen: Code (shell), 8 lines) |
| 2:31–2:43 | Name it | “The city is your factory floor; a rig is a project you bring onto it.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** Run gc init and gc rig add once, or use the Tutorial 01 transcript on the slide.

**Repository references:**

- [docs/tutorials/01-cities-and-rigs.md](https://github.com/gastownhall/gascity/blob/main/docs/tutorials/01-cities-and-rigs.md)
- [docs/getting-started/quickstart.md](https://github.com/gastownhall/gascity/blob/main/docs/getting-started/quickstart.md)

**Verify before Take 1:**

- [ ] Tutorial 01: gc rig add prints 'Prefix: mp'.
- [ ] Tutorial 01: the rig path binding lives in .gc/site.toml.

## Module 2: Work: Beads

Understand the unit of work, how it is ordered, grouped and claimed.

### Day 8: Your First Sling: The Work Lifecycle

Saturday 17 October 2026 · concept: **gc sling** · builds on: Day 7: City and Rig: The Factory Floor

> Takeaway: One sling sets the whole loop in motion: bead, session, work, close.

**WHAT** — Slinging hands a task to an agent: gc sling creates a bead and routes it, and the city does the rest.

- One command
- Creates a bead
- Routes it to an agent

**WHY** — This is the smallest complete loop. Once you see it, every bigger workflow is more of the same.

- Smallest end-to-end job
- Same loop at every scale
- You watch, you don't steer

**HOW** — Sling creates a bead and a route. A reconcile tick spawns a session, the agent finds its work, edits the rig and closes the bead.

- Sling creates a bead and a route
- A tick spawns a session
- The agent works in the rig
- The bead closes; events record it

**See it — demo: One sling, start to finish** (default demo city (bd + Dolt); uses Claude Code (tokens), slow parts become time-lapse cuts)

```
gc sling hello-factory/claude "Write hello world in python to the file hello_world.py"
gc bd show <bead>
gc bd show <bead>   # time-lapse until 'closed'
python3 hello_world.py
```

- Sling creates a bead and routes it.
- The bead: open, routed, tracked by a convoy.
- A tick spawns a session; the agent works and closes it.
- And the file is there.

**Group it — picture:** Gas City diagram `work-lifecycle` (The work lifecycle after one sling).

**Say it simply:** Dropping a ticket in the kitchen window: you don't pick the cook, the kitchen picks it up.

- **sling** — Gas City's verb for creating work and routing it in one go
- **tick** — the orchestrator's regular check-in, every 30 seconds by default

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **gc sling** · One command · Creates a bead · why: Smallest end-to-end job |
| 0:29–2:09 | See it | Demo: One sling, start to finish. Sling creates a bead and routes it. → The bead: open, routed, tracked by a convoy. → A tick spawns a session; the agent works and closes it. → And the file is there. |
| 2:09–2:31 | Group it | Sling creates a bead and a route → A tick spawns a session → The agent works in the rig → The bead closes; events record it (on screen: Gas City diagram `work-lifecycle`) |
| 2:31–2:43 | Name it | “One sling sets the whole loop in motion: bead, session, work, close.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** The hello-world sling transcript from Tutorial 01.

**Repository references:**

- [docs/tutorials/01-cities-and-rigs.md](https://github.com/gastownhall/gascity/blob/main/docs/tutorials/01-cities-and-rigs.md)
- [docs/getting-started/quickstart.md](https://github.com/gastownhall/gascity/blob/main/docs/getting-started/quickstart.md)
- [diagram: work-lifecycle](https://github.com/gastownhall/gascity/blob/main/docs/diagrams/excalidraw-rendered/work-lifecycle.svg)

**Verify before Take 1:**

- [ ] Tutorial 01: sling prints 'Created mp-…' and attaches the mol-do-work workflow.
- [ ] health-patrol.md: the patrol interval defaults to 30 seconds.

### Day 9: The Bead: Work That Survives a Crash

Sunday 18 October 2026 · concept: **Bead** · builds on: Day 8: Your First Sling: The Work Lifecycle

> Takeaway: Sessions are disposable; beads are not.

**WHAT** — A bead is one unit of work with an ID, a title, a status and a type.

- ID · title · status · type
- open → in_progress → closed
- Lives in the store, not the agent

**WHY** — Agents crash and sessions recycle. Because the work lives in a bead, a fresh agent picks up exactly where the last one stopped.

- Sessions are disposable
- Beads are not
- Ground truth after any restart

**HOW** — An agent claims an open bead, which moves it to in progress, and closes it when done. Blocked and deferred are managed for you.

- open: waiting
- in_progress: claimed
- closed: done
- blocked and deferred: managed for you

**See it — demo: A bead from open to closed** (default demo city (bd + Dolt); no agent, fast)

```
bd create "Fix the login bug"
bd update <bead> --status in_progress && bd show <bead> | head -3
bd close <bead>
bd list --all --flat | grep <bead>
```

- Create one unit of work.
- Claimed: in progress.
- Done: closed.
- Still in the store, with its history.

**Group it — picture:** Gas City diagram `bead-lifecycle` (A bead's lifecycle).

**Say it simply:** A sticky note on a shared board: whoever picks it up moves it to doing, then done. The note outlives any worker.

- **claim** — an agent takes a bead in one step, so nobody else works on it

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Bead** · ID · title · status · type · open → in_progress → closed · why: Sessions are disposable |
| 0:29–2:09 | See it | Demo: A bead from open to closed. Create one unit of work. → Claimed: in progress. → Done: closed. → Still in the store, with its history. |
| 2:09–2:31 | Group it | open: waiting → in_progress: claimed → closed: done → blocked and deferred: managed for you (on screen: Gas City diagram `bead-lifecycle`) |
| 2:31–2:43 | Name it | “Sessions are disposable; beads are not.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** A bd list output with the status symbols.

**Repository references:**

- [docs/tutorials/06-beads.md](https://github.com/gastownhall/gascity/blob/main/docs/tutorials/06-beads.md)
- [docs/getting-started/how-gas-city-works.md](https://github.com/gastownhall/gascity/blob/main/docs/getting-started/how-gas-city-works.md)
- [diagram: bead-lifecycle](https://github.com/gastownhall/gascity/blob/main/docs/diagrams/excalidraw-rendered/bead-lifecycle.svg)

**Verify before Take 1:**

- [ ] Tutorial 06: statuses open, in_progress, blocked, deferred, closed.
- [ ] Tutorial 06: bead IDs start with a two-letter prefix.

### Day 10: Everything Is a Bead

Monday 19 October 2026 · concept: **One store for everything** · builds on: Day 9: The Bead: Work That Survives a Crash

> Takeaway: When everything is a bead, one set of tools works on everything.

**WHAT** — Tasks, mail, sessions and convoys are all beads that differ only by type.

- task · message
- session · convoy
- One store, one way to query

**WHY** — One store means one way to query, one dependency model and one history. That is what makes the system composable.

- No separate databases
- Same tools for everything
- Features compose easily

**HOW** — bd list shows formula steps, mail and sessions side by side. A formula run lands as plain task beads tagged with metadata.

- The type column says what it is
- bd list sees everything
- Formula runs become task beads
- Metadata adds structure

**See it — demo: Mail, sessions and tasks in one list** (default demo city (bd + Dolt); no agent, fast)

```
gc mail send mayor -s "Hello" -m "Mail is a bead too"
bd show <msg> | head -4
bd list --status in_progress --flat | head -5
bd list --flat | head -8
```

- Send the mayor some mail.
- That message is a bead: type message.
- Running sessions are beads too.
- One store, one list, one way to query.

**Group it — picture:** Hub: Bead store with task, message, session, convoy (Same store, same queries; only the type differs).

**Say it simply:** One spreadsheet with a 'type' column instead of four separate spreadsheets.

- **metadata** — extra key-value notes attached to a bead

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **One store for everything** · task · message · session · convoy · why: No separate databases |
| 0:29–2:09 | See it | Demo: Mail, sessions and tasks in one list. Send the mayor some mail. → That message is a bead: type message. → Running sessions are beads too. → One store, one list, one way to query. |
| 2:09–2:31 | Group it | The type column says what it is → bd list sees everything → Formula runs become task beads → Metadata adds structure (on screen: Hub: Bead store with task, message, session, convoy) |
| 2:31–2:43 | Name it | “When everything is a bead, one set of tools works on everything.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** The bead types table from Tutorial 06.

**Repository references:**

- [docs/tutorials/06-beads.md](https://github.com/gastownhall/gascity/blob/main/docs/tutorials/06-beads.md)

**Verify before Take 1:**

- [ ] Tutorial 06 bead types table: task, message, session, convoy.
- [ ] Tutorial 06: a formula root carries gc.kind=workflow metadata.

### Day 11: Dependencies: Order Without a Scheduler

Tuesday 20 October 2026 · concept: **Blocking dependencies** · builds on: Day 10: Everything Is a Bead

> Takeaway: Agents only see ready work, so the right order emerges from the graph.

**WHAT** — A dependency says one bead must close before another can start.

- A blocks B
- Blocked work is invisible
- Order emerges from the graph

**WHY** — No central scheduler decides what runs next. Agents simply only see work that is ready.

- No scheduler bottleneck
- Nobody starts too early
- Parallel by default

**HOW** — bd dep A --blocks B adds the edge. B disappears from every agent's work query until A closes; then it shows up as ready.

- bd dep A --blocks B
- B is hidden while A is open
- A closes, B becomes ready
- Only 'blocks' affects visibility

**See it — demo: Watch blocked work appear when it's ready** (default demo city (bd + Dolt); no agent, fast)

```
bd create "Refactor auth"
bd create "Update API docs"
bd dep <a> --blocks <b>
bd ready --limit 20 | grep -E '<a>|<b>'
bd close <a> >/dev/null && bd ready --limit 20 | grep -E '<a>|<b>'
```

- Bead A.
- Bead B.
- A blocks B.
- Only A is ready. B is invisible.
- Close A, and B shows up.

**Group it — picture:** Flow: A: Refactor auth → B: Update API docs (Agents only see ready work).

**Say it simply:** You can't paint a wall before the plaster dries, so the painter isn't even told about the job yet.

- **edge** — an arrow that links two beads
- **ready** — open, with nothing blocking it

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Blocking dependencies** · A blocks B · Blocked work is invisible · why: No scheduler bottleneck |
| 0:29–2:09 | See it | Demo: Watch blocked work appear when it's ready. Bead A. → Bead B. → A blocks B. → Only A is ready. B is invisible. → Close A, and B shows up. |
| 2:09–2:31 | Group it | bd dep A --blocks B → B is hidden while A is open → A closes, B becomes ready → Only 'blocks' affects visibility (on screen: Flow: A: Refactor auth → B: Update API docs) |
| 2:31–2:43 | Name it | “Agents only see ready work, so the right order emerges from the graph.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** Two beads and one blocks edge.

**Repository references:**

- [docs/tutorials/06-beads.md](https://github.com/gastownhall/gascity/blob/main/docs/tutorials/06-beads.md)
- [docs/getting-started/how-gas-city-works.md](https://github.com/gastownhall/gascity/blob/main/docs/getting-started/how-gas-city-works.md)

**Verify before Take 1:**

- [ ] Tutorial 06 dependency table: only blocks affects work visibility.
- [ ] Check the exact bd ready flags on your bd version: bd ready --help.

### Day 12: Convoys: Track a Batch as One

Wednesday 21 October 2026 · concept: **Convoy** · builds on: Day 11: Dependencies: Order Without a Scheduler

> Takeaway: A convoy groups work without making the pieces wait on each other.

**WHAT** — A convoy is a bead that groups related beads, so you can track a batch of work as one unit.

- A container bead
- Members keep their identity
- Closes itself when all are done

**WHY** — Real work comes in batches: a sprint, a deploy, a feature. You want one answer to 'is all of this done yet?'

- One progress view
- No fake dependencies
- Auto-close, no polling

**HOW** — gc convoy create links members with tracks edges, which block nothing. When the last member closes, the convoy closes itself.

- gc convoy create "Sprint 42" ...
- tracks edges, not blocks
- gc convoy status shows progress
- Auto-close on the last member

**See it — demo: A convoy that closes itself** (default demo city (bd + Dolt); no agent, fast)

```
for t in "Design page" "Build page" "Write docs"; do bd create "$t"; done
gc convoy create landing-page $(bd list --flat | grep -E 'Design page|Build page|Write docs' | grep -oE '[a-z0-9]+-[a-z0-9]+' | head -3 | tr '\n' ' ')
bd close <a> >/dev/null && gc convoy status <convoy>
for id in $(gc convoy status <convoy> | grep -E ' open ' | awk '{print $1}'); do bd close $id >/dev/null; done; sleep 3; gc convoy status <convoy> | head -4
```

- Three independent beads.
- Group them: tracking, not blocking.
- One closed: progress 1 of 3.
- The last one closes, and so does the convoy.

**Group it — picture:** Gas City diagram `convoy-tracks-membership` (Convoy membership is tracking, not blocking).

**Say it simply:** A shipping convoy: each truck drives on its own, but you track the convoy's arrival as one event.

- **tracks edge** — an 'I care about this' link that blocks nothing

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Convoy** · A container bead · Members keep their identity · why: One progress view |
| 0:29–2:09 | See it | Demo: A convoy that closes itself. Three independent beads. → Group them: tracking, not blocking. → One closed: progress 1 of 3. → The last one closes, and so does the convoy. |
| 2:09–2:31 | Group it | gc convoy create "Sprint 42" ... → tracks edges, not blocks → gc convoy status shows progress → Auto-close on the last member (on screen: Gas City diagram `convoy-tracks-membership`) |
| 2:31–2:43 | Name it | “A convoy groups work without making the pieces wait on each other.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** The gc convoy status output for 'Sprint 42' from Tutorial 06.

**Repository references:**

- [docs/tutorials/06-beads.md](https://github.com/gastownhall/gascity/blob/main/docs/tutorials/06-beads.md)
- [diagram: convoy-tracks-membership](https://github.com/gastownhall/gascity/blob/main/docs/diagrams/excalidraw-rendered/convoy-tracks-membership.svg)

**Verify before Take 1:**

- [ ] Tutorial 06: convoy membership uses tracks edges.
- [ ] Tutorial 06: auto-close runs from the on_close hook; owned convoys skip it.

### Day 13: The Pull Model: How Agents Find Work

Thursday 22 October 2026 · concept: **Routing and readiness** · builds on: Day 12: Convoys: Track a Batch as One

> Takeaway: Routing decides which queue a bead lands in; readiness decides whether anyone can see it.

**WHAT** — Agents pull their work: each one asks the store for ready work routed to it, then claims one bead.

- Agents pull, nobody pushes
- Routing picks the queue
- Readiness picks the moment

**WHY** — Pulling means the sender never needs to know which session exists. Work waits safely until a worker is ready.

- Senders stay decoupled
- No lost hand-offs
- Scale workers freely

**HOW** — Sling stamps gc.routed_to on the bead. At startup an agent runs gc hook --claim, which claims one ready bead from its queue.

- Route: gc.routed_to metadata
- Ready: no open blockers
- gc hook --claim takes one bead
- Run it, close it, repeat

**See it — demo: Routing picks the queue; the agent pulls** (default demo city (bd + Dolt); uses Claude Code (tokens), slow parts become time-lapse cuts)

```
gc sling hello-factory/claude "List every file in this repo into files.txt"
gc bd show <bead> | grep -iE 'routed|status|OPEN'
gc prime | sed -n '1,12p'
gc bd show <bead>   # time-lapse until 'closed'
```

- Sling only stamps a route on the bead.
- gc.routed_to: that's the queue.
- The worker's loop: claim one ready bead, do it, repeat.
- Pulled, done, closed.

**Group it — picture:** Flow: Work created → Routed → Ready → Claimed (Routing decides which queue; readiness decides when).

**Say it simply:** A taxi rank: passengers queue at the right rank, and the next free taxi takes the next passenger.

- **atomic claim** — taking a bead in one step, so two agents can never grab the same one

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Routing and readiness** · Agents pull, nobody pushes · Routing picks the queue · why: Senders stay decoupled |
| 0:29–2:09 | See it | Demo: Routing picks the queue; the agent pulls. Sling only stamps a route on the bead. → gc.routed_to: that's the queue. → The worker's loop: claim one ready bead, do it, repeat. → Pulled, done, closed. |
| 2:09–2:31 | Group it | Route: gc.routed_to metadata → Ready: no open blockers → gc hook --claim takes one bead → Run it, close it, repeat (on screen: Flow: Work created → Routed → Ready → Claimed) |
| 2:31–2:43 | Name it | “Routing decides which queue a bead lands in; readiness decides whether anyone can see it.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** The generic worker prompt printed by gc prime: claim, show, close, repeat.

**Repository references:**

- [docs/tutorials/06-beads.md](https://github.com/gastownhall/gascity/blob/main/docs/tutorials/06-beads.md)
- [docs/tutorials/02-agents.md](https://github.com/gastownhall/gascity/blob/main/docs/tutorials/02-agents.md)

**Verify before Take 1:**

- [ ] Tutorial 06, 'How agents find work'.
- [ ] Tutorial 02: gc prime output.

### Day 14: Demo: A Tiny Work Graph by Hand

Friday 23 October 2026 · concept: **Beads in practice** · builds on: Day 13: The Pull Model: How Agents Find Work

> Takeaway: A formula simply creates this graph for you, and now you know exactly what it builds.

**WHAT** — Today we build a three-bead work graph by hand with bd and watch readiness change as beads close.

- Three beads
- One dependency
- One convoy

**WHY** — Doing it by hand once makes the factory's automatic behaviour obvious. A formula creates exactly this, only bigger.

- See readiness change
- Recap of week two
- Sets up formulas

**HOW** — Create three beads, add a blocks edge, group them in a convoy, close the blocker and watch the convoy's progress.

- bd create three times
- bd dep A --blocks B
- gc convoy create
- bd close A, then B is ready

**See it — demo: A tiny work graph by hand** (default demo city (bd + Dolt); no agent, fast)

```
bd create "Design the page"
bd create "Build the page"
bd dep <a> --blocks <b> && gc convoy create landing <a> <b>
bd close <a> >/dev/null && bd ready --limit 20 | grep <b>
gc convoy status <convoy>
```

- Design.
- Build: it should wait for design.
- One dependency, one convoy.
- Design closes; build becomes ready.
- The convoy shows the batch: 1 of 2.

**Group it — picture:** Code (shell), 7 lines (Week two in seven commands).

**Say it simply:** Laying out the ingredients and recipe steps by hand before letting the kitchen run them.

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Beads in practice** · Three beads · One dependency · why: See readiness change |
| 0:29–2:09 | See it | Demo: A tiny work graph by hand. Design. → Build: it should wait for design. → One dependency, one convoy. → Design closes; build becomes ready. → The convoy shows the batch: 1 of 2. |
| 2:09–2:31 | Group it | bd create three times → bd dep A --blocks B → gc convoy create → bd close A, then B is ready (on screen: Code (shell), 7 lines) |
| 2:31–2:43 | Name it | “A formula simply creates this graph for you, and now you know exactly what it builds.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** Run the seven commands in a scratch city (GC_BEADS=file is fine) and keep the convoy status output.

**Repository references:**

- [docs/tutorials/06-beads.md](https://github.com/gastownhall/gascity/blob/main/docs/tutorials/06-beads.md)
- [diagram: bead-lifecycle](https://github.com/gastownhall/gascity/blob/main/docs/diagrams/excalidraw-rendered/bead-lifecycle.svg)
- [diagram: convoy-tracks-membership](https://github.com/gastownhall/gascity/blob/main/docs/diagrams/excalidraw-rendered/convoy-tracks-membership.svg)

**Verify before Take 1:**

- [ ] Real bead IDs differ from mc-1, mc-2, mc-3: use the IDs bd prints.
- [ ] Tutorial 06: gc convoy create syntax.

## Module 3: Workers: Agents and Sessions

Define agents, run sessions and see how agents coordinate.

### Day 15: Agents: A Role Is a Prompt

Saturday 24 October 2026 · concept: **Agent** · builds on: Day 14: Demo: A Tiny Work Graph by Hand

> Takeaway: A reviewer is nothing more than the prompt you wrote for it.

**WHAT** — An agent is a configured worker: a name, a provider, a scope and a prompt template that defines its behaviour.

- An agents/<name>/ folder
- agent.toml = settings
- prompt.template.md = behaviour

**WHY** — Because a role is just a prompt you wrote, a new reviewer, planner or tester takes minutes. No plugin, no code.

- No code to write
- Versioned like any file
- As many roles as you need

**HOW** — gc agent add scaffolds the folder. agent.toml sets provider and scope; the prompt says how to work. gc prime shows the result.

- gc agent add --name reviewer
- agent.toml: dir and provider
- prompt.template.md: the role
- gc prime my-project/reviewer

**See it — demo: Create a reviewer in two files** (default demo city (bd + Dolt); no agent, fast)

```
gc agent add --name reviewer
cat agents/reviewer/agent.toml
gc prime hello-factory/reviewer | tail -4
```

- Scaffold the agent folder.
- Settings: which project, which harness.
- Behaviour: the prompt you wrote.

**Group it — picture:** Code (toml), 8 lines (A reviewer is two small files).

**Say it simply:** A job description: the same person becomes a reviewer or a planner depending on the description you hand over.

- **provider** — the coding-agent CLI that runs the agent, such as Claude Code or Codex
- **prompt template** — the starting instructions, filled in with details about the city

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Agent** · An agents/<name>/ folder · agent.toml = settings · why: No code to write |
| 0:29–2:09 | See it | Demo: Create a reviewer in two files. Scaffold the agent folder. → Settings: which project, which harness. → Behaviour: the prompt you wrote. |
| 2:09–2:31 | Group it | gc agent add --name reviewer → agent.toml: dir and provider → prompt.template.md: the role → gc prime my-project/reviewer (on screen: Code (toml), 8 lines) |
| 2:31–2:43 | Name it | “A reviewer is nothing more than the prompt you wrote for it.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** The reviewer agent folder from Tutorial 02.

**Repository references:**

- [docs/tutorials/02-agents.md](https://github.com/gastownhall/gascity/blob/main/docs/tutorials/02-agents.md)
- [docs/getting-started/how-gas-city-works.md](https://github.com/gastownhall/gascity/blob/main/docs/getting-started/how-gas-city-works.md)

**Verify before Take 1:**

- [ ] Tutorial 02: agent.toml with dir and provider.
- [ ] how-gas-city-works.md: the prompt template is the agent's entire behavioural spec.

### Day 16: Harnesses: One Fleet, Many Coding Agents

Sunday 25 October 2026 · concept: **Providers (harnesses)** · builds on: Day 15: Agents: A Role Is a Prompt

> Takeaway: In Gas City, a mixed fleet of coding agents is just configuration.

**WHAT** — Each agent picks its own harness, such as Claude Code, Codex or Gemini CLI, so a mixed fleet is just configuration.

- Sixteen built-in harnesses
- Chosen per agent
- Uses your existing logins

**WHY** — Different models are good at different jobs. Mixing them puts the right model on the right role without changing the workflow.

- Right model per role
- No lock-in
- Control cost and speed

**HOW** — Set provider in agent.toml and register it in city.toml. An agent has five axes: harness, model, upstream, transport, runtime.

- provider = "codex"
- [providers.codex] in city.toml
- option_defaults sets the model
- Five independent axes

**See it — demo: Swap the model with one line** (default demo city (bd + Dolt); uses Claude Code (tokens), slow parts become time-lapse cuts)

```
cat agents/reviewer/agent.toml
gc sling hello-factory/reviewer "Review hello.py and write review.md"
gc bd show <bead>   # time-lapse until 'closed'
head -8 review.md
```

- Same harness, a smaller model: one line.
- Same workflow, different engine.
- The fleet doesn't care which model serves it.
- The review.

**Group it — picture:** Layers: Harness / Model / Upstream / Transport / Runtime (Five axes you can tune per agent).

**Say it simply:** A band where each musician brings their own instrument, but everyone reads the same sheet music.

- **harness** — the coding-agent program an agent runs inside
- **upstream** — the service that actually serves the model

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Providers (harnesses)** · Sixteen built-in harnesses · Chosen per agent · why: Right model per role |
| 0:29–2:09 | See it | Demo: Swap the model with one line. Same harness, a smaller model: one line. → Same workflow, different engine. → The fleet doesn't care which model serves it. → The review. |
| 2:09–2:31 | Group it | provider = "codex" → [providers.codex] in city.toml → option_defaults sets the model → Five independent axes (on screen: Layers: Harness / Model / Upstream / Transport / Runtime) |
| 2:31–2:43 | Name it | “In Gas City, a mixed fleet of coding agents is just configuration.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** Two agent.toml snippets side by side: one Claude, one Codex.

**Repository references:**

- [docs/guides/configuring-an-agent.md](https://github.com/gastownhall/gascity/blob/main/docs/guides/configuring-an-agent.md)
- [docs/guides/harness-recipes.md](https://github.com/gastownhall/gascity/blob/main/docs/guides/harness-recipes.md)
- [docs/getting-started/faq.md](https://github.com/gastownhall/gascity/blob/main/docs/getting-started/faq.md)

**Verify before Take 1:**

- [ ] FAQ: sixteen built-in harnesses.
- [ ] configuring-an-agent.md: the five axes.
- [ ] Tutorial 02: register [providers.codex] with base = "builtin:codex".

### Day 17: Sessions: On-Demand vs. Always-On

Monday 26 October 2026 · concept: **Session** · builds on: Day 16: Harnesses: One Fleet, Many Coding Agents

> Takeaway: Agents are definitions; sessions are the live processes, and they're disposable by design.

**WHAT** — A session is a running agent: a live process with its own terminal, state and conversation history.

- Agent = definition
- Session = live process
- On-demand or always-on

**WHY** — On-demand sessions save cost: they start for work and stop when idle. Always-on sessions keep a coordinator ready to chat.

- Pay only while working
- A mayor that's always there
- Sessions are disposable

**HOW** — Slung work starts on-demand sessions. A named session with mode always stays alive. Watch with peek and logs; poke with nudge.

- gc session list
- gc session peek and logs
- gc session attach mayor
- gc session nudge mayor "..."

**See it — demo: Peek, nudge and read a live session** (default demo city (bd + Dolt); uses Claude Code (tokens), slow parts become time-lapse cuts)

```
gc session list
gc session peek mayor --lines 4
gc session nudge mayor "In one sentence, what is this city for?" && sleep 30
gc session logs mayor --tail 2
```

- The mayor is always on.
- Peek: a snapshot of its terminal.
- Nudge: type straight into it.
- Logs: the whole conversation.

**Group it — picture:** Side by side: On-demand vs. Always-on (Same primitive, two lifecycles).

**Say it simply:** Contractors who come in for a job, versus a receptionist who's always at the front desk.

- **named session** — a session with a stable name the city keeps track of
- **nudge** — typing a message straight into a running session

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Session** · Agent = definition · Session = live process · why: Pay only while working |
| 0:29–2:09 | See it | Demo: Peek, nudge and read a live session. The mayor is always on. → Peek: a snapshot of its terminal. → Nudge: type straight into it. → Logs: the whole conversation. |
| 2:09–2:31 | Group it | gc session list → gc session peek and logs → gc session attach mayor → gc session nudge mayor "..." (on screen: Side by side: On-demand vs. Always-on) |
| 2:31–2:43 | Name it | “Agents are definitions; sessions are the live processes, and they're disposable by design.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** gc session list output with a reviewer that is creating and a mayor that is active.

**Repository references:**

- [docs/tutorials/03-sessions.md](https://github.com/gastownhall/gascity/blob/main/docs/tutorials/03-sessions.md)

**Verify before Take 1:**

- [ ] Tutorial 03: the on-demand vs. always-on table.
- [ ] Tutorial 03: detach from tmux with Ctrl-b d.

### Day 18: Agents Talk Only Through the Store

Tuesday 27 October 2026 · concept: **Mail, nudge and sling** · builds on: Day 17: Sessions: On-Demand vs. Always-On

> Takeaway: No agent holds a reference to another, so any of them can crash, scale or swap.

**WHAT** — Agents never call each other. They coordinate through the bead store: mail for messages, sling for delegated work.

- No direct connections
- Mail = a message bead
- Sling = delegated work

**WHY** — With no references between agents, any of them can crash, restart, scale or switch providers without breaking the others.

- Senders name a destination
- Gas City routes it
- Hand-offs survive crashes

**HOW** — A human mails the mayor. The mayor plans and slings tasks to agents, and agents close their beads. Every hop goes through the store.

- gc mail send mayor ...
- The mayor slings to my-project/reviewer
- The reviewer closes the bead
- A nudge only wakes a live session

**See it — demo: Mail the mayor; watch the work move** (default demo city (bd + Dolt); uses Claude Code (tokens), slow parts become time-lapse cuts)

```
gc mail send mayor -s "Review needed" -m "Please have hello-factory/reviewer review hello.py and write review.md"
gc session nudge mayor "Check mail and act on it"
ls   # time-lapse until 'review.md'
head -6 review.md
```

- I only talk to the mayor, by mail.
- Nudge it to take a turn.
- Mayor slings to the reviewer; nobody holds a reference.
- Every hop went through the store.

**Group it — picture:** Gas City diagram `coordination-through-store` (Agents coordinate only through the store).

**Say it simply:** A shared office mailroom: nobody walks into anyone's office; everything goes through the pigeonholes.

- **mail** — a persistent message stored as a bead
- **nudge** — a one-off poke into a live terminal that isn't saved

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Mail, nudge and sling** · No direct connections · Mail = a message bead · why: Senders name a destination |
| 0:29–2:09 | See it | Demo: Mail the mayor; watch the work move. I only talk to the mayor, by mail. → Nudge it to take a turn. → Mayor slings to the reviewer; nobody holds a reference. → Every hop went through the store. |
| 2:09–2:31 | Group it | gc mail send mayor ... → The mayor slings to my-project/reviewer → The reviewer closes the bead → A nudge only wakes a live session (on screen: Gas City diagram `coordination-through-store`) |
| 2:31–2:43 | Name it | “No agent holds a reference to another, so any of them can crash, scale or swap.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** The mail vs. nudge table from Tutorial 04.

**Repository references:**

- [docs/tutorials/04-communication.md](https://github.com/gastownhall/gascity/blob/main/docs/tutorials/04-communication.md)
- [docs/guides/capabilities-for-coding-agent-users.md](https://github.com/gastownhall/gascity/blob/main/docs/guides/capabilities-for-coding-agent-users.md)
- [diagram: coordination-through-store](https://github.com/gastownhall/gascity/blob/main/docs/diagrams/excalidraw-rendered/coordination-through-store.svg)

**Verify before Take 1:**

- [ ] Tutorial 04 table: mail survives a crash, a nudge does not.

### Day 19: Hooks: Wiring a Coding Agent Into the City

Wednesday 28 October 2026 · concept: **Hooks** · builds on: Day 18: Agents Talk Only Through the Store

> Takeaway: Hooks turn a bare coding agent into a member of the city.

**WHAT** — Hooks connect a plain coding-agent process to Gas City, so it receives mail, picks up work and saves a hand-off by itself.

- A bare provider knows nothing
- Hooks fire at key moments
- gc init wires Claude for you

**WHY** — Without hooks you'd run gc mail check and gc prime by hand, on every agent, every turn.

- No manual polling
- Mail appears in context
- A hand-off before memory resets

**HOW** — gc init writes a managed .gc/settings.json for Claude. It runs Gas City commands at session start, before each turn and before compaction.

- .gc/settings.json for Claude
- Session start: surface pending work
- Each turn: deliver mail and nudges
- Before compaction: save a hand-off

**See it — demo: The hooks that wire Claude into the city** (default demo city (bd + Dolt); uses Claude Code (tokens), slow parts become time-lapse cuts)

```
jq -r '.hooks | keys[]' .gc/settings.json 2>/dev/null || head -20 .gc/settings.json
gc mail send mayor -s "Ping" -m "Hello from the hooks demo"
gc session nudge mayor "Anything new for you?" && sleep 30 && gc session peek mayor --lines 8
```

- gc init wrote these for Claude.
- Send mail; don't tell the mayor to check.
- The hook drops the mail into its context.

**Group it — picture:** Flow: Session start → Before each turn → Before compaction (Three moments where Gas City steps in).

**Say it simply:** Phone notifications: apps don't keep asking you; the phone taps them on the shoulder at the right moment.

- **context compaction** — when a coding agent summarises its conversation to free up memory

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Hooks** · A bare provider knows nothing · Hooks fire at key moments · why: No manual polling |
| 0:29–2:09 | See it | Demo: The hooks that wire Claude into the city. gc init wrote these for Claude. → Send mail; don't tell the mayor to check. → The hook drops the mail into its context. |
| 2:09–2:31 | Group it | .gc/settings.json for Claude → Session start: surface pending work → Each turn: deliver mail and nudges → Before compaction: save a hand-off (on screen: Flow: Session start → Before each turn → Before compaction) |
| 2:31–2:43 | Name it | “Hooks turn a bare coding agent into a member of the city.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** The install_agent_hooks line for a non-Claude provider.

**Repository references:**

- [docs/tutorials/04-communication.md](https://github.com/gastownhall/gascity/blob/main/docs/tutorials/04-communication.md)

**Verify before Take 1:**

- [ ] Tutorial 04: Claude is the only provider wired automatically.
- [ ] Tutorial 04: hooks fire at session start, before each turn and before compaction.

### Day 20: Pools: Scaling Workers to Demand

Thursday 29 October 2026 · concept: **Pool** · builds on: Day 19: Hooks: Wiring a Coding Agent Into the City

> Takeaway: A pool turns one agent definition into exactly as many workers as the work needs.

**WHAT** — A pool is one agent definition scaled into several identical workers that share a single queue.

- One definition, many sessions
- One shared queue
- Sized to demand

**WHY** — Ten ready tasks shouldn't wait on one worker, and zero tasks shouldn't keep ten sessions running.

- Parallel when busy
- Nothing running when idle
- Floors and caps you control

**HOW** — Each tick the orchestrator runs the agent's scale_check to measure demand, then sizes the pool between its floor and cap.

- scale_check measures demand
- min_active_sessions is the floor
- max_active_sessions is the cap
- Idle sessions retire

**See it — demo: One worker definition, several sessions** (default demo city (bd + Dolt); uses Claude Code (tokens), slow parts become time-lapse cuts)

```
cat agents/worker/agent.toml
for n in 1 2 3; do gc sling worker "Write the number $n into pool-$n.txt in ~/"; done
gc session list --template worker   # time-lapse until 'worker'
echo "open: $(gc beads list --status open | grep -c pool-) left"   # time-lapse until 'open: 0 left'
```

- A cap of three sessions.
- Three ready tasks at once.
- The pool scales up to the demand.
- And retires idle sessions when the queue is empty.

**Group it — picture:** Flow: Ready work → scale_check → Pool: min ... max sessions (loops back) (Demand in, sessions out).

**Say it simply:** Supermarket checkouts: open more lanes when the queue grows, close them when it's quiet.

- **scale_check** — a small command that reports how much new work is waiting
- **crew and polecats** — Gas Town names for persistent and transient workers: operating styles, not types

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Pool** · One definition, many sessions · One shared queue · why: Parallel when busy |
| 0:29–2:09 | See it | Demo: One worker definition, several sessions. A cap of three sessions. → Three ready tasks at once. → The pool scales up to the demand. → And retires idle sessions when the queue is empty. |
| 2:09–2:31 | Group it | scale_check measures demand → min_active_sessions is the floor → max_active_sessions is the cap → Idle sessions retire (on screen: Flow: Ready work → scale_check → Pool: min ... max sessions (loops back)) |
| 2:31–2:43 | Name it | “A pool turns one agent definition into exactly as many workers as the work needs.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** The pool line from gc status in Tutorial 01: 'scaled (min=0, max=2)'.

**Repository references:**

- [docs/getting-started/how-gas-city-works.md](https://github.com/gastownhall/gascity/blob/main/docs/getting-started/how-gas-city-works.md)
- [docs/reference/config.md](https://github.com/gastownhall/gascity/blob/main/docs/reference/config.md)
- [docs/getting-started/coming-from-gastown.md](https://github.com/gastownhall/gascity/blob/main/docs/getting-started/coming-from-gastown.md)
- [diagram: gastown-agents-by-scope](https://github.com/gastownhall/gascity/blob/main/docs/diagrams/excalidraw-rendered/gastown-agents-by-scope.svg)

**Verify before Take 1:**

- [ ] docs/reference/config.md: scale_check, min_active_sessions, max_active_sessions.
- [ ] coming-from-gastown.md: crew and polecats are operating modes, not types.

### Day 21: Demo: Build a Reviewer and Sling a Review

Friday 30 October 2026 · concept: **Agents in practice** · builds on: Day 20: Pools: Scaling Workers to Demand

> Takeaway: A role, a prompt and one sling: that's a new specialist on your factory floor.

**WHAT** — Today we define a reviewer agent, sling it a review and watch its session do the work.

- Define the role
- Sling the work
- Watch the session

**WHY** — This recap ties week three together: role, harness, session, pull model and coordination, in one small run.

- Week three in one run
- See the prompt land
- See the bead close

**HOW** — Scaffold the agent, write its prompt, sling a review, peek at the session and read the result.

- gc agent add --name reviewer
- Write prompt.template.md
- gc sling my-project/reviewer ...
- gc session peek, then read review.md

**See it — demo: Build a reviewer and sling a review** (default demo city (bd + Dolt); uses Claude Code (tokens), slow parts become time-lapse cuts)

```
gc agent add --name reviewer
gc sling hello-factory/reviewer "Review hello.py and write review.md with feedback"
gc session list --template hello-factory/reviewer   # time-lapse until 'reviewer'
gc bd show <bead>   # time-lapse until 'closed'
head -10 review.md
```

- A new specialist.
- Hand it a ticket.
- A session spins up for it.
- It claims, works, closes.
- The review, in the repo.

**Group it — picture:** Code (shell), 7 lines (Week three in one run).

**Say it simply:** Hiring a specialist, handing them a ticket and glancing through the window while they work.

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Agents in practice** · Define the role · Sling the work · why: Week three in one run |
| 0:29–2:09 | See it | Demo: Build a reviewer and sling a review. A new specialist. → Hand it a ticket. → A session spins up for it. → It claims, works, closes. → The review, in the repo. |
| 2:09–2:31 | Group it | gc agent add --name reviewer → Write prompt.template.md → gc sling my-project/reviewer ... → gc session peek, then read review.md (on screen: Code (shell), 7 lines) |
| 2:31–2:43 | Name it | “A role, a prompt and one sling: that's a new specialist on your factory floor.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** Record the terminal run beforehand, or show the transcript on the slide.

**Repository references:**

- [docs/tutorials/02-agents.md](https://github.com/gastownhall/gascity/blob/main/docs/tutorials/02-agents.md)
- [docs/tutorials/03-sessions.md](https://github.com/gastownhall/gascity/blob/main/docs/tutorials/03-sessions.md)
- [diagram: coordination-through-store](https://github.com/gastownhall/gascity/blob/main/docs/diagrams/excalidraw-rendered/coordination-through-store.svg)

**Verify before Take 1:**

- [ ] Tutorial 02: a custom agent has no default sling formula, so the bead is delivered directly.
- [ ] Tutorial 02: the 'suggest' permission mode blocks unattended writes; use a non-blocking mode for slung work.

## Module 4: Methods: Formulas

Write a method once and let the orchestrator run it as a graph.

### Day 22: Formulas: Write the Method Down Once

Saturday 31 October 2026 · concept: **Formula** · builds on: Day 21: Demo: Build a Reviewer and Sling a Review

> Takeaway: Write the method down once, and the orchestrator can run it again and again.

**WHAT** — A formula is a TOML file that records how a job gets done: its steps, their dependencies and its variables.

- A reusable method
- Steps plus needs
- Not the work itself

**WHY** — A method kept in a prompt is improvised every time. Written down, it's repeatable, reviewable and runs across many agents.

- Repeatable
- Reviewable like code
- Runs in parallel

**HOW** — Steps declare needs. Steps without needs run in parallel. Pancakes: dry and wet together, then combine, cook and serve.

- [[steps]] with an id and title
- needs = ["dry", "wet"]
- No needs means parallel
- A DAG: no cycles allowed

**See it — demo: Pancakes as a graph** (default demo city (bd + Dolt); no agent, fast)

```
grep -E '^id|^needs' formulas/pancakes.toml
gc formula show pancakes
```

- Steps and what each one needs.
- dry and wet run in parallel; the rest waits.

**Group it — picture:** Gas City diagram `pancakes-dag` (The pancakes formula as a graph).

**Say it simply:** A recipe card: anyone can cook from it, and two people can mix dry and wet ingredients at the same time.

- **TOML** — a simple, readable config file format
- **DAG** — a graph of steps with arrows and no loops

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Formula** · A reusable method · Steps plus needs · why: Repeatable |
| 0:29–2:09 | See it | Demo: Pancakes as a graph. Steps and what each one needs. → dry and wet run in parallel; the rest waits. |
| 2:09–2:31 | Group it | [[steps]] with an id and title → needs = ["dry", "wet"] → No needs means parallel → A DAG: no cycles allowed (on screen: Gas City diagram `pancakes-dag`) |
| 2:31–2:43 | Name it | “Write the method down once, and the orchestrator can run it again and again.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** formulas/pancakes.toml from Tutorial 05.

**Repository references:**

- [docs/tutorials/05-formulas.md](https://github.com/gastownhall/gascity/blob/main/docs/tutorials/05-formulas.md)
- [docs/guides/understanding-formulas.md](https://github.com/gastownhall/gascity/blob/main/docs/guides/understanding-formulas.md)
- [diagram: pancakes-dag](https://github.com/gastownhall/gascity/blob/main/docs/diagrams/excalidraw-rendered/pancakes-dag.svg)

**Verify before Take 1:**

- [ ] Tutorial 05: a formula isn't the work itself (that's a bead); it's the reusable method.
- [ ] Tutorial 05: the v2 compiler rejects cycles at compile time.

### Day 23: From TOML to Beads: Cook vs. Sling

Sunday 01 November 2026 · concept: **Applying a formula** · builds on: Day 22: Formulas: Write the Method Down Once

> Takeaway: A formula is the method; applying it prints the work as beads that outlive everything.

**WHAT** — Applying a formula compiles it into a recipe, then turns every step into a bead in the store.

- Compile into a recipe
- Instantiate as beads
- The work outlives the file

**WHY** — Once the steps are beads, the run no longer depends on the file or on any session. A crash can't erase it.

- Independent of the file
- Independent of sessions
- Inspect before you run

**HOW** — gc formula cook creates the beads without routing. gc sling with --formula creates and routes. A finalize step is added.

- gc formula show: preview
- gc formula cook: create only
- gc sling mayor pancakes --formula
- plus a workflow-finalize step

**See it — demo: Cook it, then sling it** (default demo city (bd + Dolt); uses Claude Code (tokens), slow parts become time-lapse cuts)

```
gc formula cook pancakes
bd show <root> | head -6
gc sling worker <root>
bd show <root>   # time-lapse until 'closed'
```

- Cook: the method becomes seven beads.
- The root waits on finalize.
- Sling routes the root to a worker.
- The orchestrator drives every step to done.

**Group it — picture:** Gas City diagram `formula-apply-pipeline` (File, recipe, beads).

**Say it simply:** Printing tickets from a recipe: the recipe stays in the book, and the printed tickets go on the rail.

- **materialize** — turn a plan into real records in the store
- **control step** — a step the orchestrator completes itself; no agent works on it

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Applying a formula** · Compile into a recipe · Instantiate as beads · why: Independent of the file |
| 0:29–2:09 | See it | Demo: Cook it, then sling it. Cook: the method becomes seven beads. → The root waits on finalize. → Sling routes the root to a worker. → The orchestrator drives every step to done. |
| 2:09–2:31 | Group it | gc formula show: preview → gc formula cook: create only → gc sling mayor pancakes --formula → plus a workflow-finalize step (on screen: Gas City diagram `formula-apply-pipeline`) |
| 2:31–2:43 | Name it | “A formula is the method; applying it prints the work as beads that outlive everything.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** The gc formula cook pancakes output: a root and 'Created: 7'.

**Repository references:**

- [docs/tutorials/05-formulas.md](https://github.com/gastownhall/gascity/blob/main/docs/tutorials/05-formulas.md)
- [docs/guides/understanding-formulas.md](https://github.com/gastownhall/gascity/blob/main/docs/guides/understanding-formulas.md)
- [diagram: formula-apply-pipeline](https://github.com/gastownhall/gascity/blob/main/docs/diagrams/excalidraw-rendered/formula-apply-pipeline.svg)

**Verify before Take 1:**

- [ ] Tutorial 05: 'Created: 7' is the root, five steps and the finalize step.
- [ ] Tutorial 05: sling doesn't prompt the agent by default; --nudge does.

### Day 24: Variables: One Method, Many Runs

Monday 02 November 2026 · concept: **Formula variables** · builds on: Day 23: From TOML to Beads: Cook vs. Sling

> Takeaway: Variables turn one written method into a method for every situation.

**WHAT** — Variables make a formula reusable: declare them, use {{name}} in the steps and pass values when you cook or sling.

- A [vars] section
- {{name}} placeholders
- --var name=value

**WHY** — The same review or release method should work for any branch, feature or priority, without copying the file.

- No copy-paste formulas
- Defaults and required fields
- Validated inputs

**HOW** — Variables stay placeholders through compilation and are filled in only when beads are created. Fields validate the input.

- vars.title: required
- vars.branch: default = "main"
- vars.priority: enum
- gc formula show --var previews

**See it — demo: One method, two different runs** (default demo city (bd + Dolt); no agent, fast)

```
sed -n '4,13p' formulas/feature-work.toml
gc formula show feature-work --var title="Auth overhaul"
gc formula show feature-work --var title="Billing export" --var priority=high
```

- Declared once: a required title, defaults for the rest.
- Run one.
- Run two, same file.

**Group it — picture:** Code (toml), 9 lines (gc formula cook feature-work --var title="Auth overhaul").

**Say it simply:** A form letter: the same letter with a different name and date each time.

- **late binding** — values are filled in at the last moment, when the work is created

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Formula variables** · A [vars] section · {{name}} placeholders · why: No copy-paste formulas |
| 0:29–2:09 | See it | Demo: One method, two different runs. Declared once: a required title, defaults for the rest. → Run one. → Run two, same file. |
| 2:09–2:31 | Group it | vars.title: required → vars.branch: default = "main" → vars.priority: enum → gc formula show --var previews (on screen: Code (toml), 9 lines) |
| 2:31–2:43 | Name it | “Variables turn one written method into a method for every situation.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** The feature-work formula with title, branch and priority.

**Repository references:**

- [docs/tutorials/05-formulas.md](https://github.com/gastownhall/gascity/blob/main/docs/tutorials/05-formulas.md)

**Verify before Take 1:**

- [ ] Tutorial 05 variable fields: description, required, default, enum, pattern.
- [ ] Tutorial 05: a variable without a default that isn't required stays as the literal {{name}}.

### Day 25: v1 vs. v2 Formulas: Who Is the Engine?

Tuesday 03 November 2026 · concept: **Compiler contracts** · builds on: Day 24: Variables: One Method, Many Runs

> Takeaway: In v2 the orchestrator, not a single agent, is the engine.

**WHAT** — Formulas have two contracts. In v1 the agent you sling to is the engine; in v2 the orchestrator is the engine.

- v1: one agent runs it all
- v2: the orchestrator runs a graph
- Choose v2 for new work

**WHY** — Only v2 makes each step its own routable bead, so steps can go to different agents, run in parallel and retry on their own.

- Routing per step
- Parallel fan-out
- Checks, retries, drain

**HOW** — Opt in with a [requires] table. v1 builds a parent-child molecule; v2 builds a flat graph of blocking edges with a finalize step.

- formula_compiler = ">=2.0.0"
- v1: a molecule tree
- v2: a flat graph plus finalize
- Graph-only: check, retry, drain

**See it — demo: Same steps, two engines** (default demo city (bd + Dolt); no agent, fast)

```
diff formulas/plan-v1.toml formulas/plan-v2.toml
gc formula show plan-v1
gc formula show plan-v2
```

- The only difference: one [requires] table.
- v1: one agent will run the whole thing.
- v2: separate routable steps plus a finalize step.

**Group it — picture:** Gas City diagram `formula-v1-vs-v2` (Two contracts, two engines).

**Say it simply:** v1 is one chef cooking the whole menu. v2 is a head chef sending each dish to the right station.

- **molecule** — v1's container bead with its steps as children
- **compiler contract** — the set of rules a formula is compiled under

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Compiler contracts** · v1: one agent runs it all · v2: the orchestrator runs a graph · why: Routing per step |
| 0:29–2:09 | See it | Demo: Same steps, two engines. The only difference: one [requires] table. → v1: one agent will run the whole thing. → v2: separate routable steps plus a finalize step. |
| 2:09–2:31 | Group it | formula_compiler = ">=2.0.0" → v1: a molecule tree → v2: a flat graph plus finalize → Graph-only: check, retry, drain (on screen: Gas City diagram `formula-v1-vs-v2`) |
| 2:31–2:43 | Name it | “In v2 the orchestrator, not a single agent, is the engine.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** The v1 vs. v2 comparison table from Understanding Formulas.

**Repository references:**

- [docs/guides/understanding-formulas.md](https://github.com/gastownhall/gascity/blob/main/docs/guides/understanding-formulas.md)
- [docs/reference/specs/formula-spec-v2.md](https://github.com/gastownhall/gascity/blob/main/docs/reference/specs/formula-spec-v2.md)
- [diagram: formula-v1-vs-v2](https://github.com/gastownhall/gascity/blob/main/docs/diagrams/excalidraw-rendered/formula-v1-vs-v2.svg)

**Verify before Take 1:**

- [ ] understanding-formulas.md contract table: engine, steps, control flow, routing, shape.
- [ ] understanding-formulas.md: 'For new work, choose v2.'

### Day 26: Check and Retry: Work That Verifies Itself

Wednesday 04 November 2026 · concept: **check and retry** · builds on: Day 25: v1 vs. v2 Formulas: Who Is the Engine?

> Takeaway: With check, done means verified, not just claimed.

**WHAT** — check reruns a step until a script says it passed. retry re-dispatches a step that failed for a temporary reason.

- check: your script decides
- retry: just try again
- Both run while the workflow runs

**WHY** — An agent saying 'done' isn't proof. A check makes done mean verified, and retry absorbs flaky failures without a human.

- Done means verified
- Flaky failures heal themselves
- Budgets stop runaway loops

**HOW** — A check script runs after each attempt: exit 0 means done, anything else starts another attempt, up to max_attempts.

- [steps.check] with a script
- exit 0 means pass
- max_attempts is the budget
- exit 75: re-check, no attempt spent

**See it — demo: A step that is done only when a script agrees** (default demo city (bd + Dolt); uses Claude Code (tokens), slow parts become time-lapse cuts)

```
cat scripts/verify.sh
gc formula show checked
gc sling worker checked --formula
bd show <root>   # time-lapse until 'closed'
cat done.txt
```

- The rule: done.txt must say verified.
- The compiler turns one step into a check loop.
- Run it.
- Closed only after verify.sh exits 0.
- Verified, not just claimed.

**Group it — picture:** Flow: Agent attempt → verify.sh → Done (loops back) (The step is done when the script says so).

**Say it simply:** A driving test: you're licensed when the examiner signs off, not when you say you can drive.

- **exit code** — the number a script returns; 0 means success

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **check and retry** · check: your script decides · retry: just try again · why: Done means verified |
| 0:29–2:09 | See it | Demo: A step that is done only when a script agrees. The rule: done.txt must say verified. → The compiler turns one step into a check loop. → Run it. → Closed only after verify.sh exits 0. → Verified, not just claimed. |
| 2:09–2:31 | Group it | [steps.check] with a script → exit 0 means pass → max_attempts is the budget → exit 75: re-check, no attempt spent (on screen: Flow: Agent attempt → verify.sh → Done (loops back)) |
| 2:31–2:43 | Name it | “With check, done means verified, not just claimed.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** The 'checked' formula with scripts/verify.sh from Tutorial 05.

**Repository references:**

- [docs/tutorials/05-formulas.md](https://github.com/gastownhall/gascity/blob/main/docs/tutorials/05-formulas.md)
- [docs/guides/understanding-formulas.md](https://github.com/gastownhall/gascity/blob/main/docs/guides/understanding-formulas.md)

**Verify before Take 1:**

- [ ] Tutorial 05: check is v2-only.
- [ ] Tutorial 05: exit code 75 re-runs the check without spending an attempt.
- [ ] understanding-formulas.md: check and retry are mutually exclusive on the same step.

### Day 27: Drain: Fan Out Over a Convoy

Thursday 05 November 2026 · concept: **drain** · builds on: Day 26: Check and Retry: Work That Verifies Itself

> Takeaway: Drain turns a convoy of any size into parallel, isolated runs.

**WHAT** — drain runs one small workflow per member of a convoy, all in parallel, for a set of work found only at runtime.

- One run per convoy member
- All in parallel
- The set is known only at runtime

**WHY** — You rarely know in advance how many tasks a plan will produce. Drain scales the fan-out to whatever is in the convoy now.

- No fixed count
- Real parallelism
- Each item isolated

**HOW** — A drain step names an item formula. The orchestrator splits the convoy into one-member units and runs the item formula for each.

- [steps.drain] formula = "do-work"
- context = separate: own worktree
- member_access = exclusive
- Sling a convoy at it

**See it — demo: Fan a convoy out into parallel runs** (default demo city (bd + Dolt); uses Claude Code (tokens), slow parts become time-lapse cuts)

```
for f in add sub mul; do bd create "Write $f.py with a $f(a, b) function"; done
gc convoy create math-funcs $(bd list --flat | grep -E 'Write (add|sub|mul).py' | grep -oE '[a-z0-9]+-[a-z0-9]+' | head -3 | tr '\n' ' ')
gc sling gc.run-operator <convoy> --on build-from-convoy
gc session list   # time-lapse until 'implementation'
gc convoy status <convoy>   # time-lapse until 'closed'
```

- Three items, discovered at runtime.
- One convoy.
- Drain it: one run per member.
- Several sessions working at once, each in its own worktree.
- All three done.

**Group it — picture:** Gas City diagram `formula-drain-fanout` (drain fans a convoy out into parallel runs).

**Say it simply:** A teacher handing each student one worksheet from the pile, however many students showed up today.

- **fan-out** — splitting one job into many parallel jobs
- **worktree** — a separate checkout of the same Git repo, for parallel work

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **drain** · One run per convoy member · All in parallel · why: No fixed count |
| 0:29–2:09 | See it | Demo: Fan a convoy out into parallel runs. Three items, discovered at runtime. → One convoy. → Drain it: one run per member. → Several sessions working at once, each in its own worktree. → All three done. |
| 2:09–2:31 | Group it | [steps.drain] formula = "do-work" → context = separate: own worktree → member_access = exclusive → Sling a convoy at it (on screen: Gas City diagram `formula-drain-fanout`) |
| 2:31–2:43 | Name it | “Drain turns a convoy of any size into parallel, isolated runs.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** The build-from-convoy drain step from Understanding Formulas.

**Repository references:**

- [docs/guides/understanding-formulas.md](https://github.com/gastownhall/gascity/blob/main/docs/guides/understanding-formulas.md)
- [engdocs/drain-fanout.md](https://github.com/gastownhall/gascity/blob/main/engdocs/drain-fanout.md)
- [diagram: formula-drain-fanout](https://github.com/gastownhall/gascity/blob/main/docs/diagrams/excalidraw-rendered/formula-drain-fanout.svg)

**Verify before Take 1:**

- [ ] understanding-formulas.md: drain is the canonical v2 fan-out.
- [ ] understanding-formulas.md: context = separate gives every unit its own git worktree.

### Day 28: Demo: Write and Run the Pancakes Formula

Friday 06 November 2026 · concept: **Formulas in practice** · builds on: Day 27: Drain: Fan Out Over a Convoy

> Takeaway: Write the method, preview it, run it, and the orchestrator drives it to done.

**WHAT** — Today we write the pancakes formula, preview it, cook it into beads and sling it to an agent.

- Write it
- Preview it
- Run it

**WHY** — This recap connects week four: method, compilation, beads and the orchestrator driving the graph to done.

- Week four in one run
- See steps run in parallel
- See finalize close the root

**HOW** — Write formulas/pancakes.toml, preview it with gc formula show, then cook it, sling the root and watch the beads close.

- formulas/pancakes.toml
- gc formula show pancakes
- gc formula cook pancakes
- gc sling worker <root-id>

**See it — demo: Write the formula, run it, watch it finish** (default demo city (bd + Dolt); uses Claude Code (tokens), slow parts become time-lapse cuts)

```
gc formula show pancakes
gc sling worker pancakes --formula
bd show <root>   # time-lapse until 'closed'
cat ~/pancakes.md 2>/dev/null || cat pancakes.md 2>/dev/null || bd list --all --flat | grep -iE 'mix|combine|cook|serve' | head -6
```

- Six steps, including finalize.
- One command starts the whole graph.
- Dry and wet in parallel, then the chain.
- Every step, done in order.

**Group it — picture:** Code (toml), 10 lines (gc formula show pancakes lists 6 steps, including finalize).

**Say it simply:** Cooking from the recipe card you wrote last week, with two helpers mixing in parallel.

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Formulas in practice** · Write it · Preview it · why: Week four in one run |
| 0:29–2:09 | See it | Demo: Write the formula, run it, watch it finish. Six steps, including finalize. → One command starts the whole graph. → Dry and wet in parallel, then the chain. → Every step, done in order. |
| 2:09–2:31 | Group it | formulas/pancakes.toml → gc formula show pancakes → gc formula cook pancakes → gc sling worker <root-id> (on screen: Code (toml), 10 lines) |
| 2:31–2:43 | Name it | “Write the method, preview it, run it, and the orchestrator drives it to done.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** A working pancakes.toml in your scratch city.

**Repository references:**

- [docs/tutorials/05-formulas.md](https://github.com/gastownhall/gascity/blob/main/docs/tutorials/05-formulas.md)
- [diagram: pancakes-dag](https://github.com/gastownhall/gascity/blob/main/docs/diagrams/excalidraw-rendered/pancakes-dag.svg)
- [diagram: formula-apply-pipeline](https://github.com/gastownhall/gascity/blob/main/docs/diagrams/excalidraw-rendered/formula-apply-pipeline.svg)

**Verify before Take 1:**

- [ ] Tutorial 05: gc formula show prints 6 steps, including workflow-finalize.

## Module 5: Automation and Operations

Make the factory start, supervise and observe its own work.

### Day 29: Orders: When, Not How

Saturday 07 November 2026 · concept: **Order** · builds on: Day 28: Demo: Write and Run the Pancakes Formula

> Takeaway: Formulas say how; orders say when, and then nobody has to press go.

**WHAT** — An order pairs a trigger with an action, so a formula or script runs on a schedule, a condition or an event.

- A trigger plus an action
- A formula or a script
- No human dispatch

**WHY** — Formulas say how; orders say when. Together, the factory starts its own work: nightly checks, updates, release notes.

- Automation without babysitting
- Schedules and events
- Drop in a file, no restart

**HOW** — Put a TOML file in orders/. Triggers: cooldown, cron, condition, event, manual. Cooldown drifts; cron hits fixed clock times.

- orders/pancakes-check.toml
- cooldown, cron, condition, event, manual
- pool = where the work goes
- gc order list, check, run

**See it — demo: An order that fires by itself** (default demo city (bd + Dolt); no agent, fast)

```
cat orders/pancakes-check.toml
gc order list | head -8
gc order check | head -8
gc order run pancakes-check
gc order history | head -5
```

- When, not how: a trigger plus a formula.
- The orchestrator sees it on its next scan.
- Is it due?
- Or fire it by hand to test.
- Every firing leaves a record.

**Group it — picture:** Gas City diagram `cooldown-vs-cron` (Cooldown drifts; cron keeps clock time).

**Say it simply:** A thermostat: you set the rule once, and it turns the heating on by itself.

- **cooldown** — wait a fixed interval after the last run
- **cron** — run at fixed clock times, such as 3 a.m. every day

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Order** · A trigger plus an action · A formula or a script · why: Automation without babysitting |
| 0:29–2:09 | See it | Demo: An order that fires by itself. When, not how: a trigger plus a formula. → The orchestrator sees it on its next scan. → Is it due? → Or fire it by hand to test. → Every firing leaves a record. |
| 2:09–2:31 | Group it | orders/pancakes-check.toml → cooldown, cron, condition, event, manual → pool = where the work goes → gc order list, check, run (on screen: Gas City diagram `cooldown-vs-cron`) |
| 2:31–2:43 | Name it | “Formulas say how; orders say when, and then nobody has to press go.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** orders/pancakes-check.toml: cooldown, 5m, pool worker.

**Repository references:**

- [docs/tutorials/07-orders.md](https://github.com/gastownhall/gascity/blob/main/docs/tutorials/07-orders.md)
- [diagram: cooldown-vs-cron](https://github.com/gastownhall/gascity/blob/main/docs/diagrams/excalidraw-rendered/cooldown-vs-cron.svg)

**Verify before Take 1:**

- [ ] Tutorial 07: the orchestrator ticks every 30 seconds.
- [ ] Tutorial 07: trigger types table.

### Day 30: Exec Orders: Automation Without an LLM

Sunday 08 November 2026 · concept: **Exec order** · builds on: Day 29: Orders: When, Not How

> Takeaway: Use agents for judgment and scripts for chores.

**WHAT** — An exec order runs a shell script on the orchestrator: no agent, no model, no work beads.

- Just a script
- No tokens spent
- For mechanical jobs

**WHY** — Pruning branches or checking disk space needs no intelligence. A script is cheaper, faster and more predictable.

- No model cost
- Predictable
- The right tool for chores

**HOW** — Set exec to a script instead of formula. Exec orders take no pool, get ORDER_DIR in their environment and time out after 300 seconds.

- exec = "scripts/prune-merged.sh"
- No pool
- [order.env] for settings
- Default timeout: 300 s

**See it — demo: A chore with no model at all** (default demo city (bd + Dolt); no agent, fast)

```
cat orders/disk-check.toml scripts/disk-check.sh
gc order show disk-check
gc order run disk-check
```

- exec, not formula: a plain script.
- No pool: it runs on the orchestrator.
- No agent, no tokens, done in a second.

**Group it — picture:** Side by side: Formula order vs. Exec order (Every order has a formula or an exec, never both).

**Say it simply:** You don't hire a consultant to take out the bins; you set a reminder.

- **exec** — run a program directly

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Exec order** · Just a script · No tokens spent · why: No model cost |
| 0:29–2:09 | See it | Demo: A chore with no model at all. exec, not formula: a plain script. → No pool: it runs on the orchestrator. → No agent, no tokens, done in a second. |
| 2:09–2:31 | Group it | exec = "scripts/prune-merged.sh" → No pool → [order.env] for settings → Default timeout: 300 s (on screen: Side by side: Formula order vs. Exec order) |
| 2:31–2:43 | Name it | “Use agents for judgment and scripts for chores.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** The prune-merged exec order snippet from Tutorial 07.

**Repository references:**

- [docs/tutorials/07-orders.md](https://github.com/gastownhall/gascity/blob/main/docs/tutorials/07-orders.md)
- [docs/getting-started/coming-from-gastown.md](https://github.com/gastownhall/gascity/blob/main/docs/getting-started/coming-from-gastown.md)

**Verify before Take 1:**

- [ ] Tutorial 07: exec orders can't have a pool.
- [ ] Tutorial 07: default timeouts are 30 s for formula orders and 300 s for exec orders.

### Day 31: Health Patrol: Let It Crash

Monday 09 November 2026 · concept: **Health patrol** · builds on: Day 30: Exec Orders: Automation Without an LLM

> Takeaway: Gas City doesn't prevent crashes; it makes them cheap.

**WHAT** — Health patrol is the orchestrator's supervision loop: it keeps running sessions in line with your config and restarts failures.

- Compare want with have
- Restart, within limits
- Modelled on Erlang/OTP

**WHY** — Agents will crash. Rather than prevent every crash, Gas City makes crashes cheap: the work persists and a fresh session resumes it.

- Crashes are expected
- Work persists in beads
- Crash loops get quarantined

**HOW** — Each tick compares what config wants with what runs: start missing agents, stop orphans, restart drifted ones.

- Want (config) vs. have (running)
- Start, stop, restart
- Config drift means restart
- Too many restarts: quarantine

**See it — demo: Kill the mayor; patrol brings it back** (default demo city (bd + Dolt); uses Claude Code (tokens), slow parts become time-lapse cuts)

```
gc session list | grep -E 'ID|mayor'
gc session kill mayor
gc session list | grep mayor   # time-lapse until 'active'
```

- The mayor is declared always-on.
- Now I kill it.
- Want versus have: the next tick restarts it.

**Group it — picture:** Flow: Config: want → Running: have → Fix the difference (loops back) (Reconciliation, the Erlang/OTP way).

**Say it simply:** A lifeguard doesn't stop people swimming; they watch and pull out anyone in trouble.

- **reconcile** — make what's running match what the config says
- **quarantine** — stop restarting an agent that keeps crashing, for a while

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Health patrol** · Compare want with have · Restart, within limits · why: Crashes are expected |
| 0:29–2:09 | See it | Demo: Kill the mayor; patrol brings it back. The mayor is declared always-on. → Now I kill it. → Want versus have: the next tick restarts it. |
| 2:09–2:31 | Group it | Want (config) vs. have (running) → Start, stop, restart → Config drift means restart → Too many restarts: quarantine (on screen: Flow: Config: want → Running: have → Fix the difference (loops back)) |
| 2:31–2:43 | Name it | “Gas City doesn't prevent crashes; it makes them cheap.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** The three reconciliation rules: start missing, stop orphans, restart drifted.

**Repository references:**

- [engdocs/architecture/health-patrol.md](https://github.com/gastownhall/gascity/blob/main/engdocs/architecture/health-patrol.md)
- [engdocs/architecture/controller.md](https://github.com/gastownhall/gascity/blob/main/engdocs/architecture/controller.md)

**Verify before Take 1:**

- [ ] health-patrol.md: Erlang/OTP supervision and 'let it crash'.
- [ ] health-patrol.md: crash loop quarantine is in memory only.

### Day 32: Events: Watching the Fleet

Tuesday 10 November 2026 · concept: **Event** · builds on: Day 31: Health Patrol: Let It Crash

> Takeaway: Events let humans watch the factory, and let the factory react to itself.

**WHAT** — An event is an unchangeable record fired when something happens: a bead closes, a session crashes, an order fires.

- Fired, not polled
- Append-only and numbered
- Humans and agents watch

**WHY** — You can't steer a fleet you can't see. Events let you and other agents watch everything, and even trigger new work.

- See the whole fleet
- Replay from any point
- Events can trigger orders

**HOW** — Each event has a sequence number, so watchers resume where they stopped. Event-triggered orders read the same stream.

- bead.created, bead.closed
- session.woke, session.crashed
- gc events --follow
- trigger = event closes the loop

**See it — demo: Watch the event stream while work happens** (default demo city (bd + Dolt); uses Claude Code (tokens), slow parts become time-lapse cuts)

```
gc events --seq
gc sling hello-factory/claude "Add a one-line comment at the top of hello.py"
gc bd show <bead>   # time-lapse until 'closed'
gc events --since 30m | grep -oE '"type":"[a-z._]+"' | sort | uniq -c | sort -rn | head -8
```

- Every event has a number: resume from anywhere.
- Make something happen.
- Work runs.
- And the stream told everyone what happened.

**Group it — picture:** Flow: Activity → Event bus → Watchers (You, agents and orders all read the same stream).

**Say it simply:** A departures board: nobody calls you; the board updates and you react.

- **sequence number** — an always-increasing counter, so you can resume where you stopped

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Event** · Fired, not polled · Append-only and numbered · why: See the whole fleet |
| 0:29–2:09 | See it | Demo: Watch the event stream while work happens. Every event has a number: resume from anywhere. → Make something happen. → Work runs. → And the stream told everyone what happened. |
| 2:09–2:31 | Group it | bead.created, bead.closed → session.woke, session.crashed → gc events --follow → trigger = event closes the loop (on screen: Flow: Activity → Event bus → Watchers) |
| 2:31–2:43 | Name it | “Events let humans watch the factory, and let the factory react to itself.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** A short gc events --follow capture, or the dashboard.

**Repository references:**

- [docs/getting-started/how-gas-city-works.md](https://github.com/gastownhall/gascity/blob/main/docs/getting-started/how-gas-city-works.md)
- [docs/reference/events.md](https://github.com/gastownhall/gascity/blob/main/docs/reference/events.md)
- [docs/getting-started/dashboard.md](https://github.com/gastownhall/gascity/blob/main/docs/getting-started/dashboard.md)

**Verify before Take 1:**

- [ ] how-gas-city-works.md: event names such as bead.created, session.crashed, order.fired.
- [ ] dashboard.md: gc dashboard opens the supervisor's dashboard.

## Module 6: Composition: Packs

Package, share and assemble the whole factory.

### Day 33: Packs: What Configures the Factory

Wednesday 11 November 2026 · concept: **Pack** · builds on: Day 32: Events: Watching the Fleet

> Takeaway: A pack turns how your team works into versioned, shareable files.

**WHAT** — A pack is a directory with a pack.toml that declares agents, formulas and orders. Your city is itself a pack.

- pack.toml plus folders
- Agents, formulas, orders
- City = your local pack

**WHY** — Coordination that lives in chat and in people's heads leaks. A pack turns it into versioned files you can review and share.

- A versioned method
- Reviewable like code
- Shareable across teams

**HOW** — Everything sorts into three layers: the portable pack, deployment choices in city.toml, and machine-local state in .gc/.

- Layer 1: pack.toml and its folders
- Layer 2: city.toml
- Layer 3: .gc/, never shared
- Start small; move what you repeat

**See it — demo: Make a tiny pack** (default demo city (bd + Dolt); no agent, fast)

```
find packs/review-pack -type f | sort
cat packs/review-pack/pack.toml
sed -n '1,12p' pack.toml
```

- A pack is just a folder.
- pack.toml names it.
- And the city itself is a pack too.

**Group it — picture:** Gas City diagram `hand-rolled-to-city` (From hand-rolled to a city: three layers).

**Say it simply:** A franchise manual: recipes and job roles are the same in every branch, and each branch picks its own address.

- **site binding** — machine-specific settings, such as where a repo lives on this laptop

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Pack** · pack.toml plus folders · Agents, formulas, orders · why: A versioned method |
| 0:29–2:09 | See it | Demo: Make a tiny pack. A pack is just a folder. → pack.toml names it. → And the city itself is a pack too. |
| 2:09–2:31 | Group it | Layer 1: pack.toml and its folders → Layer 2: city.toml → Layer 3: .gc/, never shared → Start small; move what you repeat (on screen: Gas City diagram `hand-rolled-to-city`) |
| 2:31–2:43 | Name it | “A pack turns how your team works into versioned, shareable files.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** The three-layer table from the multi-agent engineering environment guide.

**Repository references:**

- [docs/guides/understanding-packs.md](https://github.com/gastownhall/gascity/blob/main/docs/guides/understanding-packs.md)
- [docs/guides/multi-agent-engineering-environment.md](https://github.com/gastownhall/gascity/blob/main/docs/guides/multi-agent-engineering-environment.md)
- [diagram: hand-rolled-to-city](https://github.com/gastownhall/gascity/blob/main/docs/diagrams/excalidraw-rendered/hand-rolled-to-city.svg)
- [diagram: pack-loading](https://github.com/gastownhall/gascity/blob/main/docs/diagrams/excalidraw-rendered/pack-loading.svg)

**Verify before Take 1:**

- [ ] multi-agent-engineering-environment.md: the three layers table.
- [ ] understanding-packs.md: a pack with an unknown schema is rejected whole.

### Day 34: Imports: Reuse Without Copying

Thursday 12 November 2026 · concept: **Pack imports** · builds on: Day 33: Packs: What Configures the Factory

> Takeaway: Import packs, pin versions, patch the differences, and never fork.

**WHAT** — An import pulls a shared pack into your city, so its agents, formulas and orders work as if you'd written them.

- [imports.<binding>]
- A pinned source and version
- Names get qualified

**WHY** — Teams shouldn't fork a pack to change one setting. Imports plus patches reuse a pack and override only what differs.

- No forks
- Upgrade by moving a pin
- Patch a single field

**HOW** — The binding qualifies names: [imports.review] gives review.reviewer, or checkout-service/review.reviewer for a rig import.

- [imports.review] source = ...
- City import: review.reviewer
- Rig import: rig/review.reviewer
- [[patches.agent]] to tweak

**See it — demo: Import the pack; the name gets qualified** (default demo city (bd + Dolt); no agent, fast)

```
grep -A1 'imports.review' pack.toml
gc agent list | grep -i review
gc prime review.reviewer | tail -3
```

- One import, bound as review.
- The binding qualifies the name: review.reviewer.
- Reused, not copied.

**Group it — picture:** Gas City diagram `import-binding-namespace` (The binding qualifies the name; the rig adds a prefix).

**Say it simply:** Adding a library to a project: you use it by name and pin the version you trust.

- **binding** — the local name you give an imported pack
- **patch** — a small change applied to something that already exists

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **Pack imports** · [imports.<binding>] · A pinned source and version · why: No forks |
| 0:29–2:09 | See it | Demo: Import the pack; the name gets qualified. One import, bound as review. → The binding qualifies the name: review.reviewer. → Reused, not copied. |
| 2:09–2:31 | Group it | [imports.review] source = ... → City import: review.reviewer → Rig import: rig/review.reviewer → [[patches.agent]] to tweak (on screen: Gas City diagram `import-binding-namespace`) |
| 2:31–2:43 | Name it | “Import packs, pin versions, patch the differences, and never fork.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** The [imports.gc] block from the pack.toml in Tutorial 01.

**Repository references:**

- [docs/guides/understanding-packs.md](https://github.com/gastownhall/gascity/blob/main/docs/guides/understanding-packs.md)
- [docs/guides/shareable-packs.md](https://github.com/gastownhall/gascity/blob/main/docs/guides/shareable-packs.md)
- [diagram: import-binding-namespace](https://github.com/gastownhall/gascity/blob/main/docs/diagrams/excalidraw-rendered/import-binding-namespace.svg)
- [diagram: pack-loading](https://github.com/gastownhall/gascity/blob/main/docs/diagrams/excalidraw-rendered/pack-loading.svg)

**Verify before Take 1:**

- [ ] understanding-packs.md: city imports give gc.planner; rig imports give checkout-service/gc.planner.
- [ ] understanding-packs.md: a patch changes an existing agent; it never creates one.

### Day 35: The Whole Job, End to End

Friday 13 November 2026 · concept: **The factory, assembled** · builds on: Day 34: Imports: Reuse Without Copying

> Takeaway: Write the method once, and the factory turns it into finished work.

**WHAT** — A real build is a pipeline of everything we've learned: decompose, drain, review, gap-check, fix, check and ship.

- Decompose a plan
- Drain in parallel
- Review, gap-check, ship

**WHY** — This is Day 1's promise: describe a feature once and come back to a finished branch, at production quality and machine speed.

- Review gives quality
- Parallelism gives speed
- Durable work is never lost

**HOW** — The formula is the method, the beads are the work and the orchestrator is the engine, all outside any agent's session.

- Formula = the method
- Beads = the work
- Orchestrator = the engine
- Packs configure; events observe

**See it — demo: The whole factory, from one formula** (default demo city (bd + Dolt); no agent, fast)

```
gc formula list | grep -iE 'build|review|plan' | head -8
gc formula show build-from-convoy | head -14
bd list --all --flat | wc -l
gc events --since 720h | wc -l
```

- Real methods shipped with the gascity pack.
- Decompose, drain, review: the whole job as a graph.
- Everything this series built is still in the store.
- And every step of it was observable.

**Group it — picture:** Gas City diagram `formula-whole-job` (One body of work, end to end).

**Say it simply:** Day 1's restaurant, fully open: recipes, stations, tickets, a head chef and a pass where every plate is checked.

- **gap analysis** — comparing the result with the plan to find what's missing

| Time | Section | Say (keywords, not a script) |
|---|---|---|
| 0:00–0:04 | Intro | Title card and music. Stay silent, settle, smile. |
| 0:04–0:29 | What & why | **The factory, assembled** · Decompose a plan · Drain in parallel · why: Review gives quality |
| 0:29–2:09 | See it | Demo: The whole factory, from one formula. Real methods shipped with the gascity pack. → Decompose, drain, review: the whole job as a graph. → Everything this series built is still in the store. → And every step of it was observable. |
| 2:09–2:31 | Group it | Formula = the method → Beads = the work → Orchestrator = the engine → Packs configure; events observe (on screen: Gas City diagram `formula-whole-job`) |
| 2:31–2:43 | Name it | “Write the method once, and the factory turns it into finished work.” |
| 2:43–2:50 | Outro | Soft music on the closing card. Say nothing. |

**Prepare:** Put Day 3's primitives diagram next to today's pipeline and name the primitive behind each stage.

**Repository references:**

- [docs/guides/understanding-formulas.md](https://github.com/gastownhall/gascity/blob/main/docs/guides/understanding-formulas.md)
- [docs/index.mdx](https://github.com/gastownhall/gascity/blob/main/docs/index.mdx)
- [diagram: formula-whole-job](https://github.com/gastownhall/gascity/blob/main/docs/diagrams/excalidraw-rendered/formula-whole-job.svg)
- [diagram: primitives](https://github.com/gastownhall/gascity/blob/main/docs/diagrams/excalidraw-rendered/primitives.svg)

**Verify before Take 1:**

- [ ] understanding-formulas.md, 'The Whole Job, End To End'.
- [ ] Same section: the work is the beads, the formula is the method, the orchestrator is the engine.
