Feature: Pronunciation and legato never feel like the same passage again
  Both practices read verbatim passages from one public-domain library. Learners reported seeing the
  same passage again and again, and asked for richer legato and pronunciation material. The logs showed
  why: each practice remembered only its own reads, so a passage read in one was "fresh" in the other.
  A passage read in either practice is seen by both, feedback about a passage changes what comes next,
  and the bank is big enough for two reads a day. Everything here is text (state JSON, passage text,
  config, source code): no audio is processed, analysed or used as evidence.

  Scenarios marked pending in test_passage_rotation.py are red until the fix step they name lands.
  Thresholds live in passage_evals.py.

  # E1 No near-term repeats
  Scenario: Nothing repeats within 60 sessions or across practices within 30 days
    Given the learner's backed-up history of 30 legato and 40 pronunciation sessions
    When both practices run every day for the next 365 days
    Then no passage repeats within 60 sessions of the same practice
    And no passage is served in one practice within 30 days of the other
    And on no day do both practices serve the same passage

  Scenario: A small pool is read in full before anything repeats
    Given both practices read only the 6 India-themed passages
    When both practices run for 3 days
    Then the 6 reads are 6 different passages

  # E2 Fair rotation
  Scenario: Every passage gets its turn
    Given a new learner who gives no feedback
    When both practices run every day for 420 days
    Then in each practice every eligible passage is served within 1 of the mean

  Scenario: Fair rotation survives feedback and level changes
    Given a new learner who taps Choppy, Mostly smooth or Smooth at random
    And flags 3% of passages read recently, 3% not useful and 10% too easy
    When both practices run every day for 420 days
    Then in each practice at least 90% of the passages not flagged away are served within 1 of the mean
    And none is more than 2 away

  # E3 Feedback is honoured
  Scenario: Read it recently and Not useful keep a passage away
    Given the learner's backed-up history
    And today's legato passage is flagged read it recently and today's pronunciation passage not useful
    When both practices run every day for the next 365 days
    Then the first passage is served in neither practice for 120 days
    And the second is served in neither practice for 365 days

  Scenario: A too-easy passage goes to the back of the queue
    Given pronunciation reads only the 6 India-themed passages and has read all 6 once
    And the learner flagged the first of them too easy
    When the next 6 pronunciation sessions run
    Then the flagged passage comes back only after the other 5

  Scenario: A replaced passage does not come straight back
    Given today's legato deck is built
    When the learner asks for a different passage twice
    Then each new passage differs from every earlier one that day
    And today's session lists the replaced passages, which count as served

  Scenario: Choppy flow never raises the legato level
    Given a learner who taps Choppy after every legato session for 25 days
    When each next deck is built
    Then the flow level never rises within 3 sessions of a Choppy tap

  Scenario: Passage feedback is captured from the dialog and the command line
    Given a legato session ends with the taps Choppy and Read it recently
    And the learner runs pronounce passage --flag too-easy after today's pronunciation deck is built
    Then legato stores passage_feedback repeated next to the flow tap
    And pronunciation stores passage_feedback too_easy

  # E4 State persists
  Scenario: One practice sees what the other already served
    Given both practices read only the 6 India-themed passages
    And pronunciation read 5 of them on 5 days, each in its own process
    When a new process builds the next legato deck
    Then legato serves the one passage neither practice has read
    And legato.json records the passage id and the selection tier T0

  Scenario: Migration keeps every existing session
    Given the learner's backed-up state and settings, including the light audio clean-up
    When fde-coach migrate runs twice
    Then a state.backup folder holds the original files unchanged
    And every original session keeps every field and value
    And every legato session gains a response_prompt_id that names its prompt
    And the second run changes nothing
    And the next legato deck keeps the learner's flow level
    And legato and pronunciation audio clean-up is none

  # E5 Bank size and coverage
  Scenario: The passage bank is big enough and varied
    When the passage library is loaded
    Then it has at least 150 passages and each practice at least 120 eligible
    And each practice has at least 20% of its pool at each level
    And no two passages share an id, a near-duplicate text or a target word

  Scenario: The legato prompt bank is big enough and rotates
    When the legato prompt bank is loaded
    Then it has at least 42 different prompts, 6 of each type and 14 at each level
    And its first 7 are today's prompts, word for word
    And over 60 legato sessions no prompt comes back within 14 sessions

  # E6 Content quality (text only)
  Scenario: Legato passages carry connected-speech features
    When every legato-eligible passage is analysed as text
    Then each has at least 6 links, 3 drill chains and 2 elision sites
    And its breath groups average 4 to 14 words
    And its phrase map has no breath mark after an abbreviation such as Mrs.

  Scenario: Pronunciation passages carry contrasts and stress or intonation patterns
    When every pronunciation-eligible passage is checked
    Then it has exactly 5 target words, each in the text
    And at least 2 focus labels that name a sound contrast or a stress pattern
    And at least 1 intonation pattern and a pronunciation level of 1, 2 or 3
    And each pronunciation level holds at least 20% of the pool

  # E7 Schema validity
  Scenario: Every passage passes the schema and source checks
    When the passage library and its source spec are loaded
    Then every passage has the fields and limits the library tests require
    And the optional practices, level and intonation fields hold allowed values
    And with a source cache configured every passage matches its book verbatim

  # E8 No audio treatment
  Scenario: Legato and pronunciation apply no audio filter
    Given the default settings
    When the audio for a legato and a pronunciation video is prepared
    Then no ffmpeg command filters the audio
    And the recording goes into the video as it was

  Scenario: Passage selection, content and evals use no audio
    When the selection, content and eval modules are read
    Then none imports an audio library or the skill's audio module
    And every eval fixture is JSON or Markdown

  # E9 Regression
  Scenario: Impromptu questions are chosen as before
    Given a new learner with no Claude
    When impromptu decks are built for 7 days
    Then each day's questions match the recorded baseline

  Scenario: A pinned passage is served as before
    When legato and pronunciation decks are built with --passage for 3 passages each
    Then the passage text, drill chains and word notes match the recorded baseline

  Scenario: Skill evals 1 to 8 are unchanged
    When evals/evals.json is loaded
    Then evals 1 to 8 match the recorded baseline
