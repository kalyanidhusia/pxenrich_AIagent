# pxEnrich Benchmark Curation Assignment (v4 — 2026-11-19)

New here? Read `START_HERE.md` first — it gives the order of operations. This document is the complete protocol; `RULES_CARD.md` is its one-page condensation to keep open while labeling. (v4 merges all earlier addenda into one consistent document; the rules themselves are unchanged from what the calibration round started under.)

## Why you are building a benchmark

Your job is to create ground truth: expert-checkable labels saying what the correct answer is for real public datasets, so the pxEnrich extraction engine can be scored against them. Every serious AI product is graded this way — and your records extend the project's reference benchmark.

A benchmark record says, for one dataset and one field (say, HER2 status of PXD061456): what the correct value is, or that the correct answer is `unknown`, `mixed`, `conflicting`, `abstained`, or `not_evaluable`. The hardest and most valuable lesson: **"we don't know" is often the right answer**, and writing down *why* is what makes a label usable.

What you practice: navigating real repository records, reading scientific metadata critically, separating what a study *is about* from what its cohort *is*, and producing machine-readable curation with provenance.

## The evidence trail: working your way to PRIDE

For each accession, visit the sources **in this order** and record how far you had to go:

| Step | Source | What you get there |
| --- | --- | --- |
| 1 | [ProteomeCentral](https://proteomecentral.proteomexchange.org/) — search, or `cgi/GetDataset?ID=PXD…` | Cross-repository record: title, species, instrument, host repository, publication links |
| 2 | The host repository page — PRIDE: `www.ebi.ac.uk/pride/archive/projects/PXD…` | Full description, keywords, protocols, lab head, file list |
| 3 | [PRIDE REST API v3](https://www.ebi.ac.uk/pride/ws/archive/v3/webjars/swagger-ui/index.html) — `GET /projects/{accession}` and `/files` | The record as JSON; the files list reveals whether an SDRF exists |
| 4 | The SDRF file (when listed) | Per-sample annotations — often the only sample-level disease/subtype/organism statement |
| 5 | The linked publication (PubMed / DOI) | Cohort details the submitter never typed into the repository |

Two rules about sources:

1. **Label only from what a source states.** Your biology knowledge tells you where to look; the label must still point at text that exists in steps 1–5 (or at a locked mapping on the rules card). If no source states it, the answer is `unknown` — not your best guess.
2. **Note the shallowest step that decided each label.** "Subtype was in the title" and "subtype only appears in Table 1 of the paper" are different findings, and the team needs to know which fields live where.

## The task

You are assigned **10 ProteomeXchange accessions** (breast-cancer-related, from the pxEnrich index) — see `accession_assignments.md`. **Two of the ten are calibration accessions shared by every annotator; eight are unique to you.** Do not discuss the two calibration accessions with anyone until all calibration labels are submitted — they measure our independent agreement.

For **each** accession, produce one record for **each of these 6 fields** (60 records total):

| Field | The question it answers |
| --- | --- |
| `disease_context` | What disease does the biological material come from (not: what is the study about)? |
| `organism_context` | Patient-derived, named human cell line, animal model, mixed (e.g., xenograft/PDX, or patients + models), or non-disease system? |
| `sample_type` | Tumor/clinical tissue, plasma, blood, cell line, PDX, organoid, EV fraction…? Use the most specific term the source states. |
| `subtype` | TNBC, luminal A/B, HER2-enriched, basal-like — or mixed cohort, or not stated? |
| `er_status` | Does a source state the cohort's ER status? |
| `her2_status` | Does a source state the cohort's HER2 status (positive / negative / low)? |

Each record is one JSON line in the repo's schema (`tests/benchmark/benchmark_schema.json`):

```json
{"accession": "PXD052290", "field": "er_status",
 "expected_status": "asserted", "expected_value": "positive", "value_match": "contains",
 "rationale": "Title states 'NF1-depleted ER+ breast cancers'; applies to the whole cohort.",
 "source_step": 1, "evidence_quote": "NF1-depleted ER+ breast cancers",
 "set": "regression", "curator": "your-netid"}
```

A complete accession labeled end-to-end, with the reasoning narrated: `WORKED_EXAMPLE.md`.

## The status vocabulary — the heart of the assignment

| Status | Use when… |
| --- | --- |
| `asserted` | A source states the value for the dataset's cohort, or a locked mapping applies (rationale says "derived") |
| `unknown` | No relevant evidence found after completing the trail → `"evidence_quote": null`, deepest step searched in the rationale |
| `mixed` | The cohort deliberately spans several values (multi-subtype comparison; patients + models; pooled material) |
| `conflicting` | Two sources make **mutually exclusive claims about the same entity, property, and scope** (e.g., paper vs SDRF on the same sample's ER status) — quote both |
| `abstained` | Relevant evidence exists but cannot support a cohort-level value — the classic case: the study is *about* a biomarker without stating cohort status |
| `not_evaluable` | The field does not apply to this record at all |

### The decision ladder (run every field through it, top to bottom)

```
Q1  Does the field apply to this record at all?            no  → not_evaluable
Q2  Did the evidence trail yield any relevant evidence?    no  → unknown
Q3  Do two sources make mutually exclusive same-scope
    claims?                                                yes → conflicting (quote both)
Q4  Does the cohort deliberately span several values?      yes → mixed
Q5  Does a source state the value for the cohort —
    or does a locked mapping apply?                        yes → asserted
                                                           no  → abstained
```

The first terminal answer ends it; falling off the bottom means the evidence was relevant but insufficient → `abstained`; no relevant evidence at all → `unknown` (Q2).

## Curation workflow

For each accession, one field at a time:

1. Read the sources in step 1–5 order. Stop drilling once the field is decided, but always read the full repository record (step 2).
2. Walk the ladder from the top.
3. Write the record: status, value (only for `asserted`/`mixed`), a **verbatim quote** in `evidence_quote` (or `null` for `unknown`), the honest `source_step`, and a one-sentence `rationale` in your own words.
4. If you changed your mind while reading deeper sources, say so in the rationale — those reversals are the most instructive records in the benchmark.

**Known traps — these are graded specifically** (each trap record is worth triple an ordinary record):

- *Topic is not status.* "HER2 RIME experiment" studies HER2; it does not make the cohort HER2-positive.
- *Keywords are weak evidence.* "breast cancer" only in submitter keywords does not make it a breast-cancer study.
- *Locked mappings only.* ER−+PR−+HER2− → TNBC is permitted (say "derived"); every other cross-layer inference (TNBC→basal-like, HER2+→HER2-enriched, ER+/HER2−→luminal A/B, tamoxifen→ER+) is forbidden.
- *Cell line ≠ patient.* MCF-7, MDA-MB-231, T47D, SK-BR-3 are human and in vitro; 4T1, MMTV-PyMT are mouse. "Homo sapiens" never means patient-derived by itself.
- *Xenograft is not a conflict.* Human tumor + mouse host = one compatible system → `organism_context: mixed`. `conflicting` is reserved for same-scope contradictions (species field vs SDRF on the same samples, paper vs SDRF on the same sample's receptor status).

## Deliverables and self-validation

Submit **three graded files** in a pull request to `submissions/<your-folder>/` (never commit to main):

1. `benchmark_<netid>.jsonl` — your 60 records
2. `curation_log_<netid>.md` — one entry per accession (Form 1 in `STUDENT_RESPONSE_FORMS.md`)
3. `reflection_<netid>.md` — half a page: hardest field and why; one concrete improvement to the extraction rules or status vocabulary

Also expected as process (not graded, but bug reports earn bonus): the Friday 3-question check-in (Form 4) and engine-disagreement reports (Form 2).

**Self-validation — order matters:**

1. Finish your labels. **Commit and push them.** This pre-harness commit is your independent annotation of record — it is what agreement statistics are computed from, and what makes your labels a publishable reference standard.
2. Only then run the harness:
   ```
   python -m pxenrich.ingest.run_ingest --seed      # build the index once
   python tests/run_benchmark.py submissions/<your-folder>/benchmark_<netid>.jsonl
   ```
3. Read its failure list. A "failure" can mean the engine is wrong (good — you found a bug: Form 2, bonus-eligible) or your label is wrong. Deciding which is the exercise. Format errors — fix freely. **Label changes after seeing engine output** go in a separate commit with the evidence-based reason documented (changing a label merely to agree with the engine defeats the entire benchmark).

A file that does not parse, or labels accessions outside your assignment, loses the format marks automatically.

## Calibration, adjudication, and the holdout

All annotators independently label the same **2 calibration accessions**; your other 8 are unique. After the calibration deadline:

1. Per-field agreement is computed on the calibration records (percent agreement; with the full pool we also report kappa in the evaluation report) — **from pre-harness commits**.
2. We adjudicate every disagreement as a group: argue from quotes, not memory; agree a final label or escalate with both rationales written down (Form 3).
3. Adjudicated records enter the class benchmark; unresolved escalations become expert-review items.

Disagreement does **not** cost marks — honest disagreement on ambiguous records is data, and some records are chosen *because* they are ambiguous. What costs marks is a disagreement with no quote behind it.

**Holdout freeze:** after adjudication, a random ≈20% of the class benchmark moves to `"set": "holdout"` — locked, never used while the team tunes extraction rules, scored once at final evaluation in January. Do not look at which records were chosen.

## Grading (100 points)

| Component | Points | Full marks |
| --- | --- | --- |
| Format validity | 10 | Parses, runs through the harness, 60 records, correct schema, only assigned accessions |
| Label correctness | 35 | Matches expert review after adjudication; a defensible abstention on an ambiguous record counts as correct |
| Evidence and rationale quality | 20 | Verbatim quotes that support the label; rationales in your own words; `source_step` honest |
| Trap handling | 15 | Study-focus, keyword-only, cell-line-vs-patient, and conflict cases handled correctly (triple weight) |
| Calibration & adjudication | 10 | Independent calibration labeling respected; pre-harness commit present; adjudication argued from quotes |
| Curation log and reflection | 10 | Log complete for all ten; reflection proposes one implementable improvement |

Two unusual scoring notes:

- **False assertions are the cardinal error.** A confidently wrong `asserted` loses more than a wrongly cautious `unknown` (−2 vs −1 within correctness) — the same asymmetry the product is built on.
- **Finding a real extraction bug is bonus-eligible:** up to +5 per confirmed, written-up case (max +10).

## Timeline (2026)

| Date | Due |
| --- | --- |
| **Mon Nov 24** | 2 calibration accessions (12 records) committed & PR'd — independently; no discussing them |
| **Fri Dec 5** | All 10 accessions: three files in your PR |
| **Fri Dec 12** | Adjudication done; final labels merged; benchmark v1.0 tagged |
| January | Holdout scored at final evaluation |

## AI-use policy

You may use an AI assistant to understand terminology (what RIME is, what an SDRF contains) and to check JSON syntax. You may **not** have an AI produce labels or rationales: the value of this benchmark is that it is *human* ground truth — an AI-labeled benchmark scoring an AI extractor is circular and scientifically worthless. Every rationale must be writable from quotes you located yourself; expect live walk-through spot-checks. Declare any AI use in your curation log.

**Questions** go in the team channel so everyone sees the answer; genuinely ambiguous records are worth raising there — they often become the best benchmark cases.
