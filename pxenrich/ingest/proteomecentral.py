"""ProteomeCentral / ProteomeXchange discovery connector (PROXI API).

Docs: https://proteomecentral.proteomexchange.org/api/proxi/v0.1/ui/
The compact dataset listing returns positional rows; `datasets_title_list`
in the result_set names the columns. The per-dataset endpoint returns full
PROXI dataset JSON including description, contacts, and publication links.
"""

from __future__ import annotations

import datetime
import time
from typing import Iterator, Optional

import requests

from ..models import DatasetRecord

BASE = "https://proteomecentral.proteomexchange.org/api/proxi/v0.1"
USER_AGENT = "pxEnrich/0.1 (cancer evidence index; academic)"


def _get(url: str, params: Optional[dict] = None, retries: int = 3) -> dict | list:
    for attempt in range(retries):
        resp = requests.get(url, params=params, timeout=60,
                            headers={"User-Agent": USER_AGENT})
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code in (429, 500, 502, 503) and attempt < retries - 1:
            time.sleep(2 ** attempt)
            continue
        resp.raise_for_status()
    raise RuntimeError(f"unreachable: {url}")


def search_datasets(keywords: str, page_size: int = 100,
                    max_pages: int = 20) -> Iterator[dict]:
    """Yield compact dataset dicts for a keyword search, paging until done."""
    page = 1
    today = datetime.date.today().isoformat()
    while page <= max_pages:
        data = _get(f"{BASE}/datasets", {
            "resultType": "compact", "keywords": keywords,
            "pageSize": page_size, "pageNumber": page,
        })
        result_set = data.get("result_set", data) if isinstance(data, dict) else {}
        columns = result_set.get("datasets_title_list") or [
            "accession", "title", "repository", "species", "sdrf", "files",
            "instrument", "publications", "lab_head", "announce_date", "keywords"]
        rows = (data.get("datasets") if isinstance(data, dict) else data) or []
        if not rows:
            return
        for row in rows:
            if isinstance(row, dict):
                rec = dict(row)
            else:
                rec = {columns[i] if i < len(columns) else f"col{i}": v
                       for i, v in enumerate(row)}
            rec["_retrieved"] = today
            yield rec
        n_total = result_set.get("n_available_rows")
        if n_total is not None and page * page_size >= int(n_total):
            return
        if len(rows) < page_size:
            return
        page += 1
        time.sleep(0.5)  # be polite to the public API


def get_dataset_detail(accession: str) -> dict:
    """Full PROXI dataset record (description, contacts, publications, links)."""
    return _get(f"{BASE}/datasets/{accession}")


def _first(d: dict, *keys, default=None):
    for k in keys:
        v = d.get(k)
        if v:
            return v
    return default


def normalize_compact(row: dict) -> DatasetRecord:
    acc = _first(row, "accession", "dataset identifier", "identifier", "col0")
    return DatasetRecord(
        accession=str(acc).strip(),
        title=str(_first(row, "title", "col1", default="")).strip(),
        repository=str(_first(row, "repository", "col2", default="unknown")).strip(),
        species=_first(row, "species", "col3"),
        instrument=_first(row, "instrument", "col6"),
        announce_date=str(_first(row, "announce_date", "announceDate", "col9", default="") or "")[:10] or None,
        keywords=_first(row, "keywords", "col10"),
        source="proteomecentral",
        source_retrieved=row.get("_retrieved"),
        record_status="metadata_only",
    )


def merge_detail(rec: DatasetRecord, detail: dict) -> DatasetRecord:
    """Merge a PROXI detail record into a compact record."""
    # Description: PROXI uses a list of summary/description strings or a plain field.
    desc = detail.get("summary") or detail.get("description")
    if isinstance(desc, list):
        desc = " ".join(str(d) for d in desc)
    if desc:
        rec.description = str(desc)
        rec.record_status = "detailed"
    pubs = detail.get("publications") or []
    pubmed, dois = [], []
    for p in pubs if isinstance(pubs, list) else []:
        if isinstance(p, dict):
            pid = p.get("id") or p.get("pubmedId") or p.get("pubmed_id")
            if pid:
                pubmed.append(str(pid))
            doi = p.get("doi")
            if doi:
                dois.append(str(doi))
    if pubmed:
        rec.pubmed_ids = "; ".join(pubmed)
    if dois:
        rec.dois = "; ".join(dois)
    for link in detail.get("datasetLink", detail.get("fullDatasetLinks", [])) or []:
        if isinstance(link, dict):
            url = link.get("url") or link.get("value")
            if url and ("pride" in url or "massive" in url or "iprox" in url
                        or "jpost" in url):
                rec.repo_link = url
                break
    contacts = detail.get("contacts") or []
    for cdict in contacts if isinstance(contacts, list) else []:
        if isinstance(cdict, dict):
            role = str(cdict.get("role", "")).lower()
            if "lab head" in role or "principal" in role:
                rec.lab_head = cdict.get("name")
                break
    return rec
