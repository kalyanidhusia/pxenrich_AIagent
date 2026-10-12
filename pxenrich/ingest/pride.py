"""PRIDE Archive REST API v3 connector (deep metadata for PRIDE-hosted datasets).

Docs / Swagger: https://www.ebi.ac.uk/pride/ws/archive/v3/webjars/swagger-ui/index.html

PRIDE is the first deep repository connector (brief §4): its API returns
project metadata, files, SDRF sample metadata, and publication links.
Raw-file download is deliberately NOT implemented in v1 (brief §8.4).
"""

from __future__ import annotations

import time
from typing import Iterator, Optional

import requests

from ..models import DatasetRecord

BASE = "https://www.ebi.ac.uk/pride/ws/archive/v3"
USER_AGENT = "pxEnrich/0.1 (cancer evidence index; academic)"


def _get(path: str, params: Optional[dict] = None, retries: int = 3):
    url = f"{BASE}{path}"
    for attempt in range(retries):
        resp = requests.get(url, params=params, timeout=60,
                            headers={"User-Agent": USER_AGENT})
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code in (429, 500, 502, 503) and attempt < retries - 1:
            time.sleep(2 ** attempt)
            continue
        resp.raise_for_status()


def search_projects(keyword: str, page_size: int = 100,
                    max_pages: int = 20) -> Iterator[dict]:
    """Yield PRIDE project summaries matching a keyword."""
    page = 0
    while page < max_pages:
        data = _get("/search/projects", {
            "keyword": keyword, "pageSize": page_size, "page": page})
        projects = data if isinstance(data, list) else \
            (data.get("_embedded", {}).get("compactProjects")
             or data.get("projects") or [])
        if not projects:
            return
        yield from projects
        if len(projects) < page_size:
            return
        page += 1
        time.sleep(0.5)


def get_project(accession: str) -> dict:
    return _get(f"/projects/{accession}")


def get_project_files(accession: str) -> list:
    data = _get(f"/projects/{accession}/files")
    return data if isinstance(data, list) else \
        data.get("_embedded", {}).get("files", [])


def get_similar_projects(accession: str) -> list:
    try:
        data = _get(f"/projects/{accession}/similarProjects")
        return data if isinstance(data, list) else []
    except Exception:
        return []


def normalize_project(p: dict, retrieved: Optional[str] = None) -> DatasetRecord:
    """Normalize a PRIDE project (full or compact) into a DatasetRecord."""
    acc = p.get("accession") or p.get("projectAccession")
    species = p.get("organisms") or p.get("species") or []
    if isinstance(species, list):
        species = ", ".join(
            s.get("name", str(s)) if isinstance(s, dict) else str(s)
            for s in species)
    instruments = p.get("instruments") or []
    if isinstance(instruments, list):
        instruments = ", ".join(
            i.get("name", str(i)) if isinstance(i, dict) else str(i)
            for i in instruments)
    keywords = p.get("keywords") or []
    if isinstance(keywords, list):
        keywords = ", ".join(str(k) for k in keywords)
    refs = p.get("references") or []
    pubmed = "; ".join(str(r.get("pubmedId")) for r in refs
                       if isinstance(r, dict) and r.get("pubmedId"))
    dois = "; ".join(str(r.get("doi")) for r in refs
                     if isinstance(r, dict) and r.get("doi"))
    lab_heads = p.get("labPIs") or p.get("labHeads") or []
    lab_head = None
    if isinstance(lab_heads, list) and lab_heads:
        lh = lab_heads[0]
        lab_head = lh.get("name") if isinstance(lh, dict) else str(lh)

    return DatasetRecord(
        accession=str(acc),
        title=str(p.get("title", "")).strip(),
        repository="PRIDE",
        species=species or None,
        instrument=instruments or None,
        announce_date=str(p.get("publicationDate") or p.get("submissionDate")
                          or "")[:10] or None,
        keywords=keywords or None,
        description=p.get("projectDescription") or p.get("description"),
        lab_head=lab_head,
        pubmed_ids=pubmed or None,
        dois=dois or None,
        repo_link=f"https://www.ebi.ac.uk/pride/archive/projects/{acc}",
        source="pride_v3",
        source_retrieved=retrieved,
        record_status="detailed" if p.get("projectDescription") else "metadata_only",
    )


def get_sdrf_sample_metadata(accession: str) -> Optional[list]:
    """Fetch SDRF sample-level metadata when the project provides it.

    SDRF files carry per-sample disease/subtype annotations — the richest
    source for sample-scope assertions. Returns a list of file descriptors
    whose names contain 'sdrf'; downloading/parsing them is a v1.1 milestone.
    """
    try:
        files = get_project_files(accession)
        return [f for f in files
                if "sdrf" in str(f.get("fileName", "")).lower()] or None
    except Exception:
        return None
