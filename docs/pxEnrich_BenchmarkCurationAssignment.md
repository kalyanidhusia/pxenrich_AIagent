# pxEnrich Benchmark Curation Assignment

Oct 12, 2026 · @Kate

## Why you are building a benchmark

Your job in this assignment is to create ground truth: a set of expert-checkable labels that says what the correct answer is for real public datasets, so the pxEnrich extraction engine can be scored against it. Every serious AI product is graded this way — the 18-record reference benchmark in the project brief exists for exactly this purpose, and your records will extend it.

A benchmark record says, for one dataset and one field (for example, HER2 status of PXD061456): what the correct value is, or that the correct answer is *unknown*, *mixed*, *conflicting*, or *deliberately not labeled*. The hardest and most valuable part of this assignment is learning that **"we don't know" is often the right answer**, and that writing down *why* is what makes a label usable.

What you practice here: navigating real repository records (ProteomeCentral → PRIDE), reading scientific metadata critically, separating what a study *is about* from what its cohort *is*, and producing machine-readable curation with provenance. These are the skills the Evaluation/QA role runs on for the rest of the semester.

## Background: working your way to PRIDE

Start at the top of the stack and drill down. For each assigned accession, visit the sources **in this order** and record how far you had to go — that depth is part of your curation log.

| Step | Source | What you get there |
| --- | --- | --- |
| 1 | [ProteomeCentral](https://proteomecentral.proteomexchange.org/) — search, or open `cgi/GetDataset?ID=PXD…` | The cross-repository record: title, species, instrument, host repository, publication links |
| 2 | The host repository page — for PRIDE: `www.ebi.ac.uk/pride/archive/projects/PXD…` | Full description, submitter keywords, sample protocol, data protocol, lab head, file list |
| 3 | [PRIDE REST API v3](https://www.ebi.ac.uk/pride/ws/archive/v3/webjars/swagger-ui/index.html) — `GET /projects/{accession}` and `/projects/{accession}/files` | The same record as machine-readable JSON; the files list tells you whether an SDRF sample-metadata file exists |
| 4 | The SDRF file (when listed) | Per-sample annotations — often the only place disease, subtype, or organism is stated at sample level |
| 5 | The linked publication (PubMed / DOI) | Cohort details the submitter never typed into the repository record |

Two rules about sources:

1. **Label only from what a source states.** Your biology knowledge tells you where to look; the label must still point at text that exists in step 1–5. If no source states it, the answer is `unknown` — not your best guess.
2. **Note the shallowest step that decided each label.** "Subtype was in the title" and "subtype only appears in Table 1 of the paper" are very different findings, and the product team needs to know which fields live where.

## The task

You will be assigned **10 ProteomeXchange accessions** (breast-cancer-related, drawn from the pxEnrich index). Three of the ten are shared with a partner — you must not discuss those three until both of you have submitted (see the agreement section).

For **each** accession, produce one benchmark record for **each of these 6 fields** (60 records total):

| Field | The question it answers |
| --- | --- |
| `disease_context` | Is this actually a breast-cancer study, or does the term only appear in keywords? |
| `organism_context` | Patient-derived human material, human cell line, animal model, mixed, or a non-disease system? |
| `sample_type` | Tumor/clinical tissue, plasma, blood, urine, cell line, PDX, organoid, EV fraction…? |
| `subtype` | TNBC, luminal A/B, HER2-enriched, basal-like — or mixed cohort, or not stated? |
| `er_status` | Does a source state the cohort's ER status? |
| `her2_status` | Does a source state the cohort's HER2 status (positive / negative / low)? |

Each record is one JSON line in the repo's benchmark format (`tests/benchmark/benchmark_schema.json`):

```markdown
{"accession": "PXD052290", "field": "er_status",
 "expected_status": "asserted", "expected_value": "positive", "value_match": "contains",
 "rationale": "Title states 'NF1-depleted ER+ breast cancers'; applies to the whole cohort.",
 "source_step": 1, "evidence_quote": "NF1-depleted ER+ breast cancers",
 "set": "regression", "curator": "your-netid"}
```

`expected_status` takes exactly one of six values — this vocabulary is the heart of the assignment:

| Status | Use when… |
| --- | --- |
| `asserted` | A source states the value for the dataset's cohort |
| `unknown` | No source says anything either way |
| `mixed` | The cohort deliberately spans several values (e.g. a multi-subtype comparison) |
| `conflicting` | Two sources disagree (e.g. species field vs SDRF) |
| `abstained` | Evidence exists but does not support a cohort-level claim — the classic case: the study is *about* a biomarker without stating cohort status |
| `not_evaluable` | The field does not apply to this record at all |

## Curation workflow

For each accession, work one field at a time:

1. Read the sources in the step 1–5 order. Stop drilling once the field is decided, but always read at least the full repository record (step 2).
2. Walk the decision ladder below from the top. The first "yes" (or the final fall-through) is your status.
3. Write the record: status, value (only for `asserted`/`mixed`), a **verbatim quote** of the deciding text in `evidence_quote`, the `source_step` it came from, and a one-sentence `rationale` in your own words.
4. If you changed your mind while reading deeper sources, say so in the rationale — those reversals are the most instructive records in the whole benchmark.

&#91;embedded content: status decision ladder · 5 questions, 6 outcomes\]

Run every field through the ladder; the first question that answers "yes" ends it, and falling off the bottom means `unknown`.

**Known traps — these are graded specifically:**

- *Topic is not status.* "HER2 RIME experiment" studies HER2; it does not say the samples are HER2-positive. Asserting a receptor status from a pulldown target is the error this product exists to avoid.
- *Keywords are weak evidence.* "breast cancer" appearing only in submitter keywords (e.g. an E. coli biophysics study tagged with it) does not make it a breast-cancer study.
- *TNBC implies ER−, PR−, HER2−* at dataset scope — a derived assertion is fine, but your rationale must say it is derived.
- *Cell line ≠ patient.* MCF-7, MDA-MB-231, T47D, SK-BR-3 are human but in vitro; 4T1 and MMTV-PyMT are mouse. A study can be both (patient tissue plus lines) — then organism context is mixed or dual, not one or the other.
- *Species field vs SDRF.* When they disagree, the answer is `conflicting`, and your quote cites both.

## Deliverables and self-validation

Submit three files, named with your NetID:

1. `benchmark_<netid>.jsonl` — your 60 records, one JSON object per line, in the repo's schema.
2. `curation_log_<netid>.md` — one short entry per accession: the deepest source step you reached, how long it took, anything ambiguous, and any record where you changed your mind.
3. `reflection_<netid>.md` — half a page: which field was hardest to label and why, and one concrete improvement you would make to the extraction rules or the status vocabulary.

**Validate before you submit.** Your file must run cleanly through the project harness:

```markdown
# from the pxenrich-product repo root
python -m pxenrich.ingest.run_ingest --seed          # build the index once
python tests/run_benchmark.py path/to/benchmark_<netid>.jsonl
```

The harness checks your JSON is well-formed and scores the current extraction engine against *your* labels. Read its failure list before submitting: a "failure" can mean the engine is wrong (good — you found a bug; note it in your log) or that your label is wrong (fix it). Deciding which is which is the exercise. A file that does not parse, or that labels accessions outside your assignment, loses the format marks automatically.

## Double-coding, adjudication, and the holdout

Three of your ten accessions are shared with a partner, curated **independently** — no discussion of those three datasets (in person, chat, or shared notes) until both files are submitted. After submission:

1. I compute per-field agreement on the shared records (simple percent agreement; with the full class pool we will also report Cohen's kappa in the evaluation report).
2. You and your partner meet for 30 minutes to **adjudicate** every disagreement: argue from quotes, not from memory, and agree a final label or escalate to me with both rationales written down.
3. Adjudicated records enter the shared class benchmark; unresolved escalations become my expert-review items.

Disagreeing with your partner does **not** cost marks — honest disagreement on genuinely ambiguous records is data, and some records are chosen because they are ambiguous. What costs marks is a disagreement where one side has no quote behind it.

**Holdout freeze:** after adjudication I will move a random ≈20% of the class benchmark to `"set": "holdout"`. Those records are locked and never used while the team tunes extraction rules; they are scored once, at final evaluation in January. Do not look at which records were chosen.

## Grading (100 points)

| Component | Points | What earns full marks |
| --- | --- | --- |
| Format validity | 10 | File parses, runs through the harness, all 60 records present, correct schema fields, only assigned accessions |
| Label correctness | 35 | Labels match my expert review after adjudication; a defensible abstention on an ambiguous record counts as correct |
| Evidence and rationale quality | 20 | Verbatim quotes that actually support the label; rationales in your own words; `source_step` honest |
| Trap handling | 15 | The study-focus, keyword-only, cell-line-vs-patient, and conflict cases in your set are handled correctly — each trap record is worth triple an ordinary record here |
| Double-coding and adjudication | 10 | Independent curation respected; adjudication argued from quotes; escalations written up properly |
| Curation log and reflection | 10 | Log complete for all ten accessions; reflection proposes one concrete, implementable improvement |

Two scoring notes, because they are unusual:

- **False assertions are the cardinal error.** A confidently wrong `asserted` label loses more than a wrongly cautious `unknown` (−2 vs −1 within the correctness component) — exactly the asymmetry the product itself is built around.
- **Finding a real extraction bug is bonus-eligible:** up to +5 for each confirmed, written-up case (max +10) where the engine mislabels and your benchmark record proves it.

## Timeline, submission, and AI-use policy

This assignment sits in the **data foundation** milestone (Oct 19 – Nov 1) of the project timeline.

| Date | What is due |
| --- | --- |
| Mon Oct 26 | Accession assignments distributed; kickoff walkthrough of one record together |
| Fri Nov 02 | Checkpoint: first 2 accessions (12 records) submitted for early feedback — ungraded |
| Wed Nov 09 | All three files due (pull request to the team repo, `tests/benchmark/submissions/`) |
| Fri Nov 16 | Adjudication meetings done; final labels merged |
| Sun Nov 30 | Holdout frozen; class benchmark tagged in the repo |

**AI-use policy.** You may use an AI assistant to understand terminology (what RIME is, what an SDRF file contains) and to check JSON syntax. You may **not** have an AI produce the labels or rationales: the entire value of this benchmark is that it is *human* ground truth — an AI-labeled benchmark scoring an AI extractor is circular and scientifically worthless. Every rationale must be writable from quotes you located yourself; I will spot-check by asking you to walk me through records live. Declare any AI use in your curation log.

**Questions** go in the team channel so everyone sees the answer; genuinely ambiguous records are worth raising there — they often become the best benchmark cases.
