"""Benchmark / regression harness for pxEnrich extraction.

Scores the deterministic extraction engine against curated expectations and
reports the brief's error taxonomy: false assertions, missed values, correct
abstention, and scope errors.

Usage:
    python tests/run_benchmark.py                          # example records
    python tests/run_benchmark.py path/to/benchmark.jsonl  # expert benchmark
    python tests/run_benchmark.py --include-holdout file.jsonl   # final eval only

Drop the team's 18-record expert benchmark into
tests/benchmark/benchmark_records.jsonl (same schema, see benchmark_schema.json)
and it is picked up automatically. Records with "set": "holdout" are skipped
unless --include-holdout is passed — freeze the holdout BEFORE tuning rules.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pxenrich import db as dbmod  # noqa: E402
from pxenrich.models import AssertionStatus  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FILES = [
    os.path.join(HERE, "benchmark", "benchmark_records.jsonl"),  # expert set, if present
    os.path.join(HERE, "benchmark", "example_records.jsonl"),
]

ABSTAIN_STATES = {"unknown", "abstained", "conflicting", "not_evaluable", "mixed"}


def load_records(paths: list[str]) -> list[dict]:
    recs = []
    for p in paths:
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        recs.append(json.loads(line))
            break  # first existing file wins (expert set shadows examples)
    return recs


def score(records: list[dict], include_holdout: bool = False) -> dict:
    conn = dbmod.connect()
    results = []
    for exp in records:
        if exp.get("set") == "holdout" and not include_holdout:
            continue
        rec = dbmod.get_dataset(conn, exp["accession"])
        if rec is None:
            results.append({**exp, "outcome": "dataset_missing"})
            continue
        actual = next((a for a in rec.assertions if a.field == exp["field"]), None)
        if actual is None:
            results.append({**exp, "outcome": "field_missing"})
            continue

        a_status = actual.status.value
        e_status = exp["expected_status"]
        outcome = "pass"

        if e_status in ABSTAIN_STATES and a_status == "asserted":
            outcome = "false_assertion"
        elif e_status == "asserted" and a_status in (ABSTAIN_STATES - {"mixed"}):
            outcome = "missed_value"
        elif e_status == "asserted" and a_status == "asserted":
            ev = (exp.get("expected_value") or "").lower()
            av = (actual.value or "").lower()
            match_mode = exp.get("value_match", "contains")
            ok = (ev == av) if match_mode == "exact" else (ev in av)
            if not ok:
                outcome = "scope_error"
        elif e_status != a_status:
            # both are non-asserted but different flavors of uncertainty
            outcome = "scope_error" if a_status != "asserted" else "false_assertion"

        results.append({**exp, "actual_status": a_status,
                        "actual_value": actual.value, "outcome": outcome})

    scored = [r for r in results if r["outcome"] not in
              ("dataset_missing", "field_missing")]
    n = len(scored) or 1
    passes = sum(1 for r in scored if r["outcome"] == "pass")
    fa = sum(1 for r in scored if r["outcome"] == "false_assertion")
    mv = sum(1 for r in scored if r["outcome"] == "missed_value")
    se = sum(1 for r in scored if r["outcome"] == "scope_error")
    abst_expected = [r for r in scored
                     if r["expected_status"] in ("abstained", "unknown", "conflicting")]
    abst_correct = sum(1 for r in abst_expected
                       if r.get("actual_status") == r["expected_status"])

    return {
        "n_scored": len(scored),
        "n_skipped": len(results) - len(scored),
        "accuracy": round(passes / n, 3),
        "false_assertion_rate": round(fa / n, 3),
        "missed_value_rate": round(mv / n, 3),
        "scope_error_rate": round(se / n, 3),
        "correct_abstention_rate": round(
            abst_correct / len(abst_expected), 3) if abst_expected else None,
        "failures": [r for r in results if r["outcome"] != "pass"],
    }


def main() -> int:
    args = [a for a in sys.argv[1:]]
    include_holdout = "--include-holdout" in args
    paths = [a for a in args if not a.startswith("--")] or DEFAULT_FILES
    records = load_records(paths if isinstance(paths, list) else [paths])
    if not records:
        print("No benchmark records found.", file=sys.stderr)
        return 2
    report = score(records, include_holdout)
    print(json.dumps(report, indent=2))
    # Non-zero exit when any false assertion occurs: a confident answer
    # without support is a defect (brief §12).
    return 1 if report["false_assertion_rate"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
