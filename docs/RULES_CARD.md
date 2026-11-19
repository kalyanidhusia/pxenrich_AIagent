# pxEnrich rules card — keep this open while labeling

One page. Everything here also appears, with explanation, in the primer and assignment. When documents seem to disagree, this card and the assignment are authoritative; flag the discrepancy in the team channel.

## The decision ladder (run every field through it, top to bottom)

```
Q1  Does the field apply to this record at all?            no  → not_evaluable
Q2  Did the evidence trail (steps 1–5) yield any
    relevant evidence for this field?                      no  → unknown
Q3  Do two sources make mutually exclusive claims about
    the SAME entity, property, and scope?                  yes → conflicting (quote both)
Q4  Does the cohort deliberately span several values
    (multi-subtype design, pooled material)?               yes → mixed
Q5  Does a source state the value for the cohort —
    or does a locked mapping below apply?                  yes → asserted
                                                           no  → abstained
```

- `unknown` → `"evidence_quote": null` + deepest step searched in the rationale.
- `abstained` = evidence exists but can't support a cohort-level value (classic: study is *about* HER2; cohort HER2 status unstated).

## Locked deterministic mappings (the ONLY permitted inferences)

1. **TNBC:** explicit ER− **and** PR− **and** HER2− in confirmed breast cancer → `subtype = TNBC` (rationale must say "derived"). Any of the three missing/pending/equivocal → no TNBC.
2. **HER2-low:** IHC 1+ → `low`. IHC 2+ **with** negative/non-amplified ISH/FISH → `low`. IHC 2+ alone → not low (abstain).

## Forbidden inferences (graded traps)

- Topic ≠ status: "HER2 RIME study" does not make the cohort HER2-positive.
- HER2-positive ≠ HER2-enriched (clinical status vs expression subtype).
- TNBC ≠ Basal-like.
- ER+/HER2− alone ≠ Luminal A or B.
- Keywords alone ≠ disease context.
- "Tumor tissue" alone ≠ patient-derived.
- Tamoxifen/endocrine therapy ≠ ER-positive.

## `organism_context` — current schema vocabulary (match the engine)

Use the value the implemented system uses (this is what the harness scores against):

| The material is… | status / value |
|---|---|
| Patient tissue/fluid, directly collected | `asserted` / `patient-derived` |
| A named human cell line (MCF-7, MDA-MB-231, T47D, SK-BR-3…) | `asserted` / the line's name |
| An animal model (4T1, MMTV-PyMT, mouse/rat tissue) | `asserted` / `animal model` |
| Human material **in** an animal host (xenograft, PDX), or patients + models together | `mixed` / `human and animal` |
| A non-disease system (e.g., E. coli method work) | `asserted` / `non-disease` |

- Human origin + mouse host (PDX/xenograft) is **compatible, not `conflicting`** — reserve `conflicting` for same-scope contradictions (e.g., SDRF says ER+ where the paper says ER− for the same sample).
- Organoid/PDX/cell-line identity also belongs in `sample_type` (use the most specific model term the source states: `PDX` beats `tumor tissue`); explain the full picture in the rationale.

## Evidence rules

- Verbatim quotes only; `source_step` honest; stop drilling when decided, but always read the full repo record (step 2).
- One source never silently overrides another: same-scope disagreement = `conflicting` until adjudicated.
- **Commit labels before your first harness run.** Post-harness label changes = separate commit + documented reason (or a Form 2 bug report if the engine is wrong).
- No AI-produced labels or rationales, ever. (AI for terminology/JSON syntax: fine, declared in your log.)

**Golden rule: "we don't know" is often the right answer — documented, it scores full marks. A guessed assertion is the cardinal error.**
