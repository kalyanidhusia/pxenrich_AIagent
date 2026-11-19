# Instructor notes — not student-facing

Material moved out of the student documents in the v4 packaging pass (2026-11-19), per external (non-biologist) packet review.

## Schema roadmap: `organism_context` split (post-freeze)

The v3 biology review concluded that `organism_context` ideally represents **biological taxonomic origin**, with patient-derived status, host organism, and experimental model stored as separate orthogonal fields (or a multi-label `sample_type`). **This is NOT implemented.** The current engine (`pxenrich/extraction.py`, rule:v0.1) emits: `patient-derived` / named human cell line / `animal model (…)` / `mixed: human and animal model` / `non-disease experimental system (…)`, and the example benchmark records use that vocabulary.

Decision of record (2026-11-19): **v4 student materials teach the implemented vocabulary**, so student labels remain comparable to engine output through the harness. The taxonomic split is scheduled as a versioned schema change *after* benchmark v1.0 freeze, with:
- new fields (`taxon`, `host_organism`, `experimental_model`, `patient_derived`) or multi-label `sample_type`;
- a migration script for existing benchmark records;
- a rule-version bump and full benchmark re-run.

The v3 primer/quiz briefly taught the future taxonomic convention; v4 reverted that teaching. If any calibration labels were made under the v3 convention (taxonomic values like "Homo sapiens" in `organism_context`), normalize them during adjudication and note it in the adjudication record.

## Manual link checks still open (from the resource report + packet review)

1. NCI Dictionary /def/ pages render via JavaScript — click-verify each slug in a browser (esp. `mass-spectrometry`, `proteomics`; no `her2-low` slug confirmed).
2. Komen "Under the Microscope" direct episode URLs — the hub buries them in playlists; capture direct links for the *Estrogen Receptor* and *HER2* episodes and replace the hub reference in primer §3.
3. Sebastian 2023 Table 1 cell-by-cell check (it's an image) before citing specific cells in the manuscript.

## Known content caveat taught deliberately

The NCI biomarker page conflates "basal-like (also called triple-negative)" and lists HER2-low as a subtype row. The primer now carries a caution box at the point of assignment and uses the conflation as a teaching moment rather than hiding it.

## Document versioning

v4 (2026-11-19) = packaging/consistency pass: addenda merged, real 2026 dates, plain-text ladder, self-check answers, worked example, rules card, schema teaching aligned to implemented engine. **No benchmark-semantics changes.** Source review documents: the external packet review (full 8,200-word version to be added to project knowledge when received) and `Biology primer resources for CS students.md` (instructor resource report).
