"""Step definitions for tests/features/eval_gate.feature. YOU fill this in (project 3, step 6)."""
from pytest_bdd import given, parsers, scenarios, then, when

from lab.acme import load_cases, load_results
from lab.evals import score

scenarios("features/eval_gate.feature")


@given(parsers.parse('the latest saved run of version "{version}"'), target_fixture="run")
def run(version):
    return load_results(version)


@when("the grader checks every case", target_fixture="scores")
def scores(run):
    by_id = {c["id"]: c for c in load_cases()}
    return [score(by_id[r["id"]], r) for r in run]


@then("at least 80% of cases pass")
def accurate(scores):
    # TODO: assert the share of scores with "passed" is at least 0.8, with a message that shows the share
    raise NotImplementedError


@then("no reply breaks a policy rule")
def no_violations(scores):
    # TODO: assert every score has policy_ok; list the failing case ids in the message
    raise NotImplementedError
