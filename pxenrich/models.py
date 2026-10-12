"""Data models for the pxEnrich evidence index.

Plain dataclasses (stdlib-only) so the core engine runs anywhere.
The API layer serializes these to JSON; the MCP layer reuses the same shapes.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class AssertionStatus(str, Enum):
    """Status of an evidence assertion. Abstention states are first-class values."""

    ASSERTED = "asserted"            # evidence supports this value
    UNKNOWN = "unknown"              # no evidence found either way (default)
    MIXED = "mixed"                  # cohort contains more than one value (e.g. mixed subtypes)
    CONFLICTING = "conflicting"      # sources disagree (e.g. species field vs SDRF)
    ABSTAINED = "abstained"          # evidence exists but is insufficient to assert
    NOT_EVALUABLE = "not_evaluable"  # field does not apply to this record


class SourceType(str, Enum):
    """Where a piece of evidence came from."""

    TITLE = "title"
    DESCRIPTION = "description"
    KEYWORDS = "keywords"
    SPECIES_FIELD = "species_field"
    SDRF = "sdrf"
    PUBLICATION = "publication"
    CURATOR = "curator"
    REPOSITORY_FIELD = "repository_field"


class Scope(str, Enum):
    """What an assertion applies to. Distinguishing 'the study is about HER2'
    from 'the cohort is HER2-positive' is a core pxEnrich differentiator."""

    DATASET = "dataset"          # applies to the whole dataset/cohort
    COHORT_SUBSET = "cohort_subset"  # applies to part of the cohort
    SAMPLE = "sample"            # applies at sample level
    STUDY_FOCUS = "study_focus"  # the study is ABOUT this topic (not a cohort status claim)


# Fields the extraction engine evaluates for every dataset
EVIDENCE_FIELDS = [
    "er_status",        # cohort estrogen-receptor status
    "pr_status",        # cohort progesterone-receptor status
    "her2_status",      # cohort HER2 status (positive / negative / low)
    "subtype",          # breast cancer molecular subtype (TNBC, luminal A/B, HER2-enriched, ...)
    "sample_type",      # tumor tissue, plasma, blood, urine, cell line, PDX, organoid, ...
    "organism_context", # human patient-derived / human cell line / animal model / non-disease system
    "disease_context",  # is this actually a breast-cancer study (vs keyword-only mention)
    "treatment_context",# pre/post treatment, drug exposure, resistance models
]


@dataclass
class EvidenceAssertion:
    """One evidence-backed claim about one field of one dataset.

    A confident value with no evidence_text and no source is a DEFECT, not an answer.
    """

    dataset_accession: str
    field: str                       # one of EVIDENCE_FIELDS
    value: Optional[str]             # None when status is an abstention state
    status: AssertionStatus
    scope: Scope = Scope.DATASET
    confidence: float = 0.0          # 0..1; rule-based assertions carry calibrated defaults
    evidence_text: Optional[str] = None   # the exact text supporting the claim
    source_type: Optional[SourceType] = None
    source_url: Optional[str] = None
    extracted_by: str = "rule:v0.1"  # rule:vX | llm:<model> | curator:<name>
    note: Optional[str] = None       # human-readable qualifier (e.g. why abstained)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        d["scope"] = self.scope.value
        d["source_type"] = self.source_type.value if self.source_type else None
        return d


@dataclass
class DatasetRecord:
    """Normalized dataset record in the local evidence index."""

    accession: str                   # ProteomeXchange accession (PXD...)
    title: str
    repository: str                  # PRIDE | MassIVE | iProX | jPOST | ...
    species: Optional[str] = None
    instrument: Optional[str] = None
    announce_date: Optional[str] = None
    keywords: Optional[str] = None
    description: Optional[str] = None
    lab_head: Optional[str] = None
    pubmed_ids: Optional[str] = None
    dois: Optional[str] = None
    repo_link: Optional[str] = None
    px_link: Optional[str] = None    # ProteomeCentral page
    source: str = "proteomecentral"  # which connector produced this record
    source_retrieved: Optional[str] = None  # ISO date of retrieval
    record_status: str = "metadata_only"    # metadata_only | detailed | curated
    assertions: list[EvidenceAssertion] = field(default_factory=list)

    def __post_init__(self):
        if not self.px_link:
            self.px_link = (
                "https://proteomecentral.proteomexchange.org/"
                f"cgi/GetDataset?ID={self.accession}"
            )

    def to_dict(self, include_assertions: bool = True) -> dict:
        d = {k: v for k, v in asdict(self).items() if k != "assertions"}
        if include_assertions:
            d["assertions"] = [a.to_dict() for a in self.assertions]
        return d

    def searchable_text(self) -> str:
        parts = [self.title or "", self.keywords or "", self.description or ""]
        return "\n".join(p for p in parts if p)
