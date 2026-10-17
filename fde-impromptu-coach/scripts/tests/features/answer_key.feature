Feature: Exec answer key after the session
  Not freezing is no longer the problem; the next step is practising the correct
  response. After recording, every question gets a model answer in the exec
  shape (one breath, the 25-second answer, the detail to offer, the trap) to
  read and say back.

  Scenario: The answer key arrives after recording
    Given today's five questions are recorded
    When the practice session finishes
    Then an answer key page is saved with one card per question
    And every card has a one-breath headline, the exec answer, the detail to offer and the trap
    And the page opens once the practice chain is over

  Scenario: An exec reply gets its own model answer
    Given an exec question whose listener replied "What's the biggest risk?"
    When the answer key is written
    Then its card shows the reply and a model answer to it

  Scenario: Model answers stay hidden until today is recorded
    Given today's deck is built but not recorded
    When I ask for the answer key
    Then it is refused unless I pass --reveal

  Scenario: Every exec answer fits the headline window
    Given Claude returns an exec answer longer than 70 words
    When the answer key is validated
    Then that answer is rejected with the reason
    And the card shows the exec shape to fill in instead

  Scenario: Offline practice still gets an answer key later
    Given Claude is unreachable when the session finishes
    When the 15-minute tick runs after Claude is back
    Then the answer key is filled in

  Scenario: Every one-breath line collects on one page
    Given two recorded days with answer keys
    When the index is built
    Then it lists each day's one-breath lines, newest day first
