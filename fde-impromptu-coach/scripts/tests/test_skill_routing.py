"""Behaviour tests for routing the learner's words to the right skill and command.

The scenarios live in tests/features/skill_routing.feature. Each scenario has
exactly one test here, named after it and written Given / When / Then;
test_every_scenario_has_one_test_and_back fails if the two drift apart.

These tests read the repo around the skill (skills/, fde-learn/, AGENTS.md), so
they run from a clone and skip in the copy install.sh deploys to
~/FDE-Impromptu/src. Run from the skill folder:

    python3 -m unittest discover -s scripts/tests -v
"""
from __future__ import annotations

import contextlib
import io
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_coach import Home  # noqa: E402  (also puts scripts/ on sys.path)

import fde_coach  # noqa: E402
from fdecoach.config import CLAUDE_SKILLS  # noqa: E402

TESTS = Path(__file__).resolve().parent
FEATURE = TESTS / "features" / "skill_routing.feature"
SKILL_DIR = TESTS.parents[1]          # fde-impromptu-coach/
REPO = SKILL_DIR.parent               # the clone's root
LINKER = SKILL_DIR / "link_skills.sh"
IN_CLONE = (REPO / "AGENTS.md").is_file() and LINKER.is_file()

PRACTICES = ("impromptu", "pronunciation", "legato")
FOLDERS = {"fde-impromptu-coach": "fde-impromptu-coach", "fde-learn": "fde-learn",
           **{p: f"skills/{p}" for p in PRACTICES}}
LEADS = {"fde-impromptu-coach": "impromptu", "fde-learn": "fde learn",
         "impromptu": "impromptu", "pronunciation": "pronunciation", "legato": "legato"}
MISSPELT = {"impromptu": "impromptue", "pronunciation": "pronounciation", "legato": "lagato"}
START = {"impromptu": "fde-coach session --detach",
         "pronunciation": "fde-coach pronounce session --detach",
         "legato": "fde-coach legato session --detach"}
HIDDEN_RULE = {"impromptu": "Keep the surprise", "pronunciation": "Cold read", "legato": "Cold read"}


def scenarios() -> list:
    return re.findall(r"^\s*Scenario: (.+?)\s*$", FEATURE.read_text(encoding="utf-8"), re.MULTILINE)


def scenario_test_name(scenario: str) -> str:
    slug = re.sub(r"['’]", "", scenario.lower())
    return "test_" + re.sub(r"[^a-z0-9]+", "_", slug).strip("_")


def skill_file(name: str) -> Path:
    return REPO / FOLDERS[name] / "SKILL.md"


def frontmatter(path: Path) -> dict:
    import yaml  # PyYAML (requirements.txt); imported here so the deployed copy can skip without it
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path}: frontmatter must open on the first line"
    return yaml.safe_load(text.split("---\n")[1]) or {}


def fde_coach_commands(text: str) -> list:
    """Every `fde-coach …` code span, with <placeholders> and [optional] brackets filled in."""
    out = []
    for span in re.findall(r"`(fde-coach [^`]+)`", text):
        cmd = re.sub(r"<[^>]+>", "1", span.replace("\\|", "|")).replace("[", "").replace("]", "")
        tokens = shlex.split(cmd)
        if "…" in tokens:      # "fde-coach learn …" names a family of commands, not one command
            continue
        out.append((span, tokens[1:]))
    return out


def link(skills_dir: Path, *args: str, repo_linker: Path = LINKER) -> subprocess.CompletedProcess:
    env = dict(os.environ, CLAUDE_SKILLS_DIR=str(skills_dir))
    return subprocess.run(["bash", str(repo_linker), *args], env=env, capture_output=True, text=True, timeout=60)


def links(skills_dir: Path) -> dict:
    return {p.name: os.readlink(p) for p in sorted(skills_dir.iterdir()) if p.is_symlink()}


@unittest.skipUnless(IN_CLONE, "needs a clone of the repo (the deployed copy has no skills/ or AGENTS.md)")
class SkillRoutingFeature(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fdecoach-skills-"))
        self.skills = self.tmp / "skills"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_each_practice_has_its_own_slash_command(self):
        # Given the skills in this repo / When Claude Code reads their names
        names = {n: frontmatter(skill_file(n)).get("name") for n in FOLDERS}
        # Then each practice has a skill named after its folder, the umbrella included
        for n in ("impromptu", "pronunciation", "legato", "fde-learn", "fde-impromptu-coach"):
            self.assertEqual(names[n], Path(FOLDERS[n]).name, f"{n}: name must match its folder")
            self.assertEqual(names[n], n)
        # And each one-practice skill shows an argument hint after its slash command
        for n in PRACTICES + ("fde-learn",):
            self.assertTrue(frontmatter(skill_file(n)).get("argument-hint"), f"{n}: no argument-hint")

    def test_frontmatter_parses_so_claude_code_sees_the_description(self):
        # Given every SKILL.md in this repo
        files = sorted(REPO.glob("*/SKILL.md")) + sorted(REPO.glob("skills/*/SKILL.md"))
        self.assertEqual(len(files), len(FOLDERS))
        for f in files:
            # When its frontmatter is read as YAML / Then it parses and has a name and a description
            fm = frontmatter(f)
            self.assertIsInstance(fm.get("name"), str, f)
            self.assertIsInstance(fm.get("description"), str, f)
            self.assertGreater(len(fm["description"]), 100, f)

    def test_descriptions_fit_the_skill_listing_and_lead_with_the_practice(self):
        for n in FOLDERS:
            # Given each skill's description / When Claude Code builds the skill listing
            desc = frontmatter(skill_file(n))["description"]
            # Then every description is at most 1024 characters
            self.assertLessEqual(len(desc), 1024, n)
            # And the practice's name appears in its first sentence
            first = desc.split(". ")[0].lower()
            self.assertIn(LEADS[n], first, f"{n}: first sentence is {first!r}")

    def test_misspelled_practice_names_still_find_the_right_skill(self):
        # Given the learner writes "impromptue", "pronounciation" or "lagato"
        descs = {n: frontmatter(skill_file(n))["description"].lower() for n in FOLDERS}
        for practice, typo in MISSPELT.items():
            # When Claude matches the words against the skill descriptions
            hits = [n for n, d in descs.items() if typo in d]
            # Then each misspelling appears in its own practice's description and in no other
            self.assertEqual(hits, [practice], typo)

    def test_every_command_a_skill_tells_claude_to_run_is_a_real_command(self):
        # Given the fde-coach commands written in the skills and in AGENTS.md
        sources = [skill_file(n) for n in FOLDERS] + [REPO / "AGENTS.md"]
        commands = [(src.relative_to(REPO), span, argv) for src in sources
                    for span, argv in fde_coach_commands(src.read_text(encoding="utf-8"))]
        self.assertGreater(len(commands), 40)
        parser = fde_coach.build_parser()
        rejected = []
        for src, span, argv in commands:
            # When each one is parsed by the fde-coach command line
            with contextlib.redirect_stderr(io.StringIO()) as err:
                try:
                    parser.parse_args(argv)
                except SystemExit:
                    rejected.append(f"{src}: `{span}` -> {err.getvalue().strip().splitlines()[-1]}")
        # Then none is rejected
        self.assertEqual(rejected, [])

    def test_starting_a_practice_runs_detached(self):
        for p in PRACTICES:
            # Given the impromptu, pronunciation and legato skills
            text = skill_file(p).read_text(encoding="utf-8")
            # When Claude starts a practice with no arguments (the first row of the table starts with "empty")
            row = next(line for line in text.splitlines() if line.startswith("| empty"))
            # Then it runs that practice's session with --detach
            self.assertIn(f"`{START[p]}`", row, p)
            # And every session command in those skills is detached
            for span, argv in fde_coach_commands(text):
                if "session" in argv:
                    self.assertIn("--detach", argv, f"{p}: `{span}`")

    def test_the_surprise_and_the_cold_read_survive_the_shortcuts(self):
        for p in PRACTICES:
            # Given the impromptu, pronunciation and legato skills
            text = skill_file(p).read_text(encoding="utf-8")
            # Then none of them tells Claude to pass --reveal
            self.assertNotIn("--reveal", text, p)
            # And each states its keep-it-hidden rule
            self.assertIn(f"**{HIDDEN_RULE[p]}.**", text, p)

    def test_the_installer_links_every_skill_where_claude_code_looks(self):
        # Given an empty skills folder / When link_skills.sh runs
        first = link(self.skills)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        # Then every skill is a link to its folder in this clone
        want = {n: str((REPO / FOLDERS[n]).resolve()) for n in CLAUDE_SKILLS}
        self.assertEqual(links(self.skills), want)
        for n in CLAUDE_SKILLS:
            self.assertTrue((self.skills / n / "SKILL.md").is_file(), n)
        # And running it again changes nothing
        again = link(self.skills)
        self.assertEqual(again.returncode, 0)
        self.assertEqual(links(self.skills), want)
        self.assertEqual(again.stdout.count("already linked"), len(CLAUDE_SKILLS))
        # And --check reports every skill as linked
        check = link(self.skills, "--check")
        self.assertEqual(check.returncode, 0, check.stdout)
        self.assertEqual(check.stdout.count("[ok]"), len(CLAUDE_SKILLS))

    def test_the_installer_never_overwrites_a_folder_it_did_not_make(self):
        # Given the skills folder already holds a real legato folder
        mine = self.skills / "legato"
        mine.mkdir(parents=True)
        (mine / "SKILL.md").write_text("---\nname: legato\ndescription: my own\n---\n", encoding="utf-8")
        # When link_skills.sh runs
        run = link(self.skills)
        # Then that folder is untouched and the run reports it
        self.assertEqual(run.returncode, 1)
        self.assertFalse(mine.is_symlink())
        self.assertIn("description: my own", (mine / "SKILL.md").read_text(encoding="utf-8"))
        self.assertIn("/legato", next(l for l in run.stdout.splitlines() if l.startswith("[!!]")))
        # And the other skills are still linked
        self.assertEqual(set(links(self.skills)), set(CLAUDE_SKILLS) - {"legato"})
        self.assertEqual(link(self.skills, "--check").returncode, 1)

    def test_a_clone_inside_the_skills_folder_is_explained(self):
        # Given the repo was cloned inside the skills folder
        nested = self.skills / "fde-impromptu-coach"
        for n, folder in FOLDERS.items():
            (nested / folder).mkdir(parents=True, exist_ok=True)
            shutil.copy(skill_file(n), nested / folder / "SKILL.md")
        shutil.copy(LINKER, nested / "fde-impromptu-coach" / "link_skills.sh")
        # When link_skills.sh runs from that clone
        run = link(self.skills, repo_linker=nested / "fde-impromptu-coach" / "link_skills.sh")
        # Then it says Claude Code cannot see skills nested in a clone there and how to move it
        self.assertIn("cannot see", run.stdout)
        self.assertIn("Move the clone", run.stdout)
        self.assertEqual(run.returncode, 1)
        self.assertFalse(nested.is_symlink())
        # And the one-practice skills are still linked
        for p in PRACTICES + ("fde-learn",):
            self.assertTrue((self.skills / p).is_symlink(), p)
            self.assertTrue((self.skills / p / "SKILL.md").is_file(), p)

    def test_uninstall_removes_only_this_clones_links(self):
        # Given every skill is linked and fde-learn points to another clone
        link(self.skills)
        other = self.tmp / "other-clone" / "fde-learn"
        other.mkdir(parents=True)
        (self.skills / "fde-learn").unlink()
        (self.skills / "fde-learn").symlink_to(other)
        # When link_skills.sh --remove runs
        run = link(self.skills, "--remove")
        self.assertEqual(run.returncode, 0, run.stdout)
        # Then this clone's links are gone and the other clone's link stays
        self.assertEqual(links(self.skills), {"fde-learn": str(other)})

    def test_the_doctor_says_when_a_skill_is_not_linked(self):
        # Given every skill except legato is linked
        link(self.skills)
        (self.skills / "legato").unlink()
        home = Home()
        try:
            # When fde-coach doctor runs
            proc = home.run("doctor", now="2026-09-01T09:10:00", check=False,
                            extra={"CLAUDE_SKILLS_DIR": str(self.skills)})
        finally:
            shutil.rmtree(home.dir, ignore_errors=True)
        line = next(l for l in proc.stdout.splitlines() if "Claude Code skills" in l)
        # Then it reports legato as not found and the command that links it
        self.assertTrue(line.startswith("[!!]"), line)
        self.assertIn(": legato -", line)
        self.assertIn(f"bash {LINKER.resolve()}", line)
        self.assertNotEqual(proc.returncode, 0)

    def test_the_installer_the_doctor_and_agents_md_agree_on_the_skills(self):
        # Given the skill folders in this repo
        folders = {p.parent.name for p in REPO.glob("*/SKILL.md")} | {p.parent.name for p in REPO.glob("skills/*/SKILL.md")}
        # Then link_skills.sh, the doctor's list and the AGENTS.md skills table name exactly those skills
        script = LINKER.read_text(encoding="utf-8")
        block = re.search(r'^SKILLS="(.*?)"$', script, re.MULTILINE | re.DOTALL).group(1)
        in_script = {line.split(":")[0] for line in block.splitlines()}
        self.assertEqual({line.split(":")[1] for line in block.splitlines()}, {FOLDERS[n] for n in folders})
        agents = (REPO / "AGENTS.md").read_text(encoding="utf-8")
        table = agents.split("## Skills and slash commands")[1].split("\n## ")[0]
        in_agents = set(re.findall(r"^\| `([a-z-]+)` \|", table, re.MULTILINE))
        self.assertEqual(in_script, folders)
        self.assertEqual(set(CLAUDE_SKILLS), folders)
        self.assertEqual(in_agents, folders)

    def test_agents_md_routes_every_practice(self):
        # Given AGENTS.md at the repo root
        agents = (REPO / "AGENTS.md").read_text(encoding="utf-8")
        # Then it names every one-practice skill with its slash command and its start command
        for p in PRACTICES:
            self.assertIn(f"`/{p} [", agents, p)
            self.assertIn(f"`{START[p]}`", agents, p)
        self.assertIn("`/fde-learn [", agents)
        # And CLAUDE.md imports it
        self.assertIn("@AGENTS.md", (REPO / "CLAUDE.md").read_text(encoding="utf-8").splitlines())

    def test_every_scenario_has_one_test_and_back(self):
        wanted = {scenario_test_name(s) for s in scenarios()} | {"test_every_scenario_has_one_test_and_back"}
        have = {n for n in dir(self) if n.startswith("test_")}
        self.assertEqual(wanted - have, set(), "scenarios without a test")
        self.assertEqual(have - wanted, set(), "tests without a scenario")


if __name__ == "__main__":
    unittest.main()
