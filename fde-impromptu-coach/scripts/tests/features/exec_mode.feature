Feature: Exec slots train headline-plus-offer
  Executives and account leaders want what has to happen (or has happened) and
  an offer to go into detail, not the deep technical answer that technical peers
  appreciate. Exec slots make that the daily drill: the listener is on the
  slide, the answer window is short, and the listener replies.

  Scenario: Exec focus fills slots with senior listeners
    Given focus_audiences is ["exec", "account_leader"]
    When today's set is planned
    Then at least 2 of 5 slots have an exec or account-leader listener
    And each of those slides shows the listener and what they care about

  Scenario: Exec focus survives the offline fallback
    Given Claude is unreachable
    When today's set is built from the question bank
    Then at least 2 of 5 questions still have an exec or account-leader listener

  Scenario: A question written for the wrong listener is rejected
    Given a slot that needs an exec or account-leader listener
    When Claude writes that question for a technical peer
    Then the question is rejected with the reason
    And the slot is filled from the bank with the listener it needs

  Scenario: Exec slides use the headline window
    Given a slot whose listener is "exec"
    When the deck is built
    Then the slide's bar runs for 25 seconds and is labelled "Headline window"
    And the hint reads "Headline → So what → What I need → Offer detail"
    And a constraint that needs more time than the window is dropped

  Scenario: The exec says that's all they needed
    Given an exec slide whose reply is "Thanks, that's all I needed"
    When the headline window ends
    Then a reply slide shows that line for 10 seconds with no new question
    And the speaker notes ask "Did you stop?"

  Scenario: Session length and chapters follow the exec timeline
    Given a set with two exec questions, their replies and three 60-second questions
    When the slide show is timed
    Then its length counts each headline window and reply slide
    And each YouTube chapter starts where its question slide starts
