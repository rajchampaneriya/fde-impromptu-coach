Feature: A coding agent finds its way from AGENTS.md
  Every agent session starts cold and reads AGENTS.md first. Three sessions in a
  row made about 30 tool calls before their first edit, finding where the code
  lives, which tests already fail and how to try a command safely. They also
  trusted docs that had gone stale: a count of skills, a count of launchd
  agents, the size of the question bank. These scenarios keep the map true and
  keep numbers that drift out of the docs.

  Scenario: Every file on the map exists
    Given the "Where to find X" section of AGENTS.md
    When each file or folder it names is looked up in the clone
    Then every one of them exists

  Scenario: Every runtime prompt is on the list
    Given the reference files the code sends to Claude
    When the runtime prompts table in AGENTS.md is read
    Then it names each of them and nothing else

  Scenario: The docs give no count of skills or agents
    Given the docs that describe the repo as it is now
    When they mention skills or launchd agents
    Then none of them says how many there are

  Scenario: Sizes in the docs match the data
    Given the question bank, the passage library and the learning path
    When a current doc states how many questions, passages or topics there are
    Then every number matches the data

  Scenario: Uninstall removes every scheduled agent
    Given the launchd labels the scheduler installs
    When the removal loop in uninstall.sh is read
    Then it names every one of them
