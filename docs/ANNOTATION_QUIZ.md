# pxEnrich Annotation Mini-Quiz

18 realistic labeling scenarios. Work through them **after** reading `BIOLOGY_PRIMER.md` and **before** (or early in) your unique-accession labeling. Each answer is hidden — commit to your own answer first, then click. Aim for 16/18; anything you miss, re-read that primer section.

These are the *reasoning patterns* behind your six fields — the snippets are realistic but invented, so none of them leak answers to your assigned accessions.

---

**Q1.** A PRIDE description says: *"HER2 signaling in breast cancer."* Can you label the cohort `her2_status = positive`?
<details><summary>Answer</summary>

**No — `abstained`.** Relevant HER2 evidence exists, but it establishes study focus rather than cohort status. If no HER2-related evidence existed anywhere in the completed evidence trail, the correct state would be `unknown`.
</details>

**Q2.** One unified study cohort contains 15 TNBC tumors and 10 luminal tumors that are analyzed together. What is `subtype` at dataset scope?
<details><summary>Answer</summary>

**`mixed`** — and your quote should cite the enumeration. If the study instead keeps subtype-specific groups as structurally distinct sub-cohorts, preserve them at `cohort_subset` scope rather than forcing a dataset-level mixed label.
</details>

**Q3.** *"MCF-7 cells were cultured and treated with tamoxifen."* What are `organism_context`, `sample_type`, and `disease_context`?
<details><summary>Answer</summary>

`organism_context` = **asserted: the cell line's name (MCF-7)** — in the current schema this field answers "patient-derived, cell line, animal model, mixed, or non-disease system?", and a named human cell line is labeled by its name; `sample_type` = **cell line**; `disease_context` = **breast cancer** (MCF-7 is a breast-cancer line). "Human" alone is not the answer: **Homo sapiens does not mean patient-derived.**
</details>

**Q4.** The title says *"Proteomic analysis of ER+ breast tumors (n=32)."* What is `er_status`, and what's your evidence?
<details><summary>Answer</summary>

**`asserted: positive`**, quote = "ER+ breast tumors (n=32)", source step = wherever you read it (title = the repository record). This is the clean case — explicit, cohort-level.
</details>

**Q5.** A project studies a new peptide-fragmentation method using an authenticated MCF-7 breast-cancer cell line. What should `disease_context` capture?
<details><summary>Answer</summary>

`disease_context` = **breast carcinoma** because it describes the biological disease origin of the analyzed cells. The study purpose is **method development**, which is a separate study-level concept and should not erase the sample's disease identity.
</details>

**Q6.** A confirmed breast-cancer cohort is explicitly reported as *ER−/PR−/HER2−*. What may you assign to `subtype`, and what may you not infer?
<details><summary>Answer</summary>

You may deterministically assign **`subtype = TNBC`** because triple-negative breast cancer is defined by explicit negativity for ER, PR, and HER2. You may **not** infer `Basal-like`; that is an intrinsic gene-expression subtype. If any of the three receptor results is missing, pending, equivocal, or unresolved, do not assign TNBC.
</details>

**Q7.** The species field says *Homo sapiens*; the description says *"BT-474 xenograft tumors grown in NSG mice."* Is this a conflict?
<details><summary>Answer</summary>

**No.** Human-origin material in a mouse host is one compatible system, not a contradiction. In the current schema: `organism_context` = **mixed ("human and animal")**, `sample_type` = **xenograft (CDX)**, with the human-origin/mouse-host picture spelled out in the rationale. It becomes `conflicting` only if two sources make mutually exclusive claims about the same property at the same sample/timepoint.
</details>

**Q8.** The publication's Table 1 lists per-patient receptor status; the repository page says nothing about receptors. Your deepest source step and what goes in `source_step`?
<details><summary>Answer</summary>

Step **5** (linked publication) — and recording that honestly matters: it tells the team this field *cannot* be extracted from repository metadata alone.
</details>

**Q9.** *"Plasma samples from 40 breast cancer patients and 20 healthy controls."* What can you assign to `sample_type` and `organism_context`?
<details><summary>Answer</summary>

`sample_type` = **plasma**; `organism_context` = **asserted: patient-derived** — directly collected human patient material is exactly what that value means in the current schema. The cancer/healthy cohort composition belongs in `disease_context`/rationale at the appropriate scope.
</details>

**Q10.** You searched ProteomeCentral, the PRIDE page, the API, and the SDRF; nothing states HER2 status; there is no linked publication. `her2_status`?
<details><summary>Answer</summary>

**`unknown`**, `evidence_quote: null`, rationale: "searched through step 4 (SDRF); no linked publication." No relevant HER2-status evidence was found. Do not convert absence into a guessed label.
</details>

**Q11.** A breast-cancer cohort is reported as **HER2 IHC 2+ with negative/non-amplified ISH**, but the words "HER2-low" never appear. How do you label `her2_status`?
<details><summary>Answer</summary>

**`asserted: low`**. The locked deterministic mapping is: **IHC 1+ → HER2-low; IHC 2+ with negative/non-amplified ISH/FISH → HER2-low.** An unresolved/equivocal IHC 2+ result without the negative ISH/FISH result is not enough.
</details>

**Q12.** A dataset studies *"tamoxifen resistance"* with no receptor status stated anywhere. A teammate argues: "tamoxifen targets ER, so the cohort must be ER-positive." Do you agree?
<details><summary>Answer</summary>

**No — that's inference, not evidence.** Biologically plausible (tamoxifen is given to ER+ patients), but the source doesn't state it, and resistant models are sometimes ER-altered. `abstained`, because relevant endocrine-treatment evidence exists but it is insufficient to establish the cohort's ER status. Plausible-but-unsupported is exactly the error class this benchmark exists to catch.
</details>

**Q13.** The engine's harness run disagrees with your label: you said `mixed`, it asserted `TNBC`, and your quote enumerates three subtypes with counts. What do you do?
<details><summary>Answer</summary>

**Keep your evidence-backed label** — and file a Form 2 engine-disagreement report (bug-bounty eligible). Your annotation should already have been committed **before** the first harness run. Do not change a label merely to agree with the engine; any later adjudication must be a separate documented commit.
</details>

**Q14.** A link in your evidence trail resolves, but the page content doesn't actually contain the claim you want to cite. Can you use it?
<details><summary>Answer</summary>

**No.** A source existing is not the same as its content being verified — same rule for your labels as for this primer's own links. Find text that states the claim, or label the honest abstention.
</details>


**Q15.** The manuscript says `Sample_08` is ER-negative at baseline; the PRIDE SDRF says the same `Sample_08` is ER-positive at baseline. What status?
<details><summary>Answer</summary>

**`conflicting`.** Same entity, same property, same biological/temporal scope, mutually exclusive values. Quote both sources and withhold a single hard ER value until adjudication.
</details>

**Q16.** A PDX proteomics sample is described as "human breast tumor tissue propagated in mice." Can `sample_type` contain more than one compatible concept?
<details><summary>Answer</summary>

**Both concepts are true** — the material is tumor tissue *and* the model is a PDX — but the current `sample_type` field takes one value: **use the most specific model term the source states (`PDX`)**, and record the broader picture ("human tumor tissue, mouse host") in the rationale. Flattening toward the *most* specific term preserves the most information.
</details>

**Q17.** A record says only "tumor tissue" with no statement about how it was obtained. Can you infer that it is patient-derived?
<details><summary>Answer</summary>

**No.** Tumor tissue can come from a primary patient specimen, a xenograft, or another model. “Tumor tissue” alone is insufficient to establish patient-derived status.
</details>

**Q18.** A breast-cancer organoid dataset lists `organism = Homo sapiens`. Where does "organoid" belong?
<details><summary>Answer</summary>

**"Organoid" belongs in `sample_type`** — it describes the experimental model/material. For `organism_context`, ask the field's own question (patient-derived / cell line / animal model / mixed?): a patient-tumor-derived organoid is patient-derived material grown in the lab — say exactly that in the rationale, and label the most honest value the evidence supports (`patient-derived` when the patient origin is stated; `unknown` when it isn't).
</details>

---

*Answer pattern summary: (1) Label what the source states, at the scope it states it. (2) Use only the locked deterministic mappings on the rules card. (3) Keep disease origin, material/model, and study intent as separate concepts — and answer each field's own question in the current schema's vocabulary. (4) Use `unknown`, `mixed`, `conflicting`, and `abstained` deliberately rather than interchangeably. (5) Never let one source silently override another when they make same-scope contradictory claims.*
