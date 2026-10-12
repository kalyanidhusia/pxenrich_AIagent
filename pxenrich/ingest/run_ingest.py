"""Ingestion CLI: build or refresh the pxEnrich evidence index.

Usage:
    # Offline bootstrap from the bundled seed snapshot (no network needed):
    python -m pxenrich.ingest.run_ingest --seed

    # Live ingest from ProteomeCentral (discovery) + PRIDE (deep metadata):
    python -m pxenrich.ingest.run_ingest --query "breast cancer" --details 50

    # Add MassIVE coverage:
    python -m pxenrich.ingest.run_ingest --query "breast cancer" --massive
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys

from .. import db as dbmod
from ..extraction import enrich_record
from ..models import DatasetRecord

SEED_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "seed", "seed_datasets.json")


def ingest_seed(conn, seed_path: str = SEED_PATH) -> int:
    with open(seed_path, encoding="utf-8") as f:
        seed = json.load(f)
    retrieved = seed.get("retrieved")
    n = 0
    for d in seed["datasets"]:
        detail = d.get("detail") or {}
        rec = DatasetRecord(
            accession=d["accession"], title=d["title"],
            repository=d.get("repository", "unknown"),
            species=d.get("species"), instrument=d.get("instrument"),
            announce_date=d.get("announce_date"), keywords=d.get("keywords"),
            description=detail.get("description"),
            lab_head=detail.get("lab_head"),
            pubmed_ids=detail.get("pubmed"), dois=detail.get("doi"),
            repo_link=detail.get("repo_link"),
            source="seed_snapshot", source_retrieved=retrieved,
            record_status="detailed" if detail.get("description") else "metadata_only",
        )
        enrich_record(rec)
        dbmod.upsert_record(conn, rec)
        n += 1
    conn.commit()
    return n


def ingest_live(conn, query: str, details: int = 0, use_massive: bool = False) -> int:
    from . import proteomecentral as pc
    today = datetime.date.today().isoformat()
    n = 0
    detail_budget = details
    for row in pc.search_datasets(query):
        rec = pc.normalize_compact(row)
        if not rec.accession or not rec.title:
            continue
        if detail_budget > 0:
            try:
                rec = pc.merge_detail(rec, pc.get_dataset_detail(rec.accession))
                detail_budget -= 1
            except Exception as e:  # noqa: BLE001 - connector errors are non-fatal
                print(f"  detail fetch failed for {rec.accession}: {e}", file=sys.stderr)
        # PRIDE deep enrichment for PRIDE-hosted records lacking a description
        if rec.repository == "PRIDE" and not rec.description and detail_budget > 0:
            try:
                from . import pride
                rec = pride.normalize_project(pride.get_project(rec.accession), today)
                detail_budget -= 1
            except Exception:
                pass
        enrich_record(rec)
        dbmod.upsert_record(conn, rec)
        n += 1
        if n % 50 == 0:
            conn.commit()
            print(f"  ingested {n} records...")
    if use_massive:
        from . import massive
        for d in massive.search_datasets(query):
            rec = massive.normalize(d, today)
            if rec.accession and rec.title:
                enrich_record(rec)
                dbmod.upsert_record(conn, rec)
                n += 1
    conn.commit()
    return n


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", action="store_true",
                    help="bootstrap from the bundled seed snapshot (offline)")
    ap.add_argument("--query", default=None,
                    help='live ingest keyword query, e.g. "breast cancer"')
    ap.add_argument("--details", type=int, default=50,
                    help="max per-dataset detail fetches during live ingest")
    ap.add_argument("--massive", action="store_true",
                    help="also ingest directly from MassIVE PROXI")
    ap.add_argument("--db", default=None, help="database path override")
    args = ap.parse_args()

    conn = dbmod.connect(args.db)
    total = 0
    if args.seed:
        total += ingest_seed(conn)
        print(f"Seed ingest complete: {total} records.")
    if args.query:
        total += ingest_live(conn, args.query, args.details, args.massive)
        print(f"Live ingest complete: {total} records total this run.")
    if not args.seed and not args.query:
        ap.error("nothing to do: pass --seed and/or --query")
    print(json.dumps(dbmod.stats(conn), indent=2))


if __name__ == "__main__":
    main()
