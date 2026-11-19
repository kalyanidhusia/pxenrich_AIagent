# Worked example — one accession, all six fields, start to finish

This is **PXD052290**, from the public example set (`tests/benchmark/example_records.jsonl`), so it is **not** in anyone's assignment and nothing here leaks your answers. Follow along with the real record: https://proteomecentral.proteomexchange.org/cgi/GetDataset?ID=PXD052290

## What the sources say

**Step 1 — ProteomeCentral record:**
> Title: *"NF1-depleted ER+ breast cancers are differentially sensitive to CDK4/6 inhibitors"*
> Species: Homo sapiens · Repository: PRIDE · Publication linked (PMID 40864686)

**Step 2 — PRIDE description (the full read is mandatory):**
> *"Loss of neurofibromin (NF1low) is linked to endocrine therapy resistance in about 20% of early-stage **ER+/HER2-negative breast cancers**. … NF1 silencing increased ER binding at CCND1 … **durable tumor regression in ER+ NF1low patient-derived xenografts**. In **neoadjuvant treatment**, NF1low tumors on anastrozole were markedly sensitive to added palbociclib."*

Reading notes a curator would jot (this becomes your Form 1 log entry): title gives ER+ directly; description adds HER2-negative, and reveals the material spans **patient tumors** (neoadjuvant treatment), **cells** (NF1 silencing experiments), and **PDX** (mouse host). Deepest step needed: 2. The publication (step 5) exists but wasn't needed for any field below.

## The six finished records

```json
{"accession": "PXD052290", "field": "disease_context", "expected_status": "asserted", "expected_value": "breast cancer", "value_match": "contains", "rationale": "Study investigates therapy response in breast cancers; disease identity of the material is breast cancer throughout.", "source_step": 1, "evidence_quote": "NF1-depleted ER+ breast cancers", "set": "regression", "curator": "worked-example"}
{"accession": "PXD052290", "field": "er_status", "expected_status": "asserted", "expected_value": "positive", "value_match": "contains", "rationale": "Title states ER+ for the studied cancers; cohort-level.", "source_step": 1, "evidence_quote": "ER+ breast cancers", "set": "regression", "curator": "worked-example"}
{"accession": "PXD052290", "field": "her2_status", "expected_status": "asserted", "expected_value": "negative", "value_match": "contains", "rationale": "Description defines the studied population as ER+/HER2-negative.", "source_step": 2, "evidence_quote": "early-stage ER+/HER2-negative breast cancers", "set": "regression", "curator": "worked-example"}
{"accession": "PXD052290", "field": "subtype", "expected_status": "abstained", "expected_value": null, "value_match": "contains", "rationale": "Receptor profile (ER+/HER2-) is stated but no intrinsic subtype is; ER+/HER2- alone cannot be mapped to Luminal A or B (forbidden inference).", "source_step": 2, "evidence_quote": "early-stage ER+/HER2-negative breast cancers", "set": "regression", "curator": "worked-example"}
{"accession": "PXD052290", "field": "organism_context", "expected_status": "mixed", "expected_value": "human and animal", "value_match": "contains", "rationale": "Material spans patient tumors (neoadjuvant), human cell experiments, and PDX in mouse hosts; human-origin + mouse host is compatible, and the span makes it mixed.", "source_step": 2, "evidence_quote": "durable tumor regression in ER+ NF1low patient-derived xenografts. In neoadjuvant treatment, NF1low tumors", "set": "regression", "curator": "worked-example"}
{"accession": "PXD052290", "field": "sample_type", "expected_status": "mixed", "expected_value": "mixed", "value_match": "contains", "rationale": "Tumor tissue (patients), cultured cells, and PDX material all analyzed; no single material label fits; components enumerated here.", "source_step": 2, "evidence_quote": "NF1 silencing increased ER binding at CCND1 … patient-derived xenografts … neoadjuvant treatment", "set": "regression", "curator": "worked-example"}
```

## Why each decision went the way it did (the ladder in action)

| Field | Ladder exit | The reasoning in one line |
|---|---|---|
| `disease_context` | Q5 → asserted | Breast cancer is the disease identity of the material, stated at step 1 — not merely a keyword. |
| `er_status` | Q5 → asserted | Explicit "ER+" for the studied cancers. The clean case. |
| `her2_status` | Q5 → asserted | Explicit "HER2-negative" at step 2 — one step deeper than ER. That depth difference is *why* `source_step` exists. |
| `subtype` | Q5 → **abstained** | Evidence exists (the receptor profile) but no intrinsic subtype is stated, and ER+/HER2− → Luminal is a **forbidden inference**. This is the record most students get wrong. |
| `organism_context` | Q4 → **mixed** | Patients + cells + PDX. Note what this is *not*: not `conflicting` (human origin + mouse host is compatible), and not `patient-derived` alone (that ignores the models). |
| `sample_type` | Q4 → **mixed** | Three materials, deliberately. The rationale enumerates them — that's what makes a `mixed` label usable. |

## What this example teaches

1. Two assertions came from the title, two required the description — **"always read step 2 in full" is not a formality.**
2. The most valuable record is the **abstention**: a weaker curator writes `subtype = luminal` and creates exactly the plausible-but-unsupported label this benchmark exists to catch.
3. `mixed` with an enumerating rationale beats a falsely tidy single value, twice in one accession.
4. Every quote is verbatim and findable with Ctrl-F on the source page. If yours isn't, it isn't evidence.

Now open your own first accession and do exactly this, six times. The rules card (`RULES_CARD.md`) stays open beside you.
