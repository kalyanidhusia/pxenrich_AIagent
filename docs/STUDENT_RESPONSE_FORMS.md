# Student response forms — how to report, in a fixed structure

Everything you hand in on this project uses one of the four forms below.
Structured responses are not bureaucracy: they are what lets your work go
directly into a scientific benchmark, a CI pipeline, and (with you as
co-author) a journal manuscript. Free-text emails get lost; forms become data.

All files live in **your** submission folder: `submissions/<your-folder>/`.
Copy the template, fill every field; write `n/a` rather than deleting a field.

---

## Form 1 — Curation log entry (one per accession)

File: `curation_log_<netid>.md` — append one entry per accession, as you go.

```markdown
### PXD0XXXXX
- deepest_step_reached: 3            # 1=ProteomeCentral 2=repo page 3=PRIDE API 4=SDRF 5=publication
- time_spent_min: 25
- fields_decided_at: {disease_context: 1, organism_context: 2, sample_type: 2, subtype: 5, er_status: 5, her2_status: unknown}
- ambiguities: "Title says 'breast tumor samples' but SDRF lists two cell lines alongside tissue."
- changed_my_mind: "Initially labeled subtype=TNBC from the title; publication Table 1 shows a mixed cohort → mixed."
- ai_use: "Asked an AI what an SDRF 'characteristics[sampling site]' column means. No labels or rationales AI-generated."
```

**Example (filled):**
```markdown
### PXD052290
- deepest_step_reached: 2
- time_spent_min: 15
- fields_decided_at: {disease_context: 1, organism_context: 2, sample_type: 2, subtype: 2, er_status: 2, her2_status: unknown}
- ambiguities: "none"
- changed_my_mind: "no"
- ai_use: "none"
```

## Form 2 — Engine-disagreement report (bug-bounty eligible, +5 each)

File: `bug_reports_<netid>.md` — one entry per confirmed disagreement where
you believe **your label is right and the engine is wrong**. This is the most
valuable thing you can produce; it goes into the paper's error analysis.

```markdown
### BUG-<netid>-01
- accession: PXD0XXXXX
- field: subtype
- engine_said: "asserted: TNBC"
- my_label: "mixed"
- my_evidence_quote: "tumors spanning TNBC (n=12), luminal A (n=9), and HER2-enriched (n=5) subtypes"
- source_step: 5
- why_the_engine_is_wrong: "The rule matches 'TNBC' in the title but the cohort enumerates three subtypes; cohort-level assertion requires all samples to share the subtype."
- suggested_rule_fix (optional): "If multiple subtype terms co-occur with per-group counts, emit mixed."
```

## Form 3 — Adjudication record (calibration accessions only)

File: `adjudication_<netid>.md` — after agreement scores are returned, one
entry per calibration item where you disagreed with the group consensus.

```markdown
### PXD0XXXXX · her2_status
- my_label: "asserted: low"
- consensus: "unknown"
- my_quote: "..."            # the verbatim text you relied on
- their_reasoning_as_I_understand_it: "..."
- resolution: kept_mine | adopted_consensus | escalated
- final_rationale: "One sentence arguing from quotes, not memory."
```

## Form 4 — Weekly check-in (every Friday, 3 questions, ≤5 sentences total)

Posted as a comment on your open PR (or emailed if no PR yet).

```markdown
WEEK OF: 2026-11-21
1. DONE: "Calibration accessions labeled and committed (12 records)."
2. STUCK: "PXD0XXXXX — can't tell if 'mammary epithelial cells' counts as cell line or tissue."  # or "nothing"
3. NEXT: "4 of my 8 unique accessions by Tuesday."
```

---

### Rules that apply to every form

1. **Quotes are verbatim** — copy-paste, never paraphrase. A label without a
   quote (or, for `unknown`, without the depth searched) doesn't count.
2. **Commit before you compare.** Your labels must be committed to git
   *before* you first run `tests/run_benchmark.py` on them. The git history
   is our proof that the reference standard was made independently of the
   engine. After the first run you may fix *format* errors freely; changing
   a *label* after seeing the engine's output requires a Form 2 or a line in
   Form 1 `changed_my_mind` explaining the evidence (not the engine) that
   changed it.
3. **Disagreeing is data.** With the engine, with a classmate, with the
   consensus — a well-quoted disagreement is worth more than a quiet match.
4. **"We don't know" is often correct.** An `unknown` with the search depth
   documented scores full marks; a guessed assertion scores zero and fails
   the build.
