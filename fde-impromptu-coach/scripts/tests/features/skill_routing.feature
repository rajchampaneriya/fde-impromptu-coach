Feature: Every practice is one command away in Claude Code
  The learner types /impromptu, /pronunciation, /legato or /fde-learn, or just
  says what they want ("start lagato", "how should I have answered?"), and
  Claude Code runs the right fde-coach command. Claude Code finds a skill only
  at ~/.claude/skills/<name>/SKILL.md and reads its name and description on
  every turn; the rest of the skill loads when it is used.

  Scenario: Each practice has its own slash command
    Given the skills in this repo
    When Claude Code reads their names
    Then impromptu, pronunciation, legato and fde-learn each have a skill named after its folder
    And the umbrella fde-impromptu-coach skill is still there
    And each one-practice skill shows an argument hint after its slash command

  Scenario: Frontmatter parses so Claude Code sees the description
    Given every SKILL.md in this repo
    When its frontmatter is read as YAML
    Then it parses and has a name and a description

  Scenario: Descriptions fit the skill listing and lead with the practice
    Given each skill's description
    When Claude Code builds the skill listing
    Then every description is at most 1024 characters
    And the practice's name appears in its first sentence

  Scenario: Misspelled practice names still find the right skill
    Given the learner writes "impromptue", "pronounciation" or "lagato"
    When Claude matches the words against the skill descriptions
    Then each misspelling appears in its own practice's description and in no other

  Scenario: Every command a skill tells Claude to run is a real command
    Given the fde-coach commands written in the skills and in AGENTS.md
    When each one is parsed by the fde-coach command line
    Then none is rejected

  Scenario: Starting a practice runs detached
    Given the impromptu, pronunciation and legato skills
    When Claude starts a practice with no arguments
    Then it runs that practice's session with --detach
    And every session command in those skills is detached

  Scenario: The surprise and the cold read survive the shortcuts
    Given the impromptu, pronunciation and legato skills
    Then none of them tells Claude to pass --reveal
    And each states its keep-it-hidden rule

  Scenario: The installer links every skill where Claude Code looks
    Given an empty skills folder
    When link_skills.sh runs
    Then every skill is a link to its folder in this clone
    And running it again changes nothing
    And --check reports every skill as linked

  Scenario: The installer never overwrites a folder it did not make
    Given the skills folder already holds a real legato folder
    When link_skills.sh runs
    Then that folder is untouched and the run reports it
    And the other skills are still linked

  Scenario: A clone inside the skills folder is explained
    Given the repo was cloned inside the skills folder
    When link_skills.sh runs from that clone
    Then it says Claude Code cannot see skills nested in a clone there and how to move it
    And the one-practice skills are still linked

  Scenario: Uninstall removes only this clone's links
    Given every skill is linked and fde-learn points to another clone
    When link_skills.sh --remove runs
    Then this clone's links are gone and the other clone's link stays

  Scenario: The doctor says when a skill is not linked
    Given every skill except legato is linked
    When fde-coach doctor runs
    Then it reports legato as not found and the command that links it

  Scenario: The installer, the doctor and AGENTS.md agree on the skills
    Given the skill folders in this repo
    Then link_skills.sh, the doctor's list and the AGENTS.md skills table name exactly those skills

  Scenario: AGENTS.md routes every practice
    Given AGENTS.md at the repo root
    Then it names every one-practice skill with its slash command and its start command
    And CLAUDE.md imports it
