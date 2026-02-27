"""Product matching logic: exact, fuzzy, and LLM-assisted matching."""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from difflib import SequenceMatcher

from openai import OpenAI

from agent.prompts import MATCHING_PROMPT_TEMPLATE
from agent.tracker import TokenTracker

logger = logging.getLogger(__name__)

FUZZY_THRESHOLD = 0.7
BATCH_SIZE = 10  # max candidates per LLM call


@dataclass
class ProductMatch:
    """A matched pair of products from different sources."""
    official_name: str
    official_external_id: str
    retailer_name: str
    retailer_product_name: str
    retailer_price_usd: float | None
    retailer_url: str | None
    match_method: str  # "exact_name" | "exact_sku" | "fuzzy" | "llm"
    confidence: float
    retailer_sizes: list[str] | None = None
    retailer_in_stock: bool = True


def normalize_name(name: str) -> str:
    """Normalize product name for comparison."""
    name = name.lower().strip()
    name = re.sub(r"[^\w\s]", "", name)  # remove punctuation
    name = re.sub(r"\s+", " ", name)  # collapse whitespace
    return name


def match_products(
    official_products: list[dict],
    retailer_products: list[dict],
    retailer_name: str,
    client: OpenAI | None = None,
    tracker: TokenTracker | None = None,
    model: str = "qwen-turbo",
) -> list[ProductMatch]:
    """Match retailer products to the official catalog.

    Three-pass strategy:
    1. Exact SKU match
    2. Exact normalized name match
    3. Fuzzy name match with optional LLM disambiguation
    """
    matches: list[ProductMatch] = []
    matched_retailer_indices: set[int] = set()

    # Build lookup structures
    official_by_sku: dict[str, dict] = {}
    official_by_name: dict[str, dict] = {}
    for p in official_products:
        sku = (p.get("sku") or "").strip()
        if sku:
            official_by_sku[sku.lower()] = p
        norm = normalize_name(p.get("name", "") or p.get("name_en", ""))
        if norm:
            official_by_name[norm] = p

    # Pass 1: Exact SKU match
    for i, rp in enumerate(retailer_products):
        if i in matched_retailer_indices:
            continue
        rsku = (rp.get("sku") or "").strip().lower()
        if rsku and rsku in official_by_sku:
            op = official_by_sku[rsku]
            matches.append(_make_match(op, rp, retailer_name, "exact_sku", 1.0))
            matched_retailer_indices.add(i)

    # Pass 2: Exact normalized name match
    for i, rp in enumerate(retailer_products):
        if i in matched_retailer_indices:
            continue
        rname = normalize_name(rp.get("name", "") or rp.get("name_en", ""))
        if rname and rname in official_by_name:
            op = official_by_name[rname]
            matches.append(_make_match(op, rp, retailer_name, "exact_name", 0.95))
            matched_retailer_indices.add(i)

    # Pass 3: Fuzzy matching
    unmatched_retailer = [
        (i, rp) for i, rp in enumerate(retailer_products)
        if i not in matched_retailer_indices
    ]

    for op in official_products:
        op_name = normalize_name(op.get("name", "") or op.get("name_en", ""))
        candidates: list[tuple[int, dict, float]] = []

        for i, rp in unmatched_retailer:
            if i in matched_retailer_indices:
                continue
            rp_name = normalize_name(rp.get("name", "") or rp.get("name_en", ""))
            ratio = SequenceMatcher(None, op_name, rp_name).ratio()
            if ratio >= FUZZY_THRESHOLD:
                candidates.append((i, rp, ratio))

        if not candidates:
            continue

        # Sort by similarity descending
        candidates.sort(key=lambda x: x[2], reverse=True)

        # If top candidate is very high confidence, auto-match
        if candidates[0][2] >= 0.92:
            i, rp, ratio = candidates[0]
            matches.append(_make_match(op, rp, retailer_name, "fuzzy", ratio))
            matched_retailer_indices.add(i)
            continue

        # Otherwise, try LLM disambiguation if client available
        if client and tracker:
            llm_matches = _llm_disambiguate(
                op, candidates, retailer_name, client, tracker, model
            )
            for i, rp, confidence in llm_matches:
                matches.append(_make_match(
                    op, rp, retailer_name, "llm", confidence
                ))
                matched_retailer_indices.add(i)

    return matches


def _make_match(
    official: dict,
    retailer: dict,
    retailer_name: str,
    method: str,
    confidence: float,
) -> ProductMatch:
    return ProductMatch(
        official_name=official.get("name") or official.get("name_en", ""),
        official_external_id=official.get("external_id", ""),
        retailer_name=retailer_name,
        retailer_product_name=retailer.get("name") or retailer.get("name_en", ""),
        retailer_price_usd=_to_float(retailer.get("price_usd")),
        retailer_url=retailer.get("source_url"),
        match_method=method,
        confidence=confidence,
        retailer_sizes=retailer.get("sizes"),
        retailer_in_stock=retailer.get("in_stock", True),
    )


def _to_float(val) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _llm_disambiguate(
    official: dict,
    candidates: list[tuple[int, dict, float]],
    retailer_name: str,
    client: OpenAI,
    tracker: TokenTracker,
    model: str,
) -> list[tuple[int, dict, float]]:
    """Use the LLM to disambiguate fuzzy matches."""
    # Build candidates text
    candidates_lines = []
    for idx, (_, rp, ratio) in enumerate(candidates[:BATCH_SIZE]):
        rp_name = rp.get("name") or rp.get("name_en", "")
        rp_price = rp.get("price_usd", "N/A")
        rp_material = rp.get("material", "N/A")
        candidates_lines.append(
            f"[{idx}] Name: {rp_name} | Price: ${rp_price} | "
            f"Material: {rp_material} | Similarity: {ratio:.2f}"
        )

    prompt = MATCHING_PROMPT_TEMPLATE.format(
        official_name=official.get("name") or official.get("name_en", ""),
        official_sku=official.get("sku", "N/A"),
        official_price=official.get("price_usd", "N/A"),
        official_material=official.get("material", "N/A"),
        official_colors=", ".join(official.get("colors", [])) or "N/A",
        retailer_name=retailer_name,
        candidates_text="\n".join(candidates_lines),
    )

    t0 = time.monotonic()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        latency_ms = (time.monotonic() - t0) * 1000
        tracker.record(response, latency_ms, model)

        content = response.choices[0].message.content or "[]"
        # Parse JSON — handle both array and wrapped object
        parsed = json.loads(content)
        if isinstance(parsed, dict) and "matches" in parsed:
            parsed = parsed["matches"]
        if not isinstance(parsed, list):
            parsed = [parsed]

        results = []
        for item in parsed:
            if item.get("is_match") and item.get("confidence", 0) >= 0.8:
                idx = item["candidate_index"]
                if 0 <= idx < len(candidates):
                    i, rp, _ = candidates[idx]
                    results.append((i, rp, item["confidence"]))
        return results

    except Exception:
        logger.exception("LLM disambiguation failed")
        return []
