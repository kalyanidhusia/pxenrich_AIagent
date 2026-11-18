# pxEnrich Biology Primer — for the curation team

> **Working revision v3 — 2026-11-17.** Biology/metadata conflicts identified during primer review have now been resolved. One schema issue remains to be implemented in code before benchmark freeze: `organism_context` should represent biological taxonomic origin, while patient-derived status, host organism, and experimental model should be stored separately rather than collapsed into that field.

**Who this is for:** CS students labeling the pxEnrich benchmark. No biology background assumed.
**Time:** ~60–70 minutes for the required track. Optional-depth links are clearly marked — explore them if you're curious, skip them if you're not.
**How to use it:** each section maps to a labeling decision you will actually make. Read the section, absorb the labeling rule, try the two self-check questions. The full annotation quiz is in `ANNOTATION_QUIZ.md`.

> **One meta-lesson before you start.** Every link below carries a verification status from our source report: *fetched OK* (content confirmed), *JS-rendered* (link resolves; text confirmed only in a browser), or *unverified*. We show you these flags instead of hiding them because it is the same discipline you are applying to proteomics metadata: **a source existing is not the same as its content being verified.** If a link is dead or wrong, that's a finding — report it.

> **pxEnrich uncertainty states — use the most specific one that fits:**
> - `unknown` = no relevant evidence was found after completing the available evidence search.
> - `mixed` = multiple valid values coexist in the same dataset/cohort or pooled material.
> - `conflicting` = two claims are mutually exclusive for the **same entity, same property, and same biological/temporal scope**.
> - `abstained` = relevant evidence exists, but it is borderline, incomplete, or otherwise insufficient for a hard label and does not fit a more specific `mixed` or `conflicting` state.
> - `not_evaluable` = the field does not apply to the record.
>
> A `conflicting` or `mixed` record should not emit a single hard ontology value until the scope is resolved or the record is manually adjudicated.

---

## 1 · What disease does the biological material come from? → `disease_context`

**The decision:** what is the disease identity of the biological material being measured?

**Required (~10 min):**
- [What Is Breast Cancer?](https://www.cancer.gov/types/breast/what-is-breast-cancer) — NCI, ~2-min read with anatomy figure *(fetched OK)*
- [MedlinePlus: Breast Cancer](https://medlineplus.gov/breastcancer.html) — NIH topic page, skim *(fetched OK)*

**What you need to know:** `disease_context` describes the biological disease origin of the sample. It is separate from the *purpose of the experiment*. A breast-cancer cell line remains breast-cancer-derived material even when it is used to test a mass-spectrometry method or study a generic signaling pathway.

> **For pxEnrich:** keep biological identity separate from study intent. An authenticated breast-cancer cell line such as MCF-7 can support `disease_context = breast carcinoma` even when the study itself is method development. Study purpose should be represented separately (for example, `study_intent = method_development`) rather than by erasing the sample's disease origin. `unknown` is reserved for cases where the biological disease origin itself cannot be established.

**Real example:**
> *Source says:* "Optimization of phosphopeptide enrichment, demonstrated in MCF-7 cells."
> *`disease_context`?* **Breast carcinoma**, if the MCF-7 identity is established by the source/evidence trail.  
> *`sample_type`?* **Cell line.**  
> *Study purpose?* **Method development** — a separate concept, not the disease label.

**Self-check:** (1) A dataset studies a peptide-fragmentation method using MCF-7 cells. What is the disease origin, and what is the study purpose? (2) A study mentions BRCA1 but uses HeLa cells. Does the BRCA1 mention make the material breast-cancer-derived?

---

## 2 · DNA → RNA → protein (3 minutes, really)

**The decision:** none directly — but every other section leans on this.

**Required (~5 min):**
- [The Central Dogma of Biology](https://dnalc.cshl.edu/resources/3d/central-dogma.html) — Cold Spring Harbor 3D animation, **2:51** *(fetched OK)*
- Glossary (NHGRI, ~1 min each, all fetched OK): [Gene Expression](https://www.genome.gov/genetics-glossary/Gene-Expression) · [Transcription](https://www.genome.gov/genetics-glossary/Transcription) · [Translation](https://www.genome.gov/genetics-glossary/Translation)

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
- [Tests for Breast Cancer Biomarkers](https://www.cancer.gov/types/breast/diagnosis/breast-cancer-biomarker-tests) — NCI, updated Dec 2025. **The single most useful page in this primer**: covers ER, PR, HER2, **HER2-low**, and the subtype table, with a labeled cell figure *(fetched OK)*
- [Komen "Under the Microscope" video hub](https://www.komen.org/support-resources/tools/videos/) — the *Estrogen Receptor* and *HER2* episodes, each under 3 min *(hub fetched OK; find the episodes on the page)*

**What you need to know:** receptors are proteins on/in tumor cells. Pathologists score them as positive/negative (and for HER2, also **low** — some HER2 protein, but below the "positive" threshold; this category matters because new drugs target it). Status is determined per sample by a lab test — never guessed from what genes a paper discusses.

> **PR note:** you'll see PR (progesterone receptor) everywhere alongside ER and HER2 — you need it to understand "triple-negative" (= ER−, PR−, HER2−). **PR is necessary biological context, but `pr_status` is not one of your six benchmark fields.** Learn it; don't label it.

> **For pxEnrich:** assign `er_status` or `her2_status` only when the source explicitly states the status for the relevant cohort/samples **or when a locked deterministic clinical mapping applies.** A paper that *studies HER2 biology* is not automatically a HER2-positive cohort. "HER2" appearing in a title establishes topic, not status.

> **Locked HER2-low mapping:** `IHC 1+` → `her2_status = low`; `IHC 2+` with negative/non-amplified ISH/FISH → `her2_status = low`. Do **not** map an unresolved/equivocal `IHC 2+` result to HER2-low without the negative ISH/FISH result.

> **Unknown vs abstained here:**
> - No ER/HER2 information anywhere in the available evidence trail → `unknown`.
> - Relevant pathology exists but is borderline/incomplete (for example, HER2 IHC 2+ with FISH pending) → `abstained`.
> - Two sources assign incompatible receptor values to the same sample/timepoint → `conflicting`, with both sources quoted.

**Real example:**
> *Source says:* "HER2 RIME analysis in breast cancer cells."
> *Should `her2_status` = positive?* **No.** HER2 is the study's focus; the cohort's HER2 status is not established. Correct label: `abstained` (evidence exists but doesn't support a cohort-level claim) — with that sentence as your rationale.

**Self-check:** (1) A description says "ER+ tumors (n=24) were profiled" — what's `er_status` and what's your quote? (2) A description says "we investigated estrogen signaling" — what's `er_status`?

---

## 4 · Subtypes: TNBC, luminal A/B, HER2-enriched → `subtype`

**The decision:** TNBC, luminal A, luminal B, HER2-enriched, **mixed**, or not stated?

**Required (~10 min):**
- [Komen: Molecular Subtypes of Breast Cancer](https://www.komen.org/breast-cancer/diagnosis/molecular-subtypes/) — the subtype → receptor-status lookup table you'll actually use *(fetched OK)*
- The subtype table on the [NCI biomarker page](https://www.cancer.gov/types/breast/diagnosis/breast-cancer-biomarker-tests) you already read *(fetched OK)*

**What you need to know:** pxEnrich's `subtype` field contains two kinds of labels that must not be collapsed into one another:
- **Clinical phenotype:** TNBC, defined by explicit ER-negative + PR-negative + HER2-negative status.
- **Intrinsic molecular subtypes:** Luminal A, Luminal B, HER2-enriched, Basal-like (normally determined from gene-expression profiling such as PAM50/related classifiers).

> ⚠️ **The most important warning in this primer.** Clinical receptor status and intrinsic molecular subtype are different classification layers.
> - **Locked TNBC rule:** if a confirmed breast-cancer source explicitly states **ER−, PR−, and HER2−**, pxEnrich may deterministically assign `subtype = TNBC` even if the literal term "TNBC" is absent.
> - All three receptor results must be explicit. If one is missing, pending, equivocal, or unresolved, do **not** assign TNBC.
> - **Do not infer HER2-enriched from HER2-positive.** HER2+ is a clinical receptor status; HER2-enriched is a gene-expression subtype.
> - **Do not infer Basal-like from TNBC.** They overlap strongly but are not equivalent.
> - **Do not infer Luminal A or Luminal B from ER+/HER2− alone.** Distinguishing them requires explicit subtype evidence or the additional validated markers/classifier required by the source.
> Biologically plausible but unsupported cross-mapping is exactly the error this benchmark exists to catch.

**Mixed cohorts — preserve scope:**
```
Dataset PXD-example

sample[1] → TNBC
sample[2] → TNBC
sample[3] → Luminal A
sample[4] → HER2-enriched
```

If these samples form **one unified heterogeneous cohort**, dataset-level `subtype = mixed` is appropriate.

If the study is structurally divided into distinct subtype-specific sub-cohorts, preserve the subtype labels at `cohort_subset` scope rather than forcing a single dataset-level subtype. Likewise, a pooled reference channel containing material from several subtypes should be represented as `mixed` (or as its component labels, if the schema supports them), not forced into one subtype.

**A dataset containing TNBC samples is not necessarily a TNBC dataset.** This exact mistake — asserting TNBC for a multi-subtype cohort — is a real bug the benchmark has already caught in our extraction engine. Your labels guard against it.

**Self-check:** (1) One unified cohort contains 15 TNBC and 10 luminal tumors. What is `subtype` at dataset scope? (2) A breast-cancer source explicitly reports ER−/PR−/HER2− for the cohort. What clinical subtype may be assigned, and what intrinsic subtype may **not** be inferred?

---

## 5 · Biological origin, material, host, and model → `sample_type`, `organism_context`

**The decision:** what organism did the measured biological material originate from, and what physical material/model was analyzed?

**Required (~10 min):**
- [MedlinePlus: Biopsy](https://medlineplus.gov/biopsy.html) and [Blood](https://medlineplus.gov/blood.html) (plasma = the liquid fraction of blood) *(both fetched OK)*
- NCI Dictionary *(JS-rendered — text loads in your browser)*: [cell line (cultured)](https://www.cancer.gov/publications/dictionaries/cancer-terms/def/cultured-cell-line) · [xenograft](https://www.cancer.gov/publications/dictionaries/cancer-terms/def/xenograft) · [PDX](https://www.cancer.gov/publications/dictionaries/cancer-terms/def/pdx) · [organoid](https://www.cancer.gov/publications/dictionaries/cancer-terms/def/organoid)

**What you need to know:** four concepts that are often collapsed in repository metadata are actually different:
- **Biological origin / taxon** — the organism from which the measured cells or tissue originated (`Homo sapiens`, `Mus musculus`, etc.).
- **Physical material** — tumor tissue, plasma, blood, cultured cells, etc.
- **Experimental model** — primary tumor, cell line, PDX, CDX, organoid, etc.
- **Host organism** — the living carrier of a graft, such as a mouse carrying a human PDX.

> **Locked rule:** `organism_context` should represent **biological taxonomic origin**, not “patient-derived,” “primary tumor,” or model type.  
> `Homo sapiens` does **not** mean patient-derived. “Tumor tissue” by itself does **not** prove patient-derived status.  
> Organoids belong under `sample_type` / experimental-model information, never under `organism_context`.

> **PDX rule:** human tumor origin + mouse host is **not a conflict**. These are orthogonal facts:
> - biological origin = `Homo sapiens`
> - host organism = `Mus musculus`
> - experimental model = PDX
> - physical material = tumor tissue

**Current-schema warning:** the six-field benchmark has only `sample_type` and `organism_context`; it does not yet have dedicated `host_organism`, `experimental_model`, or `patient_derived` fields. Before benchmark freeze, the backend should either:
1. split these concepts into orthogonal fields, **preferred**, or
2. allow `sample_type` to carry multiple compatible controlled labels (for example, `["tumor tissue", "xenograft", "PDX"]`) while keeping `organism_context` taxonomic.

If a single flat `sample_type` string is temporarily unavoidable, use the most specific model label available (for example, `PDX` rather than only `tumor tissue`) and record the broader material/host context in the rationale.

**Real example:**
> *Source says:* "BT-474 xenograft tumors were grown in NSG mice."
> biological origin / `organism_context` → **Homo sapiens**  
> physical material → **tumor tissue**  
> experimental model → **cell-line-derived xenograft (CDX)**  
> host → **Mus musculus**  
> **This is not `conflicting`.**

**True conflict example:**
> Manuscript Table 1: `Sample_08 = ER-negative`  
> PRIDE SDRF: `Sample_08 = ER-positive`  
> Same sample, same property, same timepoint → **`conflicting`**. Quote both sources and withhold a single hard ER label until adjudication.

**Self-check:** (1) An SDRF says `organism = Homo sapiens`; the description says “BT-474 xenografts in nude mice.” Why can both be correct? (2) Does “tumor tissue” alone prove that a sample was directly collected from a patient?

---

## 6 · What the machines actually measured — and where you work

**The decision:** none directly — this is the context for everything you're cataloguing, ending at the repository you curate.

**Required (~15 min):**
- [PRIDE Quick tour](https://www.ebi.ac.uk/training/online/courses/pride-quick-tour) — EMBL-EBI, ~30 min listed, skimmable in 15. **EBI runs PRIDE — this is the official tour of the archive you are curating** *(fetched OK, CC BY 4.0)*
- The pipeline, in one diagram:
```
sample → extract proteins → cut into peptides → mass spectrometer
       → spectra (MS/MS) → database search → identified proteins
       → deposited in PRIDE with metadata  ← YOU ARE HERE
```

**What you need to know:** a mass spectrometer weighs molecule fragments extremely precisely; software matches those weights against protein databases to infer which proteins were present. The data files are enormous; the *metadata* describing what was measured is what makes them findable — and that metadata is what you're making trustworthy.

**Optional depth:** [Krogan lecture: Mass Spectrometry](https://www.ibiology.org/techniques/mass-spectrometry/) (27:36, the full how-it-works) *(fetched OK)* · [Dupree 2020 review](https://www.mdpi.com/2227-7382/8/3/14) (Figure 1 = the workflow; CC BY) *(fetched OK)* · [EMBL-EBI proteomics resources intro](https://www.ebi.ac.uk/training/online/courses/proteomics-an-introduction/) (0.5 h, CC BY 4.0) *(fetched OK)*

---

## Locked annotation rules from the biology review

Before formal curation starts, these are the rules to keep consistent across the primer, assignment, engine, and benchmark:

1. Explicit ER− + PR− + HER2− in confirmed breast cancer → deterministic `subtype = TNBC`.
2. TNBC must **not** be converted to Basal-like without molecular subtype evidence.
3. HER2-positive must **not** be converted to HER2-enriched without expression-based subtype evidence.
4. ER+/HER2− alone is insufficient to assign Luminal A vs Luminal B.
5. HER2 IHC 1+ → HER2-low; HER2 IHC 2+ requires negative/non-amplified ISH/FISH to map to HER2-low.
6. A heterogeneous unified cohort may be `mixed`; structurally distinct subtype groups should remain at `cohort_subset` scope.
7. `unknown` means no evidence found; `abstained` means relevant evidence exists but cannot support a hard label.
8. `conflicting` requires mutually exclusive claims about the same entity, property, and biological/temporal scope.
9. Human biological origin + mouse host in a xenograft is compatible, not conflicting.
10. `disease_context` records biological disease origin; study purpose is a separate concept.
11. Organoid/PDX/cell-line/model identity belongs with material/model metadata, not taxonomic `organism_context`.
12. Repository metadata and publication evidence do not silently override each other. Same-scope disagreement is `conflicting` until adjudicated.

---

## Done? Two last things

1. Take the quiz: `docs/ANNOTATION_QUIZ.md` — 18 realistic labeling scenarios. If you can reason through those, you're ready.
2. Remember the golden rule from the assignment: **"we don't know" is often the right answer**, and writing down *why* — with a verbatim quote or the depth you searched — is what makes your label science.

*Sources, licenses, and verification details for every link: see the instructor document `Biology primer resources for CS students.md`. Developed under AR INBRE (NIH NIGMS P20 GM103429). Educational content, not medical advice.*
