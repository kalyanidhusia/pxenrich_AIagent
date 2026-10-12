"""MassIVE connector (UCSD) — second repository, same normalized schema.

MassIVE also speaks PROXI, so discovery-level coverage comes free via the
ProteomeCentral connector (MassIVE-hosted PXD records already appear there).
This module adds direct MassIVE lookups for records that are MassIVE-only
(MSV accessions without PXD identifiers) and for richer metadata.

API base: https://massive.ucsd.edu/ProteoSAFe/proxi/v0.1
"""

from __future__ import annotations

import time
from typing import Iterator, Optional

import requests

from ..models import DatasetRecord

BASE = "https://massive.ucsd.edu/ProteoSAFe/proxi/v0.1"
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


def search_datasets(keywords: str, page_size: int = 100,
                    max_pages: int = 10) -> Iterator[dict]:
    page = 1
    while page <= max_pages:
        data = _get("/datasets", {"keywords": keywords, "pageSize": page_size,
                                  "pageNumber": page})
        rows = data if isinstance(data, list) else (data or {}).get("datasets", [])
        if not rows:
            return
        yield from rows
        if len(rows) < page_size:
            return
        page += 1
        time.sleep(0.5)


def get_dataset_detail(accession: str) -> dict:
    return _get(f"/datasets/{accession}")


def normalize(d: dict, retrieved: Optional[str] = None) -> DatasetRecord:
    acc = d.get("accession") or d.get("identifier") or d.get("id")
    species = d.get("species")
    if isinstance(species, list):
        species = ", ".join(
            s.get("name", str(s)) if isinstance(s, dict) else str(s)
            for s in species)
    instruments = d.get("instruments")
    if isinstance(instruments, list):
        instruments = ", ".join(
            i.get("name", str(i)) if isinstance(i, dict) else str(i)
            for i in instruments)
    desc = d.get("summary") or d.get("description")
    if isinstance(desc, list):
        desc = " ".join(str(x) for x in desc)
    kw = d.get("keywords")
    if isinstance(kw, list):
        kw = ", ".join(str(k) for k in kw)
    return DatasetRecord(
        accession=str(acc),
        title=str(d.get("title", "")).strip(),
        repository="MassIVE",
        species=species or None,
        instrument=instruments or None,
        keywords=kw or None,
        description=str(desc) if desc else None,
        repo_link=f"https://massive.ucsd.edu/ProteoSAFe/dataset.jsp?accession={acc}",
        source="massive_proxi",
        source_retrieved=retrieved,
        record_status="detailed" if desc else "metadata_only",
    )
