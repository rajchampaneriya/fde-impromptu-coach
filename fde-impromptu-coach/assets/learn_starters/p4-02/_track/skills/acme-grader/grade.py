"""Grade one saved run: python skills/acme-grader/grade.py <version>. YOU fill this in (project 4, step 2)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lab.acme import load_cases, load_results  # noqa: E402
from lab.evals import score, summary  # noqa: E402


def main(version: str) -> int:
    rows = load_results(version)
    by_id = {c["id"]: c for c in load_cases()}
    scores = [score(by_id[r["id"]], r) for r in rows]
    # TODO: print each check from summary(scores) with ± 2 se, then the provenance hashes stored in the run
    #       (model_id, prompt_sha, grader_sha, dataset_sha), or "missing" when a run has none
    raise NotImplementedError


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "C"))
