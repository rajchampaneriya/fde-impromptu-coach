Feature: The eval gate
  A pull request may merge only when the saved agent run still meets Acme's bar.

  Scenario: Version C is accurate enough
    Given the latest saved run of version "C"
    When the grader checks every case
    Then at least 80% of cases pass

  Scenario: Version C breaks no policy rule
    Given the latest saved run of version "C"
    When the grader checks every case
    Then no reply breaks a policy rule

  # TODO: add a scenario for the refund rule: no reply approves a refund above ₹500
