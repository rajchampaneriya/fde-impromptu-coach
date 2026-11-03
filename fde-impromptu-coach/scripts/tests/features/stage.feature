Feature: Weekend Stage turns one famous TED talk a weekend into practice on camera
  Reciting a talk trains memory; stealing one delivery move a week trains
  delivery. Each weekend the learner studies one segment off camera, then
  records three takes: Take A mirrors the speaker, Take B uses the same move on
  their own FDE material, Take C adds a twist that stays hidden until its slide.
  TED talks are CC BY-NC-ND 4.0, so the catalogue keeps links, times and our own
  delivery notes, never a transcript, and nothing from TED reaches an upload.

  Scenario: The weekend talk follows the curriculum
    Given weeks 1 to 3 are recorded
    When the next weekend's deck is built
    Then it uses talk 4, Simon Sinek, and its Take A segment
    And the deck runs Take A, Take B and Take C with a reset between each

  Scenario: The weekly streak survives the weekdays
    Given stage was recorded on each of the last 3 weekends, one of them on a Sunday
    When stage status runs on a Wednesday
    Then the current streak is 3 weeks
    And this weekend is due by Sunday, with nothing broken

  Scenario: A missed Saturday rolls to Sunday
    Given the launchd agent runs on Saturday and Sunday mornings
    And Saturday ended without a recording
    When the Sunday run fires
    Then the same week's deck opens again instead of a new one
    And a calendar alert waits for Sunday evening

  Scenario: The prep page embeds TED's player and never the words
    Given this weekend's talk
    When stage prep runs
    Then a local page shows TED's embedded player, the segment and three watch passes
    And it shows Take B's prompt but not Take C's twist
    And the transcript is a link to ted.com, never copied

  Scenario: A segment found on the first watch is saved
    Given week 4's segment has no times yet
    When the learner saves its start and end
    Then the prep page and the Take A slide show those times

  Scenario: Talks are links, never text
    Given the talk catalogue
    When it is validated
    Then it holds 10 talks on 10 subjects, one per week
    And every talk has a ted.com link, a segment, its licence, a Take B and a Take C
    And no talk has a transcript field and no coach note runs past 60 words

  Scenario: Video practices record with the camera
    Given the stage practice records video
    When a session runs
    Then QuickTime records the camera into the stage recordings folder
    And no slides-plus-audio video is assembled
    And the week is marked recorded

  Scenario: Nothing from TED reaches YouTube
    Given a recorded stage session
    When its upload is prepared
    Then the uploaded file is the camera recording
    And the description credits TED under CC BY-NC-ND 4.0 with the talk's link
    And the video is private

  Scenario: Stage is a real skill
    Given the skills in this repo
    When link_skills.sh, CLAUDE_SKILLS and AGENTS.md are compared
    Then each of them names stage
    And /stage with no arguments starts a detached session
