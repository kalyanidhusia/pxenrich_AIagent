"""Pluggable LLM layer for grounded narrative answers.

Configuration (env vars):
    ANTHROPIC_API_KEY   -> uses Anthropic Messages API
    OPENAI_API_KEY      -> uses OpenAI Chat Completions (if no Anthropic key)
    PXENRICH_LLM_MODEL  -> override the default model name
    PXENRICH_NO_LLM=1   -> force retrieval-only mode even if a key is present

Without a key, the product runs in retrieval-only mode: every feature except
free-form narrative works identically. The LLM NEVER adds facts — the prompt
restricts it to the retrieved records, requires accession citations, and
instructs abstention. Grounding is additionally checked by the caller: the
template answer and the full record set are always preserved alongside any
LLM narrative, and the evaluation harness compares the two.

Uses stdlib urllib so no SDK install is required.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Optional

from .models import DatasetRecord

DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-5"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """You are the answer layer of pxEnrich, a public tool that explains
breast-cancer proteomics research evidence. You will receive a user question and a
set of retrieved dataset records with evidence assertions.

Hard rules:
1. Use ONLY the provided records. Never add facts from memory.
2. Cite dataset accessions (e.g. PXD057759) for every claim tied to a dataset.
3. Distinguish patient-derived studies from cell-line and animal studies.
4. Respect assertion statuses: 'abstained'/'unknown'/'conflicting' fields must not
   be presented as known values. Explain the uncertainty instead.
5. If the records do not support an answer, say "There is not enough evidence in
   the indexed datasets to answer this" and say what IS available.
6. Never diagnose, prognose, or recommend treatment. This is research navigation.
7. Match the audience level you are given (plain / clinician / researcher).
Write 1-3 short paragraphs. No markdown headers."""


def llm_available() -> bool:
    if os.environ.get("PXENRICH_NO_LLM"):
        return False
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY"))


def _records_payload(records: list[DatasetRecord], cap: int = 12) -> str:
    blocks = []
    for r in records[:cap]:
        a_lines = [
            f"  - {a.field}: value={a.value!r} status={a.status.value} "
            f"scope={a.scope.value} evidence={a.evidence_text!r}"
            for a in r.assertions
        ]
        blocks.append(
            f"[{r.accession}] {r.title}\n"
            f"  repository={r.repository} species={r.species} "
            f"announced={r.announce_date}\n"
            f"  description={(r.description or 'n/a')[:600]}\n"
            + "\n".join(a_lines)
        )
    return "\n\n".join(blocks)


def llm_narrative(question: str, records: list[DatasetRecord],
                  audience: str) -> Optional[str]:
    """Return a grounded narrative, or None on any failure (caller falls back)."""
    user_msg = (
        f"Audience: {audience}\nQuestion: {question}\n\n"
        f"Retrieved records:\n{_records_payload(records)}"
    )
    try:
        if os.environ.get("ANTHROPIC_API_KEY"):
            return _anthropic(user_msg)
        if os.environ.get("OPENAI_API_KEY"):
            return _openai(user_msg)
    except Exception:
        return None
    return None


def _post_json(url: str, headers: dict, payload: dict, timeout: int = 60) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _anthropic(user_msg: str) -> Optional[str]:
    model = os.environ.get("PXENRICH_LLM_MODEL", DEFAULT_ANTHROPIC_MODEL)
    data = _post_json(
        "https://api.anthropic.com/v1/messages",
        {"x-api-key": os.environ["ANTHROPIC_API_KEY"],
         "anthropic-version": "2023-06-01"},
        {"model": model, "max_tokens": 800, "system": SYSTEM_PROMPT,
         "messages": [{"role": "user", "content": user_msg}]},
    )
    parts = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
    return "".join(parts).strip() or None


def _openai(user_msg: str) -> Optional[str]:
    model = os.environ.get("PXENRICH_LLM_MODEL", DEFAULT_OPENAI_MODEL)
    data = _post_json(
        "https://api.openai.com/v1/chat/completions",
        {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
        {"model": model, "max_tokens": 800,
         "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                      {"role": "user", "content": user_msg}]},
    )
    choices = data.get("choices") or []
    if choices:
        return (choices[0].get("message", {}).get("content") or "").strip() or None
    return None
