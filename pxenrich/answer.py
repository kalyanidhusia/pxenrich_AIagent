"""Evidence-grounded answer composition.

Two modes:
  1. retrieval-only (default, no API key needed): deterministic, template-based
     plain-language summaries of what retrieval found, at three audience levels.
  2. LLM-assisted (set ANTHROPIC_API_KEY or OPENAI_API_KEY): the LLM writes the
     narrative but is constrained to the retrieved records; it must cite
     accessions and is instructed to abstain when evidence is insufficient.

In BOTH modes the answer object carries the underlying records and assertions,
so the UI can always show provenance. An answer with no sources is a defect.
"""

from __future__ import annotations

from typing import Optional

from .llm import llm_available, llm_narrative
from .models import AssertionStatus, DatasetRecord

AUDIENCES = ("plain", "clinician", "researcher")

NON_CLINICAL_NOTICE = (
    "This tool explains public research evidence. It does not diagnose disease, "
    "recommend treatment, or interpret personal medical records. For medical "
    "decisions, please talk with a clinician."
)


def _counts(records: list[DatasetRecord]) -> dict:
    c = {"human_patient": 0, "human_cellline": 0, "animal": 0, "mixed": 0,
         "other": 0, "samples": {}, "subtypes": {}, "repos": {}}
    for r in records:
        org = next((a for a in r.assertions if a.field == "organism_context"), None)
        v = (org.value or "") if org else ""
        if org and org.status == AssertionStatus.MIXED:
            c["mixed"] += 1
        elif "patient-derived" in v:
            c["human_patient"] += 1
        elif "cell line" in v:
            c["human_cellline"] += 1
        elif "animal" in v:
            c["animal"] += 1
        else:
            c["other"] += 1
        st = next((a for a in r.assertions if a.field == "sample_type"
                   and a.status == AssertionStatus.ASSERTED), None)
        if st and st.value:
            key = st.value.split(";")[0].strip()
            c["samples"][key] = c["samples"].get(key, 0) + 1
        sub = next((a for a in r.assertions if a.field == "subtype"
                    and a.status == AssertionStatus.ASSERTED), None)
        if sub and sub.value:
            c["subtypes"][sub.value] = c["subtypes"].get(sub.value, 0) + 1
        c["repos"][r.repository] = c["repos"].get(r.repository, 0) + 1
    return c


def _top(d: dict, n: int = 3) -> str:
    items = sorted(d.items(), key=lambda kv: -kv[1])[:n]
    return ", ".join(f"{k} ({v})" for k, v in items)


def compose_answer(question: str, retrieval: dict, audience: str = "plain",
                   use_llm: Optional[bool] = None) -> dict:
    """Build a grounded answer object from a retrieval result."""
    records: list[DatasetRecord] = retrieval["records"]
    audience = audience if audience in AUDIENCES else "plain"

    if not records:
        return {
            "question": question,
            "audience": audience,
            "status": "insufficient_evidence",
            "answer": (
                "Not enough evidence in the current index to answer this. "
                "The index covers public breast-cancer proteomics datasets; this "
                "question either falls outside that scope or matches no indexed "
                "records. Try broader terms, or browse the topic list."
            ),
            "mode": "retrieval_only",
            "sources": [],
            "notice": NON_CLINICAL_NOTICE,
        }

    c = _counts(records)
    n = retrieval["total_matches"]
    shown = len(records)

    if audience == "plain":
        lines = [
            f"Researchers have shared {n} public protein-measurement "
            f"(proteomics) dataset{'s' if n != 1 else ''} matching this question"
            f"{'; here are ' + str(shown) + ' of them' if n > shown else ''}.",
        ]
        if c["human_patient"]:
            lines.append(f"{c['human_patient']} of the studies shown used samples "
                         "donated by patients.")
        if c["human_cellline"]:
            lines.append(f"{c['human_cellline']} used human cancer cells grown in "
                         "the lab (cell lines) — useful for biology, but not the "
                         "same as studying patients directly.")
        if c["animal"]:
            lines.append(f"{c['animal']} used animal models.")
        if c["samples"]:
            lines.append(f"Most common sample types: {_top(c['samples'])}.")
        lines.append("Each study below links to its original public record, so "
                     "you can see exactly where this information comes from.")
    elif audience == "clinician":
        lines = [
            f"{n} indexed public proteomics datasets match "
            f"({shown} shown). Provenance: {_top(c['repos'])}.",
            f"Material: {c['human_patient']} patient-derived, "
            f"{c['human_cellline']} human cell-line, {c['animal']} animal-model, "
            f"{c['mixed']} mixed.",
        ]
        if c["subtypes"]:
            lines.append(f"Subtype annotations (asserted from metadata): {_top(c['subtypes'])}.")
        if c["samples"]:
            lines.append(f"Specimen types: {_top(c['samples'], 4)}.")
        lines.append("Receptor/subtype labels are metadata-derived with per-field "
                     "provenance and abstention; expand any record for the "
                     "supporting text. These are research datasets, not clinical evidence reviews.")
    else:  # researcher
        lines = [
            f"{n} datasets matched (showing {shown}). Filters applied: "
            f"{retrieval['parsed']}.",
            f"Repositories: {_top(c['repos'], 5)}. Organism contexts: "
            f"{c['human_patient']} patient-derived / {c['human_cellline']} human "
            f"cell line / {c['animal']} animal / {c['mixed']} mixed / "
            f"{c['other']} other-or-unresolved.",
            "All assertions are rule-derived (see extracted_by) with evidence "
            "snippets, scope (dataset vs study_focus), and abstention states. "
            "PXD accessions link to ProteomeCentral and the host repository.",
        ]

    template_answer = " ".join(lines)
    mode = "retrieval_only"
    answer_text = template_answer

    wants_llm = use_llm if use_llm is not None else llm_available()
    if wants_llm and llm_available():
        narrative = llm_narrative(question, records, audience)
        if narrative:
            answer_text = narrative
            mode = "llm_grounded"

    return {
        "question": question,
        "audience": audience,
        "status": "ok",
        "answer": answer_text,
        "template_answer": template_answer,  # always kept for comparison/testing
        "mode": mode,
        "evidence_summary": c,
        "total_matches": n,
        "sources": [
            {
                "accession": r.accession,
                "title": r.title,
                "repository": r.repository,
                "px_link": r.px_link,
                "repo_link": r.repo_link,
            } for r in records
        ],
        "notice": NON_CLINICAL_NOTICE,
    }


def explain_label(rec: DatasetRecord, fieldname: str) -> dict:
    """Answer 'why is / isn't this study labeled X?' from stored assertions."""
    a = next((x for x in rec.assertions if x.field == fieldname), None)
    if a is None:
        return {"field": fieldname, "explanation": "Field not evaluated for this record."}
    status_phrases = {
        AssertionStatus.ASSERTED: f"labeled '{a.value}'",
        AssertionStatus.UNKNOWN: "left as unknown",
        AssertionStatus.MIXED: f"labeled mixed ({a.value})",
        AssertionStatus.CONFLICTING: "flagged as conflicting",
        AssertionStatus.ABSTAINED: "deliberately not labeled (abstained)",
        AssertionStatus.NOT_EVALUABLE: "marked not evaluable",
    }
    parts = [f"{rec.accession} is {status_phrases[a.status]} for {fieldname}."]
    if a.evidence_text:
        parts.append(f"Supporting text: \"{a.evidence_text}\"")
    if a.note:
        parts.append(a.note)
    parts.append(f"(source: {a.source_type.value if a.source_type else 'n/a'}, "
                 f"scope: {a.scope.value}, extracted by {a.extracted_by}, "
                 f"confidence {a.confidence:.2f})")
    return {"field": fieldname, "assertion": a.to_dict(), "explanation": " ".join(parts)}
