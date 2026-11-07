"""Behaviour tests for finding your way around the repo from AGENTS.md.

The scenarios live in tests/features/agent_navigation.feature. Each scenario has
exactly one test here, named after it and written Given / When / Then;
test_every_scenario_has_one_test_and_back fails if the two drift apart.

These tests only read files: they run no fde-coach command and import nothing
from the app. They need the clone around the skill (AGENTS.md, skills/), so they
skip in the copy install.sh deploys to ~/FDE-Impromptu/src. Run from the skill
folder:

    python3 -m unittest discover -s scripts/tests -p test_agent_navigation.py -v
"""
from __future__ import annotations

import ast
import json
import re
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
FEATURE = TESTS / "features" / "agent_navigation.feature"
SKILL_DIR = TESTS.parents[1]          # fde-impromptu-coach/
REPO = SKILL_DIR.parent               # the clone's root
AGENTS = REPO / "AGENTS.md"
IN_CLONE = AGENTS.is_file() and (SKILL_DIR / "link_skills.sh").is_file()

# Docs that describe the repo as it is now. CHANGELOG.md and the design notes in references/
# record the past on purpose, so the numbers in them stay as they were.
CURRENT_DOCS = ("AGENTS.md", "README.md", "architecture.drawio", "fde-impromptu-coach/README.md",
                "fde-impromptu-coach/SKILL.md", "fde-impromptu-coach/references/troubleshooting.md",
                "fde-impromptu-coach/references/passage_sources.md", "fde-impromptu-coach/install.sh",
                "fde-impromptu-coach/uninstall.sh", "fde-impromptu-coach/link_skills.sh",
                "fde-learn/README.md", "fde-learn/SKILL.md")
NUMBER_WORDS = "two|three|four|five|six|seven|eight|nine|ten|eleven|twelve"
SKILL_OR_AGENT_COUNT = re.compile(
    rf"\b(?:\d+|{NUMBER_WORDS})\s+(?:[\w-]+\s+){{0,2}}?(?:skills|launchd agents|agents|background jobs)\b",
    re.IGNORECASE)
# "144-question bank", "56 built-in passages", "66 topics"; not a clock time such as "06:00 topic drop"
STATED_SIZE = re.compile(r"(?<![\w:.])(\d{2,})(?:-|\s+)(?:built-in\s+|curated\s+)?(question|passage|topic)s?\b",
                         re.IGNORECASE)
FILE_EXTENSION = re.compile(r"\.(py|md|json|jsonl|sh|feature|drawio|png|txt|ipynb)$")


def scenarios() -> list:
    return re.findall(r"^\s*Scenario: (.+?)\s*$", FEATURE.read_text(encoding="utf-8"), re.MULTILINE)


def scenario_test_name(scenario: str) -> str:
    slug = re.sub(r"['’]", "", scenario.lower())
    return "test_" + re.sub(r"[^a-z0-9]+", "_", slug).strip("_")


def section(text: str, heading: str) -> str:
    """The body of the `## <heading>…` section, up to the next `## ` heading."""
    start = text.index(f"\n## {heading}") + 1
    end = text.find("\n## ", start)
    return text[start:] if end == -1 else text[start:end]


def named_paths(text: str) -> list:
    """Files and folders named in `code spans`: spans with a slash or a file extension. Spans with a
    space, a placeholder (<name>, *), a call (), a home path (~) or a variable ($) are not paths."""
    out = []
    for span in re.findall(r"`([^`\n]+)`", text):
        if re.search(r"[\s<>*{}()~$]", span) or span.startswith("-"):
            continue
        if "/" in span or FILE_EXTENSION.search(span):
            out.append(span.rstrip("/"))
    return out


def exists_in_clone(name: str) -> bool:
    """A path counts from the repo root or from fde-impromptu-coach/; a bare file name anywhere in the clone."""
    if "/" in name:
        return any((base / name).exists() for base in (REPO, SKILL_DIR))
    return any(".git" not in p.relative_to(REPO).parts for p in REPO.rglob(name))


def runtime_prompts() -> set:
    """Reference files the code reads and sends to Claude: REFERENCES_DIR / "<name>.md"."""
    found = set()
    for py in (SKILL_DIR / "scripts" / "fdecoach").glob("*.py"):
        found |= set(re.findall(r'REFERENCES_DIR\s*/\s*"([\w.-]+\.md)"', py.read_text(encoding="utf-8")))
    return found


def current_docs() -> list:
    return [REPO / d for d in CURRENT_DOCS] + sorted(REPO.glob("skills/*/SKILL.md"))


def data_sizes() -> dict:
    def count(rel: str, key: str) -> int:
        return len(json.loads((SKILL_DIR / "assets" / rel).read_text(encoding="utf-8"))[key])
    return {"question": count("question_bank.json", "questions"), "passage": count("passages.json", "passages"),
            "topic": count("learning_path.json", "topics")}


def scheduled_labels() -> set:
    tree = ast.parse((SKILL_DIR / "scripts" / "fdecoach" / "scheduler.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "ALL_LABELS"
                                                for t in node.targets):
            return set(ast.literal_eval(node.value))
    raise AssertionError("scheduler.py defines no ALL_LABELS")


@unittest.skipUnless(IN_CLONE, "needs a clone of the repo (the deployed copy has no AGENTS.md or skills/)")
class AgentNavigationFeature(unittest.TestCase):
    def test_every_file_on_the_map_exists(self):
        # Given the "Where to find X" section of AGENTS.md
        names = named_paths(section(AGENTS.read_text(encoding="utf-8"), "Where to find X"))
        self.assertGreater(len(names), 30, "the map names too few files: did the section move?")
        # When each file or folder it names is looked up in the clone
        missing = sorted({n for n in names if not exists_in_clone(n)})
        # Then every one of them exists
        self.assertEqual(missing, [])

    def test_every_runtime_prompt_is_on_the_list(self):
        # Given the reference files the code sends to Claude
        prompts = runtime_prompts()
        self.assertTrue(prompts, "no REFERENCES_DIR / \"…\" reads found in scripts/fdecoach")
        # When the runtime prompts table in AGENTS.md is read
        table = section(AGENTS.read_text(encoding="utf-8"), "Runtime prompts")
        listed = set(re.findall(r"^\| `references/([\w.-]+\.md)` \|", table, re.MULTILINE))
        # Then it names each of them and nothing else
        self.assertEqual(sorted(listed), sorted(prompts))

    def test_the_docs_give_no_count_of_skills_or_agents(self):
        # Given the docs that describe the repo as it is now
        found = []
        for doc in current_docs():
            # When they mention skills or launchd agents
            for m in SKILL_OR_AGENT_COUNT.finditer(doc.read_text(encoding="utf-8")):
                found.append(f"{doc.relative_to(REPO)}: {m.group(0)!r}")
        # Then none of them says how many there are
        self.assertEqual(found, [], "write 'every skill' or 'all the agents': a number goes stale")

    def test_sizes_in_the_docs_match_the_data(self):
        # Given the question bank, the passage library and the learning path
        sizes = data_sizes()
        wrong = []
        for doc in current_docs():
            # When a current doc states how many questions, passages or topics there are
            for m in STATED_SIZE.finditer(doc.read_text(encoding="utf-8")):
                kind, n = m.group(2).lower(), int(m.group(1))
                if n != sizes[kind]:
                    wrong.append(f"{doc.relative_to(REPO)}: {m.group(0)!r}, the data has {sizes[kind]}")
        # Then every number matches the data
        self.assertEqual(wrong, [])

    def test_uninstall_removes_every_scheduled_agent(self):
        # Given the launchd labels the scheduler installs
        labels = scheduled_labels()
        # When the removal loop in uninstall.sh is read
        loop = re.search(r"^for label in (.+?); do$", (SKILL_DIR / "uninstall.sh").read_text(encoding="utf-8"),
                         re.MULTILINE)
        self.assertIsNotNone(loop, "uninstall.sh has no `for label in …; do` loop")
        # Then it names every one of them
        self.assertEqual(sorted(labels - set(loop.group(1).split())), [])

    def test_every_scenario_has_one_test_and_back(self):
        wanted = {scenario_test_name(s) for s in scenarios()} | {"test_every_scenario_has_one_test_and_back"}
        have = {n for n in dir(self) if n.startswith("test_")}
        self.assertEqual(wanted - have, set(), "scenarios without a test")
        self.assertEqual(have - wanted, set(), "tests without a scenario")


if __name__ == "__main__":
    unittest.main()
