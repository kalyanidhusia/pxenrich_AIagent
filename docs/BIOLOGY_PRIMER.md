# pxEnrich Biology Primer — for the curation team

**Who this is for:** CS students labeling the pxEnrich benchmark. No biology background assumed.
**Time:** ~75 minutes for the required track (±15 depending how fast you take the PRIDE tour). Optional-depth links are clearly marked — explore if curious, skip freely.
**How to use it:** each section maps to a labeling decision you will actually make. Read the section, absorb the labeling rule, try the self-checks (answers hidden under each — commit to yours first). Then take the full quiz in `ANNOTATION_QUIZ.md`, read `WORKED_EXAMPLE.md`, and keep `RULES_CARD.md` open while labeling. The five uncertainty states (`unknown / mixed / conflicting / abstained / not_evaluable`) are introduced *where you first need them* and condensed on the rules card — don't memorize them now.

> **One meta-lesson before you start.** Every link below carries a verification status: *fetched OK* (content machine-confirmed), *JS-rendered* (link resolves; text only confirmed in a browser). We show the flags instead of hiding them because it's the discipline you're learning: **a source existing is not the same as its content being verified.** A dead or wrong link is a finding — report it.

---

## 1 · What disease does the material come from? → `disease_context`

**The decision:** what is the disease identity of the biological material being measured?

**Required (~10 min):**
- [What Is Breast Cancer?](https://www.cancer.gov/types/breast/what-is-breast-cancer) — NCI, ~2-min read with anatomy figure *(fetched OK)*
- [MedlinePlus: Breast Cancer](https://medlineplus.gov/breastcancer.html) — NIH topic page, skim *(fetched OK)*

**What you need to know:** `disease_context` describes the disease origin of the *sample*, which is separate from the *purpose of the experiment*. A breast-cancer cell line is still breast-cancer-derived material even when the study uses it to test a lab method.

> **For pxEnrich:** keep biological identity separate from study intent. An authenticated breast-cancer cell line such as MCF-7 supports `disease_context = breast cancer` even in a method-development study. `unknown` is for when the disease origin itself can't be established. But **keywords alone are weak evidence**: "breast cancer" appearing only in submitter tags does not make it a breast-cancer study — look for the disease identity in the title, description, or sample metadata.

**Real example:**
> *Source says:* "Optimization of phosphopeptide enrichment, demonstrated in MCF-7 cells."
> `disease_context` → **breast cancer** (MCF-7 is a breast-cancer line) · `sample_type` → **cell line** · study purpose (method development) → goes in your rationale, not the disease label.

**Self-check 1.1:** A study mentions BRCA1 (a gene whose mutations raise breast-cancer risk) but uses HeLa cells. Does the BRCA1 mention make the material breast-cancer-derived?
<details><summary>Answer</summary>

**No.** HeLa is a *cervical*-cancer cell line — the material's disease origin is cervical cancer regardless of which gene the study investigates. Gene-of-interest ≠ disease identity of the material.
</details>

**Self-check 1.2:** An E. coli biophysics dataset carries the keyword "breast cancer." What's `disease_context`?
<details><summary>Answer</summary>

Not breast cancer — the material is a **non-disease bacterial system**; the keyword is noise. Depending on the record, `not_evaluable` or `unknown` with the keyword issue noted in your rationale.
</details>

---

## 2 · DNA → RNA → protein (3 minutes, really)

**The decision:** none directly — but every other section leans on this.

**Required (~5 min):**
- [The Central Dogma of Biology](https://dnalc.cshl.edu/resources/3d/central-dogma.html) — Cold Spring Harbor 3D animation, **2:51** *(fetched OK)*
- [How do genes direct the production of proteins?](https://medlineplus.gov/genetics/understanding/howgeneswork/makingprotein) — MedlinePlus, illustrated 3-min read *(fetched OK)*
- Two glossary terms (NHGRI, ~1 min each, *fetched OK*): [Transcription](https://www.genome.gov/genetics-glossary/Transcription) · [Translation](https://www.genome.gov/genetics-glossary/Translation)

**What you need to know, in full:**
```
DNA → RNA → protein

Genomics        asks what sequence exists.
Transcriptomics asks what RNA is expressed.
Proteomics      measures the proteins/peptides actually present.

Related — but NOT equivalent evidence.
```
"Expression" = how much of a gene's product is being made. That's it. That's the section.

**Optional depth:** [HHMI Central Dogma and Genetic Medicine](https://www.biointeractive.org/classroom-resources/central-dogma-and-genetic-medicine) — excellent 50+ min interactive *(fetched OK; not required)*.

---

## 3 · Receptors: ER, PR, HER2 — and HER2-low → `er_status`, `her2_status`

**The decision:** does a source *state* the cohort's receptor status — and for which samples?

**Required (~15 min):**
- [Tests for Breast Cancer Biomarkers](https://www.cancer.gov/types/breast/diagnosis/breast-cancer-biomarker-tests) — NCI, updated Dec 2025: ER, PR, HER2, **HER2-low**, labeled cell figure, subtype table *(fetched OK)* — **read the caution box below first**
- Two short Komen videos (<3 min each): the *"Estrogen Receptor"* and *"HER2 – A Driver of Breast Cancer"* episodes of the "Under the Microscope" series, on the [Komen video hub](https://www.komen.org/support-resources/tools/videos/) *(hub fetched OK — search those two titles on the page; the hub lists ~70 videos and YouTube will autoplay onward, so stop after your two)*

> ⚠️ **Caution for the NCI page (and most clinical websites):** its subtype table says "Basal-like (**also called** triple-negative)" and lists HER2-low as a subtype row. For *our labels* that phrasing is too loose: TNBC and basal-like **overlap but are not equivalent** (§4), and HER2-low is a *receptor status*, not a subtype. Even authoritative sources blur these lines — **which is exactly why your labels can't.** Use the page for what receptors are; use §4 and the rules card for how to label.

**What you need to know:** receptors are proteins on/in tumor cells. Pathologists score them per sample by lab test — IHC (a staining intensity score: 0, 1+, 2+, 3+) sometimes followed by ISH/FISH (a gene-copy test) — as positive/negative, and for HER2 also **low**. Status is never guessed from which genes a paper *discusses*.

> **PR note:** PR (progesterone receptor) appears everywhere alongside ER and HER2, and you need it to understand "triple-negative" (= ER−, PR−, HER2−). **PR is necessary context, but `pr_status` is not one of your six fields.** Learn it; don't label it.

> **For pxEnrich:** assign `er_status` / `her2_status` only when a source explicitly states the status for the relevant cohort/samples, **or** when a locked mapping applies:
> - **HER2-low mapping (locked):** IHC 1+ → `low`; IHC 2+ **with** negative/non-amplified ISH/FISH → `low`. An IHC 2+ without that ISH/FISH result is *not* HER2-low — abstain.
> - A paper that *studies HER2 biology* is not a HER2-positive cohort. Topic ≠ status.
>
> **Your first three uncertainty states, in their natural habitat:**
> - no receptor information anywhere in the trail → `unknown`
> - relevant pathology exists but is borderline/incomplete (IHC 2+, FISH pending) → `abstained`
> - two sources give incompatible values for the same sample/timepoint → `conflicting` (quote both)

**Real example:**
> *Source says:* "HER2 RIME analysis in breast cancer cells." (RIME is a lab technique — Rapid Immunoprecipitation Mass spectrometry of Endogenous proteins — that studies what a protein binds to; the name tells you HER2 is the *study target*.)
> *`her2_status = positive`?* **No — `abstained`:** evidence about HER2 exists, but it establishes study focus, not cohort status.

**Self-check 3.1:** "ER+ tumors (n=24) were profiled" — what's `er_status`, and what's your quote?
<details><summary>Answer</summary>

`asserted: positive`, quote = "ER+ tumors (n=24)" — explicit and cohort-level. The clean case.
</details>

**Self-check 3.2:** "We investigated estrogen signaling" — what's `er_status`?
<details><summary>Answer</summary>

`abstained` — estrogen-related evidence exists but the cohort's ER status is never stated. (If *nothing* ER-relevant appeared anywhere in the trail, it would be `unknown`.)
</details>

---

## 4 · Subtypes: TNBC, luminal A/B, HER2-enriched → `subtype`

**The decision:** TNBC, luminal A, luminal B, HER2-enriched, **mixed**, or not stated?

**Required (~10 min):**
- [Komen: Molecular Subtypes of Breast Cancer](https://www.komen.org/breast-cancer/diagnosis/molecular-subtypes/) — the subtype → receptor-status lookup you'll actually use *(fetched OK)*
- The subtype table on the NCI biomarker page you already read — with the §3 caution in mind

**What you need to know:** the `subtype` field contains two kinds of labels that must not be collapsed:
- **Clinical phenotype:** TNBC — defined directly by explicit ER−/PR−/HER2− status.
- **Intrinsic molecular subtypes:** Luminal A, Luminal B, HER2-enriched, Basal-like — determined by gene-*expression* profiling (classifiers like PAM50), not by receptor tests alone.

> ⚠️ **The most important warning in this primer.** Clinical receptor status and intrinsic subtype are different classification layers.
> - **Locked TNBC rule:** explicit **ER− + PR− + HER2−** in confirmed breast cancer → you may assign `subtype = TNBC` even if the word "TNBC" is absent (rationale says "derived"). All three must be explicit — one missing/pending/equivocal → no TNBC.
> - **Do not infer HER2-enriched from HER2-positive.**
> - **Do not infer Basal-like from TNBC.**
> - **Do not infer Luminal A or B from ER+/HER2− alone.**
> Biologically plausible but unsupported cross-mapping is exactly the error this benchmark exists to catch.

**Mixed cohorts — think of it as an array:**
```
sample[1] → TNBC        sample[3] → Luminal A
sample[2] → TNBC        sample[4] → HER2-enriched
```
One unified heterogeneous cohort → dataset-level `subtype = mixed`, with the enumeration quoted. (A study structured as separate subtype-specific arms keeps its labels at sub-cohort scope — say so in the rationale rather than forcing one dataset-level value.)

**A dataset *containing* TNBC samples is not necessarily a TNBC dataset.** That exact mistake is a real bug this benchmark already caught in our engine.

**Self-check 4.1:** One unified cohort: 15 TNBC + 10 luminal tumors. `subtype` at dataset scope?
<details><summary>Answer</summary>

`mixed`, quoting the enumeration. Not TNBC.
</details>

**Self-check 4.2:** A cohort is explicitly ER−/PR−/HER2−. What may you assign, and what may you not infer?
<details><summary>Answer</summary>

You may assign **`subtype = TNBC`** (locked derivation; rationale says derived). You may **not** infer **Basal-like** — that needs expression-profiling evidence.
</details>

---

## 5 · Where did the material come from? → `sample_type`, `organism_context`

**The decision:** what material was measured, and what does the current schema's `organism_context` field expect?

**Required (~10 min):**
- [MedlinePlus: Biopsy](https://medlineplus.gov/biopsy.html) and [Blood](https://medlineplus.gov/blood.html) (plasma = the liquid fraction of blood) *(both fetched OK)*
- NCI Dictionary *(JS-rendered — text loads in your browser)*: [cell line (cultured)](https://www.cancer.gov/publications/dictionaries/cancer-terms/def/cultured-cell-line) · [xenograft](https://www.cancer.gov/publications/dictionaries/cancer-terms/def/xenograft) · [PDX](https://www.cancer.gov/publications/dictionaries/cancer-terms/def/pdx) · [organoid](https://www.cancer.gov/publications/dictionaries/cancer-terms/def/organoid)

**What you need to know — the concepts:** patient tissue, plasma, **cell lines** (immortalized cells grown in dishes for decades — MCF-7, MDA-MB-231, T47D, SK-BR-3 are human breast-cancer lines; 4T1 and MMTV-PyMT are mouse), **PDX/xenografts** (tumor grown in a mouse host), and **organoids** (lab-grown 3D mini-cultures) are different kinds of evidence. Two facts novices miss: **"Homo sapiens" does not mean patient-derived** (MCF-7 is human, and it is a cell line), and **human tumor + mouse host is one compatible system, not a contradiction.**

**How to label, in the current schema (this matches the engine — see `RULES_CARD.md` for the same table):**

| The material is… | `organism_context` | `sample_type` |
|---|---|---|
| Patient tissue/fluid, directly collected | `asserted` / `patient-derived` | tumor tissue, plasma, etc. |
| A named human cell line | `asserted` / the line's name | cell line |
| An animal model | `asserted` / `animal model` | the material (e.g., tumor tissue) |
| Xenograft/PDX, or patients + models together | `mixed` / `human and animal` | most specific model term (`PDX` beats `tumor tissue`) |
| Non-disease system | `asserted` / `non-disease` | as stated |

When one accession spans several materials, `sample_type` is `mixed` with the components enumerated in your rationale — the worked example shows exactly this.

**Real example:**
> *Source says:* "BT-474 xenograft tumors were grown in NSG mice."
> `organism_context` → `mixed` ("human and animal": human cell-line tumor, mouse host) · `sample_type` → **xenograft (CDX)** · and **this is not `conflicting`** — nothing contradicts anything.

**A true conflict, for contrast:**
> Paper Table 1: `Sample_08 = ER-negative` · PRIDE SDRF: `Sample_08 = ER-positive` — same sample, same property, same timepoint → `conflicting`, quote both.

**Self-check 5.1:** SDRF says `organism = Homo sapiens`; description says "BT-474 xenografts in nude mice." Conflict?
<details><summary>Answer</summary>

**No.** Human-origin material in a mouse host is one compatible system. Label `organism_context = mixed` ("human and animal"), `sample_type = xenograft`, and explain in the rationale.
</details>

**Self-check 5.2:** A record says only "tumor tissue," nothing about how it was obtained. Patient-derived?
<details><summary>Answer</summary>

**Cannot be inferred** — tumor tissue can come from a patient, a PDX, or another model. If nothing in the trail settles it, `organism_context = unknown` with the search depth documented.
</details>

---

## 6 · What the machines measured — and where you work

**The decision:** none directly — this is the context for everything you're cataloguing, ending at the repository you curate.

**Required (~15–30 min):**
- [PRIDE Quick tour](https://www.ebi.ac.uk/training/online/courses/pride-quick-tour) — EMBL-EBI, listed at 30 min. **EBI runs PRIDE — this is the official tour of the archive you're curating** *(fetched OK, CC BY 4.0)*. Heads-up: it's written for life-science students, so expect occasional unexplained jargon — that's what this primer and the team channel are for.
- The pipeline, in one diagram:
```
sample → extract proteins → cut into peptides → mass spectrometer
       → spectra (MS/MS) → database search → identified proteins
       → deposited in PRIDE with metadata  ← YOU ARE HERE
```

**What you need to know:** a mass spectrometer weighs molecule fragments extremely precisely; software matches the weights against protein databases to infer which proteins were present. The data files are enormous; the *metadata* describing what was measured is what makes them findable — and that metadata is what you're making trustworthy.

**Optional depth:** [Krogan lecture: Mass Spectrometry](https://www.ibiology.org/techniques/mass-spectrometry/) (27:36) *(fetched OK)* · [Dupree 2020 bottom-up proteomics review](https://www.mdpi.com/2227-7382/8/3/14) (Figure 1 = the workflow; CC BY) *(fetched OK)* · [EMBL-EBI proteomics intro](https://www.ebi.ac.uk/training/online/courses/proteomics-an-introduction/) (0.5 h, CC BY 4.0) *(fetched OK)*

---

## Done? Three last things

1. Quiz: `ANNOTATION_QUIZ.md` — 18 scenarios, aim ≥16.
2. Worked example: `WORKED_EXAMPLE.md` — one accession, all six fields, finished.
3. While labeling, keep **`RULES_CARD.md`** open — every rule above, on one page. Remember the golden rule: **"we don't know" is often the right answer**, and writing down *why* is what makes your label science.

*Sources, licenses, and verification details: instructor documents (`INSTRUCTOR_NOTES.md` and the resource report). Developed under AR INBRE (NIH NIGMS P20 GM103429). Educational content, not medical advice.*
