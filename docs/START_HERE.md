# Start here — pxEnrich curation, in order

Welcome. You are building the ground-truth benchmark that an AI system is graded against — co-authorship-level work. Everything you need is in this folder. Do it in this order:

## Order of operations

| Step | What | Where | Time |
|---|---|---|---|
| 1 | Read the biology primer (required track) | `BIOLOGY_PRIMER.md` | ~75 min |
| 2 | Take the self-test quiz (aim ≥16/18) | `ANNOTATION_QUIZ.md` | ~30 min |
| 3 | Read one accession labeled end-to-end | `WORKED_EXAMPLE.md` | ~15 min |
| 4 | Read the assignment (protocol, grading, dates) | `pxEnrich_BenchmarkCurationAssignment.md` | ~20 min |
| 5 | Find your accessions | `accession_assignments.md` | 2 min |
| 6 | Label, with the rules card open beside you | `RULES_CARD.md` | the real work |

## The one rule that cannot wait until step 4

**Commit your labels to git *before* you run `tests/run_benchmark.py` for the first time.** Your pre-harness commit is what proves your labels are independent of the AI engine — it's what makes them a publishable reference standard. (Details: assignment §"Self-validation".)

## What is graded vs. what is process

**Graded (the three files in your PR to `submissions/<your-folder>/`):**
1. `benchmark_<netid>.jsonl` — your 60 records
2. `curation_log_<netid>.md` — one entry per accession (Form 1)
3. `reflection_<netid>.md` — half a page

**Process, not graded (but expected):** the Friday 3-question check-in (Form 4), and engine-disagreement reports (Form 2 — these earn *bonus* points). All forms: `STUDENT_RESPONSE_FORMS.md`.

## Key dates (2026)

| Date | Due |
|---|---|
| **Mon Nov 24** | The 2 calibration accessions (12 records) committed & PR'd — labeled independently, no discussing them |
| **Fri Dec 5** | All 10 accessions: three files in your PR |
| **Fri Dec 12** | Group adjudication done; final labels merged; benchmark v1.0 tagged |
| January | Frozen holdout scored at final evaluation |

## Questions

Team channel, so everyone sees the answer. Genuinely ambiguous records are worth raising — they often become the best benchmark cases.
