**Daily video series**

# Software Factory: the learning path

35 videos from 10 October 2026 · one concept a day · source: https://github.com/gastownhall/gascity (verified at e244b16f3a)

Generated from `assets/factory_curriculum.json` by `fde-coach factory plan --markdown`. Dates assume one video a day; a missed day carries its topic over, so no concept is skipped.

Rule for every video: one video, one concept, one clear takeaway. Understand → Explain → Demonstrate → Publish → Repeat.

## Module 1: The Big Picture

Know what a software factory is and the shape of Gas City.

| Day | Date | Topic | Takeaway | HOW visual |
|---|---|---|---|---|
| 1 | Sat 10 Oct | Software Factory vs. Coding Agent | A coding agent gives you faster hands; a software factory gives you finished work without you in the loop. | compare |
| 2 | Sun 11 Oct | Gas City: Zero Hardcoded Roles | Gas City hardcodes zero roles, so you can build the factory your team actually needs. | layers |
| 3 | Mon 12 Oct | The Six Primitives | Who, what, how, where, configure, observe: six primitives hold the whole system. | primitives |
| 4 | Tue 13 Oct | The Machinery Underneath | The orchestrator never waits for a callback; it reads shared state, so work survives a crash on either side. | flow |
| 5 | Wed 14 Oct | Why Not a Bash Loop or CI? | A loop repeats; an orchestrator remembers. | compare |
| 6 | Thu 15 Oct | The Toolbelt: gc, bd, tmux, Dolt | Learn which tool owns which job, and every error message gets easier to read. | layers |
| 7 | Fri 16 Oct | City and Rig: The Factory Floor | The city is your factory floor; a rig is a project you bring onto it. | code |

## Module 2: Work: Beads

Understand the unit of work, how it is ordered, grouped and claimed.

| Day | Date | Topic | Takeaway | HOW visual |
|---|---|---|---|---|
| 8 | Sat 17 Oct | Your First Sling: The Work Lifecycle | One sling sets the whole loop in motion: bead, session, work, close. | work-lifecycle |
| 9 | Sun 18 Oct | The Bead: Work That Survives a Crash | Sessions are disposable; beads are not. | bead-lifecycle |
| 10 | Mon 19 Oct | Everything Is a Bead | When everything is a bead, one set of tools works on everything. | hub |
| 11 | Tue 20 Oct | Dependencies: Order Without a Scheduler | Agents only see ready work, so the right order emerges from the graph. | flow |
| 12 | Wed 21 Oct | Convoys: Track a Batch as One | A convoy groups work without making the pieces wait on each other. | convoy-tracks-membership |
| 13 | Thu 22 Oct | The Pull Model: How Agents Find Work | Routing decides which queue a bead lands in; readiness decides whether anyone can see it. | flow |
| 14 | Fri 23 Oct | Demo: A Tiny Work Graph by Hand | A formula simply creates this graph for you, and now you know exactly what it builds. | code |

## Module 3: Workers: Agents and Sessions

Define agents, run sessions and see how agents coordinate.

| Day | Date | Topic | Takeaway | HOW visual |
|---|---|---|---|---|
| 15 | Sat 24 Oct | Agents: A Role Is a Prompt | A reviewer is nothing more than the prompt you wrote for it. | code |
| 16 | Sun 25 Oct | Harnesses: One Fleet, Many Coding Agents | In Gas City, a mixed fleet of coding agents is just configuration. | layers |
| 17 | Mon 26 Oct | Sessions: On-Demand vs. Always-On | Agents are definitions; sessions are the live processes, and they're disposable by design. | compare |
| 18 | Tue 27 Oct | Agents Talk Only Through the Store | No agent holds a reference to another, so any of them can crash, scale or swap. | coordination-through-store |
| 19 | Wed 28 Oct | Hooks: Wiring a Coding Agent Into the City | Hooks turn a bare coding agent into a member of the city. | flow |
| 20 | Thu 29 Oct | Pools: Scaling Workers to Demand | A pool turns one agent definition into exactly as many workers as the work needs. | flow |
| 21 | Fri 30 Oct | Demo: Build a Reviewer and Sling a Review | A role, a prompt and one sling: that's a new specialist on your factory floor. | code |

## Module 4: Methods: Formulas

Write a method once and let the orchestrator run it as a graph.

| Day | Date | Topic | Takeaway | HOW visual |
|---|---|---|---|---|
| 22 | Sat 31 Oct | Formulas: Write the Method Down Once | Write the method down once, and the orchestrator can run it again and again. | pancakes-dag |
| 23 | Sun 01 Nov | From TOML to Beads: Cook vs. Sling | A formula is the method; applying it prints the work as beads that outlive everything. | formula-apply-pipeline |
| 24 | Mon 02 Nov | Variables: One Method, Many Runs | Variables turn one written method into a method for every situation. | code |
| 25 | Tue 03 Nov | v1 vs. v2 Formulas: Who Is the Engine? | In v2 the orchestrator, not a single agent, is the engine. | formula-v1-vs-v2 |
| 26 | Wed 04 Nov | Check and Retry: Work That Verifies Itself | With check, done means verified, not just claimed. | flow |
| 27 | Thu 05 Nov | Drain: Fan Out Over a Convoy | Drain turns a convoy of any size into parallel, isolated runs. | formula-drain-fanout |
| 28 | Fri 06 Nov | Demo: Write and Run the Pancakes Formula | Write the method, preview it, run it, and the orchestrator drives it to done. | code |

## Module 5: Automation and Operations

Make the factory start, supervise and observe its own work.

| Day | Date | Topic | Takeaway | HOW visual |
|---|---|---|---|---|
| 29 | Sat 07 Nov | Orders: When, Not How | Formulas say how; orders say when, and then nobody has to press go. | cooldown-vs-cron |
| 30 | Sun 08 Nov | Exec Orders: Automation Without an LLM | Use agents for judgment and scripts for chores. | compare |
| 31 | Mon 09 Nov | Health Patrol: Let It Crash | Gas City doesn't prevent crashes; it makes them cheap. | flow |
| 32 | Tue 10 Nov | Events: Watching the Fleet | Events let humans watch the factory, and let the factory react to itself. | flow |

## Module 6: Composition: Packs

Package, share and assemble the whole factory.

| Day | Date | Topic | Takeaway | HOW visual |
|---|---|---|---|---|
| 33 | Wed 11 Nov | Packs: What Configures the Factory | A pack turns how your team works into versioned, shareable files. | hand-rolled-to-city |
| 34 | Thu 12 Nov | Imports: Reuse Without Copying | Import packs, pin versions, patch the differences, and never fork. | import-binding-namespace |
| 35 | Fri 13 Nov | The Whole Job, End to End | Write the method once, and the factory turns it into finished work. | formula-whole-job |
