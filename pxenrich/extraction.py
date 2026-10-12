"""Deterministic evidence extraction for breast-cancer proteomics metadata.

Design rules (from the product brief):
  * The LLM is not the database — these rules are deterministic and reproducible.
  * Every assertion carries evidence_text, source, scope, and confidence.
  * "Unknown", "mixed", "conflicting", and "abstained" are valid outputs.
  * A study ABOUT a biomarker (study_focus) is NOT a claim that the cohort
    HAS that biomarker status (dataset scope). The two are kept distinct.

The rule set encodes the domain knowledge the pxEnrich team curated for
ER / PR / HER2 / subtype / sample scope. Extend RULE_VERSION when rules change
so regression tests can pin behavior to a rule version.
"""

from __future__ import annotations

import re
from typing import Optional

from .models import (
    AssertionStatus,
    DatasetRecord,
    EvidenceAssertion,
    Scope,
    SourceType,
)

RULE_VERSION = "rule:v0.1"

# ---------------------------------------------------------------------------
# Lexicons
# ---------------------------------------------------------------------------

# Human breast cancer cell lines commonly seen in proteomics metadata.
CELL_LINES_HUMAN = [
    "MCF-7", "MCF7", "MDA-MB-231", "MDA-MB231", "MDA-MB-468", "MDA-MB468",
    "T47D", "T-47D", "SK-BR-3", "SKBR3", "BT-474", "BT474", "HCC1937",
    "SUM-159", "SUM159", "ZR-75", "CAL-51", "HS578T", "CA1a", "CTC-ITB-01",
]
# Mouse mammary tumor lines / models.
CELL_LINES_MOUSE = ["4T1", "EMT6", "E0771", "MMTV-PyMT", "PyMT"]

ANIMAL_SPECIES = {
    "mus musculus": "mouse",
    "rattus norvegicus": "rat",
    "canis": "dog",
    "bos taurus": "cow",
    "nesolagus": "rabbit",
    "oryctolagus": "rabbit",
    "danio rerio": "zebrafish",
}
NON_DISEASE_SPECIES = ["escherichia coli", "saccharomyces", "bacillus"]

# Subtype vocabulary (pattern, canonical value).
SUBTYPE_PATTERNS = [
    (r"triple[\s-]?negative|TNBC", "triple-negative (TNBC)"),
    (r"luminal\s*A\b", "luminal A"),
    (r"luminal\s*B\b", "luminal B"),
    (r"HER2[\s-]?enriched", "HER2-enriched"),
    (r"basal[\s-]?like", "basal-like"),
]

# Receptor-status patterns asserting a COHORT status (not just topic focus).
ER_STATUS_PATTERNS = [
    (r"\bER[\s-]?positive\b|\bER\+", "positive"),
    (r"\bestrogen[\s-]?receptor[\s-]?positive\b", "positive"),
    (r"\bER[\s-]?negative\b|\bER-(?![\w])", "negative"),
    (r"\bestrogen[\s-]?receptor[\s-]?negative\b", "negative"),
]
PR_STATUS_PATTERNS = [
    (r"\bPR[\s-]?positive\b|\bPR\+", "positive"),
    (r"\bprogesterone[\s-]?receptor[\s-]?positive\b", "positive"),
    (r"\bPR[\s-]?negative\b", "negative"),
]
HER2_STATUS_PATTERNS = [
    (r"\bHER2[\s-]?low\b", "low"),
    (r"\bHER2[\s-]?positive\b|\bHER2\+", "positive"),
    (r"\bHER2[\s-]?negative\b|\bHER2-(?![\w])", "negative"),
]
# Mentions that indicate the study is ABOUT a receptor without asserting cohort status.
HER2_FOCUS = r"\bHER2\b|\bERBB2\b"
ER_FOCUS = r"\bER(?:alpha|α)?\b|\bESR1\b|\bestrogen receptor\b"

# Sample-type vocabulary, ordered by specificity.
SAMPLE_PATTERNS = [
    (r"patient[\s-]?derived xenograft|\bPDX\b", "patient-derived xenograft (PDX)"),
    (r"tumou?roids?|organoids?", "organoid / tumoroid"),
    (r"circulating tumou?r cells?|\bCTCs?\b", "circulating tumor cells"),
    (r"\bFFPE\b|tumou?r tissue|tumor and (?:neighboring|adjacent)|tissue samples?|clinical samples?|breast tissue|microdissected", "tumor / clinical tissue"),
    (r"\bplasma\b", "plasma"),
    (r"\bserum\b", "serum"),
    (r"\burin(?:e|ary)\b", "urine"),
    (r"peripheral blood|\bPBMCs?\b|monocytes|lymphocytes|\bblood\b", "blood / immune cells"),
    (r"saliva", "saliva"),
    (r"extracellular vesicles?|exosomes?|\bEVs?\b", "extracellular vesicles"),
    (r"cell lines?|spheroids?|co[\s-]?culture", "cell line / in vitro"),
]

TNBC_RE = re.compile(r"triple[\s-]?negative|TNBC", re.I)

TREATMENT_PATTERNS = [
    (r"pre[\s-]?and post[\s-]?|before and after (?:surgery|treatment)|pre[\s-]?surgery|post[\s-]?surgery|neoadjuvant|adjuvant", "pre/post treatment comparison"),
    (r"resistan(?:t|ce)|persist(?:er|ence)", "therapy resistance / persistence"),
    (r"treated with|treatment response|exposed to|inhibitor|inhibition|drug repurposing|chemotherapy|endocrine therapy|tamoxifen|fulvestrant|palbociclib|paclitaxel|cisplatin|docetaxel|anastrozole|aromatase", "drug / treatment exposure"),
]


def _search(patterns, text: str):
    """Return (canonical_value, matched_text) for the first matching pattern."""
    for pat, value in patterns:
        m = re.search(pat, text, re.I)
        if m:
            return value, m.group(0)
    return None, None


def _snippet(text: str, match: str, width: int = 120) -> str:
    """Return a short evidence snippet around the match."""
    idx = text.lower().find(match.lower())
    if idx < 0:
        return match
    start = max(0, idx - width // 2)
    end = min(len(text), idx + len(match) + width // 2)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{text[start:end].strip()}{suffix}"


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def extract_assertions(rec: DatasetRecord) -> list[EvidenceAssertion]:
    """Run all deterministic rules over one dataset record.

    Returns one assertion per evidence field. Fields with no evidence get an
    UNKNOWN assertion so that downstream consumers never confuse "we did not
    look" with "we looked and found nothing".
    """
    out: list[EvidenceAssertion] = []
    acc = rec.accession
    title = rec.title or ""
    desc = rec.description or ""
    keyw = rec.keywords or ""
    species = (rec.species or "").lower()
    # Order matters: title and description are stronger evidence than keywords.
    sources = [
        (title, SourceType.TITLE, 0.85),
        (desc, SourceType.DESCRIPTION, 0.80),
        (keyw, SourceType.KEYWORDS, 0.60),
    ]
    all_text = f"{title}\n{desc}\n{keyw}"

    # --- organism / disease context -------------------------------------
    out.extend(_organism_and_disease(rec, species, all_text, title, desc, keyw))

    # --- subtype ----------------------------------------------------------
    subtype_hits = []
    for text, stype, conf in sources:
        if not text:
            continue
        for pat, value in SUBTYPE_PATTERNS:
            m = re.search(pat, text, re.I)
            if m:
                subtype_hits.append((value, m.group(0), text, stype, conf))
    distinct = {v for v, *_ in subtype_hits}
    # Mixed-cohort detection: a single subtype hit inside an ENUMERATION of
    # subtype groups ("HER2-negative luminal, HER2-positive, and triple-
    # negative...") is a mixed cohort, not a TNBC/luminal-only study.
    group_terms = len(set(re.findall(
        r"triple[\s-]?negative|TNBC|luminal(?:\s*[AB])?|HER2[\s-]?(?:positive|negative|enriched)|basal[\s-]?like",
        all_text, re.I)) )
    enumerated = len(re.findall(
        r"triple[\s-]?negative|TNBC|luminal|HER2[\s-]?(?:positive|negative|enriched)|basal[\s-]?like",
        all_text, re.I))
    if len(distinct) == 1 and enumerated >= 2 and group_terms >= 2 and \
            re.search(r"subtypes|spanning|across|cohort", all_text, re.I):
        hit_text = "; ".join(sorted(set(re.findall(
            r"triple[\s-]?negative|TNBC|luminal(?:\s*[AB])?|HER2[\s-]?(?:positive|negative|enriched)|basal[\s-]?like",
            all_text, re.I))))
        out.append(EvidenceAssertion(
            acc, "subtype", None, AssertionStatus.MIXED, Scope.DATASET, 0.7,
            evidence_text=f"Multiple subtype groups enumerated: {hit_text}",
            source_type=SourceType.DESCRIPTION, source_url=rec.repo_link,
            extracted_by=RULE_VERSION,
            note="The cohort spans several subtype groups; no single subtype label applies.",
        ))
        subtype_handled = True
    else:
        subtype_handled = False
    if subtype_handled:
        pass
    elif len(distinct) > 1:
        values = ", ".join(sorted(distinct))
        out.append(EvidenceAssertion(
            acc, "subtype", values, AssertionStatus.MIXED, Scope.DATASET, 0.7,
            evidence_text="; ".join(sorted({f"'{m}'" for _, m, *_ in subtype_hits})),
            source_type=SourceType.DESCRIPTION, source_url=rec.repo_link,
            extracted_by=RULE_VERSION,
            note="Multiple subtypes mentioned — likely a mixed or comparative cohort.",
        ))
    elif len(distinct) == 1:
        value, matched, text, stype, conf = subtype_hits[0]
        out.append(EvidenceAssertion(
            acc, "subtype", value, AssertionStatus.ASSERTED, Scope.DATASET, conf,
            evidence_text=_snippet(text, matched), source_type=stype,
            source_url=rec.repo_link, extracted_by=RULE_VERSION,
        ))
    else:
        out.append(_unknown(acc, "subtype", rec,
                            "No subtype terms found in title, description, or keywords."))

    # --- receptor statuses -------------------------------------------------
    out.append(_receptor(rec, "er_status", ER_STATUS_PATTERNS, ER_FOCUS, sources))
    out.append(_receptor(rec, "pr_status", PR_STATUS_PATTERNS, None, sources))
    out.append(_receptor(rec, "her2_status", HER2_STATUS_PATTERNS, HER2_FOCUS, sources))

    # TNBC implies ER-/PR-/HER2- at dataset scope — propagate when subtype asserted.
    if any(a.field == "subtype" and a.value and "TNBC" in a.value
           and a.status == AssertionStatus.ASSERTED for a in out):
        for f, implied in (("er_status", "negative"), ("pr_status", "negative"),
                           ("her2_status", "negative")):
            existing = next(a for a in out if a.field == f)
            if existing.status == AssertionStatus.UNKNOWN:
                idx = out.index(existing)
                out[idx] = EvidenceAssertion(
                    acc, f, implied, AssertionStatus.ASSERTED, Scope.DATASET, 0.7,
                    evidence_text="Implied by triple-negative subtype assertion.",
                    source_type=SourceType.DESCRIPTION, source_url=rec.repo_link,
                    extracted_by=RULE_VERSION,
                    note="Derived: triple-negative = ER-, PR-, HER2- by definition.",
                )

    # --- sample type --------------------------------------------------------
    sample_hits = []
    for text, stype, conf in sources:
        if not text:
            continue
        for pat, value in SAMPLE_PATTERNS:
            m = re.search(pat, text, re.I)
            if m and (value, ) not in [(v, ) for v, *_ in sample_hits]:
                sample_hits.append((value, m.group(0), text, stype, conf))
    # Cell-line names count as sample evidence too.
    for line in CELL_LINES_HUMAN + CELL_LINES_MOUSE:
        if re.search(re.escape(line), all_text, re.I):
            sample_hits.append(("cell line / in vitro", line, all_text,
                                SourceType.TITLE, 0.9))
            break
    seen_vals = []
    for v, m, t, st, c in sample_hits:
        if v not in seen_vals:
            seen_vals.append(v)
    if not seen_vals:
        out.append(_unknown(acc, "sample_type", rec,
                            "No sample-type terms found in available metadata."))
    else:
        primary = [v for v in seen_vals if v != "extracellular vesicles"] or seen_vals
        value = "; ".join(primary[:3])
        if "extracellular vesicles" in seen_vals:
            value += " (extracellular-vesicle fraction)"
        first = next(h for h in sample_hits if h[0] == primary[0])
        out.append(EvidenceAssertion(
            acc, "sample_type", value, AssertionStatus.ASSERTED, Scope.DATASET,
            first[4], evidence_text=_snippet(first[2], first[1]),
            source_type=first[3], source_url=rec.repo_link, extracted_by=RULE_VERSION,
        ))

    # --- treatment context ---------------------------------------------------
    tvalue, tmatch = _search(TREATMENT_PATTERNS, all_text)
    if tvalue:
        out.append(EvidenceAssertion(
            acc, "treatment_context", tvalue, AssertionStatus.ASSERTED,
            Scope.DATASET, 0.65, evidence_text=_snippet(all_text, tmatch),
            source_type=SourceType.DESCRIPTION, source_url=rec.repo_link,
            extracted_by=RULE_VERSION,
        ))
    else:
        out.append(_unknown(acc, "treatment_context", rec,
                            "No treatment or therapy-response terms found."))

    return out


def _unknown(acc: str, fieldname: str, rec: DatasetRecord, note: str) -> EvidenceAssertion:
    return EvidenceAssertion(
        acc, fieldname, None, AssertionStatus.UNKNOWN, Scope.DATASET, 0.0,
        source_url=rec.repo_link, extracted_by=RULE_VERSION, note=note,
    )


def _receptor(rec, fieldname, status_patterns, focus_pattern, sources) -> EvidenceAssertion:
    """Receptor extraction distinguishing cohort status from study focus."""
    acc = rec.accession
    for text, stype, conf in sources:
        if not text:
            continue
        value, matched = _search(status_patterns, text)
        if value:
            return EvidenceAssertion(
                acc, fieldname, value, AssertionStatus.ASSERTED, Scope.DATASET,
                conf, evidence_text=_snippet(text, matched), source_type=stype,
                source_url=rec.repo_link, extracted_by=RULE_VERSION,
            )
    # No status pattern. Is the study ABOUT this receptor?
    if focus_pattern:
        all_text = "\n".join(t for t, _, _ in sources if t)
        m = re.search(focus_pattern, all_text, re.I)
        if m:
            return EvidenceAssertion(
                acc, fieldname, None, AssertionStatus.ABSTAINED, Scope.STUDY_FOCUS,
                0.0, evidence_text=_snippet(all_text, m.group(0)),
                source_type=SourceType.DESCRIPTION, source_url=rec.repo_link,
                extracted_by=RULE_VERSION,
                note=(f"The study involves {m.group(0)} as a subject of investigation, "
                      "but the metadata does not state the cohort's receptor status. "
                      "Studying a receptor is not the same as the samples being "
                      "receptor-positive or -negative."),
            )
    return _unknown(acc, fieldname, rec,
                    "No receptor-status statement found in available metadata.")


def _organism_and_disease(rec, species, all_text, title, desc, keyw):
    """Classify organism context and whether this is really a breast-cancer study."""
    acc = rec.accession
    out = []
    conflict = None
    if rec.to_dict(include_assertions=False).get("source") and isinstance(rec.description, str):
        if "sdrf lists homo sapiens" in (rec.description or "").lower() and \
           any(s in species for s in NON_DISEASE_SPECIES):
            conflict = ("Record species field and SDRF disagree "
                        f"(species field: {rec.species}; SDRF: Homo sapiens).")

    species_list = [s.strip() for s in re.split(r"[,;]", species) if s.strip()]
    kinds = set()
    for s in species_list:
        if "homo sapiens" in s or s == "human":
            kinds.add("human")
        elif any(k in s for k in ANIMAL_SPECIES):
            kinds.add("animal")
        elif any(k in s for k in NON_DISEASE_SPECIES):
            kinds.add("non_disease_system")
        elif s:
            kinds.add("other")

    human_cellline = any(re.search(re.escape(c), all_text, re.I) for c in CELL_LINES_HUMAN)
    mouse_model = any(re.search(re.escape(c), all_text, re.I) for c in CELL_LINES_MOUSE)
    patienty = re.search(
        r"patients?\b|clinical samples?|cohort|women|tumou?r tissue|biopsy|FFPE|patient[\s-]?derived",
        all_text, re.I)

    if conflict:
        out.append(EvidenceAssertion(
            acc, "organism_context", None, AssertionStatus.CONFLICTING, Scope.DATASET,
            0.0, evidence_text=conflict, source_type=SourceType.SPECIES_FIELD,
            source_url=rec.repo_link, extracted_by=RULE_VERSION,
            note="Sources disagree about the organism; flagged for curator review.",
        ))
    elif kinds == {"human"}:
        if patienty and not human_cellline:
            value, note = "human — patient-derived samples", None
        elif patienty and human_cellline:
            value = "human — patient-derived and cell-line components"
            note = "Both patient material and established cell lines are mentioned."
        elif human_cellline:
            value = "human cell line (in vitro)"
            note = ("Human-derived but an established cell line, not patient tissue; "
                    "findings may not transfer directly to patients.")
        else:
            value, note = "human (sample source not detailed)", None
        ev = patienty.group(0) if patienty else (
            next((c for c in CELL_LINES_HUMAN if re.search(re.escape(c), all_text, re.I)), rec.species))
        out.append(EvidenceAssertion(
            acc, "organism_context", value, AssertionStatus.ASSERTED, Scope.DATASET,
            0.85, evidence_text=_snippet(all_text, ev) if ev else rec.species,
            source_type=SourceType.SPECIES_FIELD, source_url=rec.repo_link,
            extracted_by=RULE_VERSION, note=note,
        ))
    elif "human" in kinds and ("animal" in kinds or mouse_model):
        out.append(EvidenceAssertion(
            acc, "organism_context", "mixed: human and animal model",
            AssertionStatus.MIXED, Scope.DATASET, 0.8,
            evidence_text=f"Species field: {rec.species}",
            source_type=SourceType.SPECIES_FIELD, source_url=rec.repo_link,
            extracted_by=RULE_VERSION,
            note="Contains both human and animal-model material; interpret per-sample.",
        ))
    elif "animal" in kinds or mouse_model:
        animal = next((v for k, v in ANIMAL_SPECIES.items() if k in species), "animal")
        out.append(EvidenceAssertion(
            acc, "organism_context", f"animal model ({animal})",
            AssertionStatus.ASSERTED, Scope.DATASET, 0.9,
            evidence_text=f"Species field: {rec.species}",
            source_type=SourceType.SPECIES_FIELD, source_url=rec.repo_link,
            extracted_by=RULE_VERSION,
            note="Animal-model study: informative for biology, not direct evidence in humans.",
        ))
    elif "non_disease_system" in kinds:
        out.append(EvidenceAssertion(
            acc, "organism_context", f"non-disease experimental system ({rec.species})",
            AssertionStatus.ASSERTED, Scope.DATASET, 0.9,
            evidence_text=f"Species field: {rec.species}",
            source_type=SourceType.SPECIES_FIELD, source_url=rec.repo_link,
            extracted_by=RULE_VERSION,
            note="e.g. recombinant protein work; not a study of patients or tumors.",
        ))
    else:
        out.append(_unknown(acc, "organism_context", rec, "Species field missing or unrecognized."))

    # Disease context: is this truly a breast-cancer study, or keyword-only?
    bc_strong = re.search(r"breast (?:cancer|carcinoma|tumou?r|adenocarcinoma)|mammary (?:tumou?r|gland|tumorigenesis)|TNBC|triple[\s-]negative", f"{title}\n{desc}", re.I)
    bc_kw_only = re.search(r"breast cancer", keyw, re.I)
    if bc_strong:
        out.append(EvidenceAssertion(
            acc, "disease_context", "breast cancer", AssertionStatus.ASSERTED,
            Scope.DATASET, 0.9, evidence_text=_snippet(f"{title}\n{desc}", bc_strong.group(0)),
            source_type=SourceType.TITLE, source_url=rec.repo_link,
            extracted_by=RULE_VERSION,
        ))
    elif bc_kw_only:
        out.append(EvidenceAssertion(
            acc, "disease_context", None, AssertionStatus.ABSTAINED, Scope.STUDY_FOCUS,
            0.0, evidence_text=_snippet(keyw, "breast cancer"),
            source_type=SourceType.KEYWORDS, source_url=rec.repo_link,
            extracted_by=RULE_VERSION,
            note=("'breast cancer' appears only in submitter keywords, not in the "
                  "title or description. The study may be related to breast-cancer "
                  "biology without being a breast-cancer study; not confidently labeled."),
        ))
    else:
        out.append(_unknown(acc, "disease_context", rec,
                            "No breast-cancer terms found in available metadata."))
    return out


def enrich_record(rec: DatasetRecord) -> DatasetRecord:
    """Attach extracted assertions to a record (idempotent)."""
    rec.assertions = extract_assertions(rec)
    return rec
