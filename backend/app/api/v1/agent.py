"""Agent admin API — trigger research jobs, view status, inspect sessions."""

from __future__ import annotations

import json
from pathlib import Path

from celery import Celery
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import AgentJob, Brand, Item, PriceListing, Retailer
from app.schemas.agent_job import (
    AgentJobListResponse,
    AgentJobResponse,
    AgentJobTrigger,
    SessionEntry,
    SessionResponse,
)
from app.schemas.common import PaginatedResponse

router = APIRouter()

celery_app = Celery(broker=settings.REDIS_URL)

SESSIONS_DIR = Path("sessions")


@router.post("/agent-jobs", response_model=AgentJobResponse, status_code=201)
def trigger_agent_research(
    body: AgentJobTrigger,
    db: Session = Depends(get_db),
) -> AgentJobResponse:
    brand = db.query(Brand).filter(Brand.slug == body.brand_slug).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    job = AgentJob(
        brand_id=brand.id,
        model=body.model,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    result = celery_app.send_task(
        "agent.tasks.research_brand",
        args=[body.brand_slug],
        kwargs={"model": body.model, "job_id": job.id},
        queue="agent",
    )

    job.celery_task_id = result.id
    db.commit()
    db.refresh(job)

    return _job_to_response(job, brand.slug)


@router.get("/agent-jobs", response_model=PaginatedResponse)
def list_agent_jobs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str | None = None,
    brand_slug: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(AgentJob, Brand.slug).join(Brand, AgentJob.brand_id == Brand.id)

    if status:
        query = query.filter(AgentJob.status == status)

    if brand_slug:
        query = query.filter(Brand.slug == brand_slug)

    total = query.count()
    rows = (
        query.order_by(AgentJob.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    data = []
    for job, slug in rows:
        data.append(AgentJobListResponse(
            id=job.id,
            brand_slug=slug,
            model=job.model,
            status=job.status,
            tool_calls=job.tool_calls,
            total_input_tokens=job.total_input_tokens,
            total_output_tokens=job.total_output_tokens,
            total_cost_usd=job.total_cost_usd,
            has_snapshot=bool((job.result or {}).get("snapshot")),
            started_at=job.started_at,
            completed_at=job.completed_at,
            created_at=job.created_at,
        ))

    return PaginatedResponse(data=data, total=total, page=page, per_page=per_page)


@router.get("/agent-jobs/compare")
def compare_agent_jobs(
    job_a: int = Query(..., alias="job_a"),
    job_b: int = Query(..., alias="job_b"),
    db: Session = Depends(get_db),
):
    """Compare snapshots from two agent jobs side-by-side."""
    row_a = (
        db.query(AgentJob, Brand.slug)
        .join(Brand, AgentJob.brand_id == Brand.id)
        .filter(AgentJob.id == job_a)
        .first()
    )
    row_b = (
        db.query(AgentJob, Brand.slug)
        .join(Brand, AgentJob.brand_id == Brand.id)
        .filter(AgentJob.id == job_b)
        .first()
    )
    if not row_a or not row_b:
        raise HTTPException(status_code=404, detail="One or both jobs not found")

    ja, slug_a = row_a
    jb, slug_b = row_b

    snap_a = (ja.result or {}).get("snapshot", {})
    snap_b = (jb.result or {}).get("snapshot", {})
    metrics_a = snap_a.get("metrics") or {}
    metrics_b = snap_b.get("metrics") or {}

    # Compute deltas for numeric metrics
    delta_keys = [
        "items_total", "items_with_images", "items_with_prices",
        "items_in_stock", "listings_total", "listings_with_urls",
        "channels_count", "avg_price_usd",
    ]
    deltas: dict = {}
    for key in delta_keys:
        va = metrics_a.get(key)
        vb = metrics_b.get(key)
        if va is not None and vb is not None:
            deltas[key] = round(vb - va, 2) if isinstance(vb, float) else vb - va
        else:
            deltas[key] = None

    # Cost delta
    cost_a = ja.total_cost_usd or 0
    cost_b = jb.total_cost_usd or 0
    deltas["cost_usd"] = round(cost_b - cost_a, 4)

    # Item diff based on name_en matching
    items_a = {i["name_en"]: i for i in snap_a.get("items", [])}
    items_b = {i["name_en"]: i for i in snap_b.get("items", [])}
    names_a = set(items_a.keys())
    names_b = set(items_b.keys())

    only_in_a = sorted(names_a - names_b)
    only_in_b = sorted(names_b - names_a)
    in_both_names = names_a & names_b

    price_changes = []
    for name in sorted(in_both_names):
        pa = items_a[name].get("price_usd")
        pb = items_b[name].get("price_usd")
        if pa is not None and pb is not None and pa != pb:
            price_changes.append({"name": name, "a_price": pa, "b_price": pb})

    def _job_summary(job, slug, metrics):
        return {
            "id": job.id,
            "brand_slug": slug,
            "model": job.model,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "cost_usd": job.total_cost_usd,
            "metrics": metrics or None,
        }

    return {
        "job_a": _job_summary(ja, slug_a, metrics_a),
        "job_b": _job_summary(jb, slug_b, metrics_b),
        "deltas": deltas,
        "item_diff": {
            "only_in_a": only_in_a,
            "only_in_b": only_in_b,
            "in_both": len(in_both_names),
            "price_changes": price_changes,
        },
    }


@router.get("/agent-jobs/{job_id}", response_model=AgentJobResponse)
def get_agent_job(
    job_id: int,
    db: Session = Depends(get_db),
) -> AgentJobResponse:
    row = (
        db.query(AgentJob, Brand.slug)
        .join(Brand, AgentJob.brand_id == Brand.id)
        .filter(AgentJob.id == job_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Agent job not found")

    job, slug = row
    return _job_to_response(job, slug)


MODEL_COSTS: dict[str, tuple[float, float]] = {
    # (input_cost_per_1m, output_cost_per_1m)
    "qwen-max": (1.20, 6.00),
    "qwen-plus": (0.40, 1.20),
    "qwen-plus-latest": (0.40, 1.20),
    "qwen-turbo": (0.05, 0.20),
    "qwen-flash": (0.05, 0.40),
    "qwen3.5-plus": (0.40, 2.40),
    # Gemini pricing per 1M tokens (USD)
    "gemini-2.5-flash-lite": (0.10, 0.40),
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-3-flash-preview": (0.50, 3.00),
    "gemini-3.1-pro-preview": (2.00, 12.00),
}


def _calc_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    in_rate, out_rate = MODEL_COSTS.get(model, (0.0, 0.0))
    return input_tokens * in_rate / 1_000_000 + output_tokens * out_rate / 1_000_000


def _truncate(text: str, max_len: int = 5000) -> str:
    if len(text) > max_len:
        return text[:max_len] + f"... [truncated, {len(text)} total chars]"
    return text


@router.get("/agent-jobs/{job_id}/session", response_model=SessionResponse)
def get_agent_session(
    job_id: int,
    db: Session = Depends(get_db),
) -> SessionResponse:
    job = db.query(AgentJob).filter(AgentJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Agent job not found")

    if not job.session_file:
        return SessionResponse(entries=[], summary={})

    session_path = Path(job.session_file)
    if not session_path.is_absolute():
        session_path = SESSIONS_DIR / session_path.name

    if not session_path.exists():
        return SessionResponse(entries=[], summary={"error": "Session file not found"})

    entries: list[SessionEntry] = []

    # Cumulative counters
    cum_input = 0
    cum_output = 0
    cum_cost = 0.0
    total_latency_ms = 0.0
    total_tool_duration_ms = 0.0
    tool_call_count = 0

    for line in session_path.read_text().strip().split("\n"):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue

        event_type = record.get("type", "")

        if event_type == "api_call":
            model = record.get("model", "")
            usage = record.get("usage", {})
            in_tok = usage.get("prompt_tokens", 0)
            out_tok = usage.get("completion_tokens", 0)
            latency = record.get("latency_ms", 0)
            call_cost = _calc_cost(model, in_tok, out_tok)

            cum_input += in_tok
            cum_output += out_tok
            cum_cost += call_cost
            total_latency_ms += latency

            # Parse response
            resp = record.get("response", {})
            content_text = resp.get("content") or ""
            finish_reason = resp.get("finish_reason")
            tool_calls_data = []
            for tc in resp.get("tool_calls", []):
                tool_calls_data.append({
                    "id": tc.get("id"),
                    "name": tc.get("function", {}).get("name"),
                    "arguments": tc.get("function", {}).get("arguments"),
                })

            # Include request messages (compact: role + content preview)
            req_messages = []
            for msg in record.get("request", {}).get("messages", []):
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "tool":
                    # Tool result messages — show truncated
                    content = _truncate(str(content), 500)
                elif isinstance(content, str) and len(content) > 1000:
                    content = _truncate(content, 1000)
                req_messages.append({
                    "role": role,
                    "content": content,
                    "tool_call_id": msg.get("tool_call_id"),
                })

            entries.append(SessionEntry(
                type="api_call",
                timestamp=record.get("timestamp"),
                model=model,
                usage=usage,
                latency_ms=latency,
                cost_usd=round(call_cost, 6),
                finish_reason=finish_reason,
                content=_truncate(content_text, 5000) if content_text else None,
                tool_calls=tool_calls_data if tool_calls_data else None,
                request_messages=req_messages if req_messages else None,
                cumulative_input_tokens=cum_input,
                cumulative_output_tokens=cum_output,
                cumulative_cost_usd=round(cum_cost, 6),
            ))

        elif event_type == "tool_exec":
            tool_call_count += 1
            duration = record.get("duration_ms", 0)
            total_tool_duration_ms += duration

            output = record.get("output", "")
            if isinstance(output, str):
                output = _truncate(output, 5000)
            elif isinstance(output, dict):
                serialized = json.dumps(output, default=str)
                if len(serialized) > 5000:
                    output = serialized[:5000] + f"... [truncated, {len(serialized)} total chars]"

            entries.append(SessionEntry(
                type="tool_exec",
                timestamp=record.get("timestamp"),
                name=record.get("name"),
                input=record.get("input"),
                output=output,
                duration_ms=duration,
            ))

    api_call_count = sum(1 for e in entries if e.type == "api_call")

    summary = {
        "total_entries": len(entries),
        "api_calls": api_call_count,
        "tool_execs": tool_call_count,
        "total_input_tokens": cum_input,
        "total_output_tokens": cum_output,
        "total_tokens": cum_input + cum_output,
        "total_cost_usd": round(cum_cost, 6),
        "total_latency_ms": round(total_latency_ms, 1),
        "total_tool_duration_ms": round(total_tool_duration_ms, 1),
        "avg_latency_ms": round(total_latency_ms / api_call_count, 1) if api_call_count else 0,
    }

    return SessionResponse(entries=entries, summary=summary)


@router.get("/agent-jobs/{job_id}/snapshot")
def get_agent_snapshot(
    job_id: int,
    db: Session = Depends(get_db),
):
    """Return snapshot data (items + metrics) from a completed agent job."""
    job = db.query(AgentJob).filter(AgentJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Agent job not found")

    snapshot = (job.result or {}).get("snapshot", {})
    return {
        "items": snapshot.get("items", []),
        "metrics": snapshot.get("metrics") or None,
        "tool_summary": snapshot.get("tool_summary") or None,
    }


@router.post("/agent-jobs/{job_id}/rebuild-snapshot")
def rebuild_snapshot(
    job_id: int,
    db: Session = Depends(get_db),
):
    """Rebuild snapshot from session JSONL for a completed job (backfill)."""
    row = (
        db.query(AgentJob, Brand.slug)
        .join(Brand, AgentJob.brand_id == Brand.id)
        .filter(AgentJob.id == job_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Agent job not found")

    job, brand_slug = row
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Job is not completed")
    if not job.session_file:
        raise HTTPException(status_code=400, detail="No session file for this job")

    session_path = Path(job.session_file)
    if not session_path.is_absolute():
        session_path = SESSIONS_DIR / session_path.name
    if not session_path.exists():
        raise HTTPException(status_code=400, detail="Session file not found on disk")

    # Parse session JSONL to extract item IDs and tool info
    item_ids: list[int] = []
    tool_counts: dict[str, int] = {}
    scrape_results: dict[str, dict] = {}
    errors: list[str] = []
    total_tool_calls = 0

    for line in session_path.read_text().strip().split("\n"):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("type") != "tool_exec":
            continue

        name = record.get("name", "")
        total_tool_calls += 1
        tool_counts[name] = tool_counts.get(name, 0) + 1
        output = record.get("output", "")

        # Parse output (may be string or dict)
        if isinstance(output, str):
            try:
                output = json.loads(output)
            except (json.JSONDecodeError, TypeError):
                output = {}

        if name == "save_items" and isinstance(output, dict):
            csv_text = output.get("items_csv", "")
            for csv_line in csv_text.strip().split("\n")[1:]:
                parts = csv_line.split("|")
                if parts and parts[0].strip().isdigit():
                    item_ids.append(int(parts[0].strip()))

        elif name == "save_price_listings" and isinstance(output, dict):
            for err in output.get("errors", []):
                if isinstance(err, str) and err not in errors:
                    errors.append(err)

        elif name in ("crawl_products", "scrape_shopify_store") and isinstance(output, dict):
            inp = record.get("input", {})
            if isinstance(inp, str):
                try:
                    inp = json.loads(inp)
                except (json.JSONDecodeError, TypeError):
                    inp = {}
            if name == "crawl_products":
                import re
                url = inp.get("start_url", "") if isinstance(inp, dict) else ""
                match = re.match(r"https?://([^/]+)", url)
                key = match.group(1) if match else "unknown"
                scrape_results[key] = {
                    "products_found": output.get("products_found", 0),
                    "source_url": url,
                }
            else:
                domain = output.get("domain", inp.get("domain", "unknown") if isinstance(inp, dict) else "unknown")
                scrape_results[domain] = {
                    "products_found": output.get("count", 0),
                    "source_url": f"https://{domain}",
                }

    # Deduplicate
    seen: set[int] = set()
    unique_ids: list[int] = []
    for iid in item_ids:
        if iid not in seen:
            seen.add(iid)
            unique_ids.append(iid)

    # Query items + price_listings
    items_data: list[dict] = []
    if unique_ids:
        items = db.query(Item).filter(Item.id.in_(unique_ids)).all()

        listing_rows = (
            db.query(PriceListing, Retailer.slug, Retailer.name)
            .join(Retailer, PriceListing.retailer_id == Retailer.id)
            .filter(PriceListing.item_id.in_(unique_ids))
            .all()
        )
        listings_by_item: dict[int, list[dict]] = {}
        for pl, r_slug, r_name in listing_rows:
            listings_by_item.setdefault(pl.item_id, []).append({
                "id": pl.id,
                "retailer_slug": r_slug,
                "retailer_name": r_name,
                "price_jpy": pl.price_jpy,
                "price_usd": float(pl.price_usd) if pl.price_usd is not None else None,
                "in_stock": pl.in_stock,
                "available_sizes": pl.available_sizes,
                "url": pl.url,
                "last_checked_at": pl.last_checked_at.isoformat() if pl.last_checked_at else None,
            })

        for item in items:
            items_data.append({
                "id": item.id,
                "brand_id": item.brand_id,
                "collection_id": item.collection_id,
                "name_en": item.name_en,
                "name_ja": item.name_ja,
                "item_type": item.item_type,
                "price_jpy": item.price_jpy,
                "price_usd": float(item.price_usd) if item.price_usd is not None else None,
                "compare_at_price_usd": float(item.compare_at_price_usd) if item.compare_at_price_usd is not None else None,
                "material": item.material,
                "sizes": item.sizes,
                "primary_image_url": item.primary_image_url,
                "source_url": item.source_url,
                "external_id": item.external_id,
                "handle": item.handle,
                "vendor": item.vendor,
                "product_type_raw": item.product_type_raw,
                "tags": item.tags,
                "colors": item.colors,
                "season_code": item.season_code,
                "sku": item.sku,
                "in_stock": item.in_stock,
                "price_listings": listings_by_item.get(item.id, []),
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            })

    # Compute metrics
    prices_usd = [i["price_usd"] for i in items_data if i.get("price_usd") is not None]
    all_listings = []
    channels: set[str] = set()
    for i in items_data:
        for pl in i.get("price_listings", []):
            all_listings.append(pl)
            if pl.get("retailer_slug"):
                channels.add(pl["retailer_slug"])

    from datetime import datetime, timezone
    snapshot = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "items": items_data,
        "metrics": {
            "items_total": len(items_data),
            "items_with_images": sum(1 for i in items_data if i.get("primary_image_url")),
            "items_with_prices": len(prices_usd),
            "items_in_stock": sum(1 for i in items_data if i.get("in_stock")),
            "listings_total": len(all_listings),
            "listings_with_urls": sum(1 for pl in all_listings if pl.get("url")),
            "channels": sorted(channels),
            "channels_count": len(channels),
            "price_range_usd": [min(prices_usd), max(prices_usd)] if prices_usd else None,
            "avg_price_usd": round(sum(prices_usd) / len(prices_usd), 2) if prices_usd else None,
        },
        "tool_summary": {
            "total_tool_calls": total_tool_calls,
            "tools_used": tool_counts,
            "scrape_results": scrape_results,
            "errors": errors,
        },
    }

    # Update job result
    result = dict(job.result or {})
    result["snapshot"] = snapshot
    job.result = result
    db.commit()

    return {
        "status": "ok",
        "items_count": len(items_data),
        "metrics": snapshot["metrics"],
    }


@router.get("/agent-brands")
def get_agent_brands(db: Session = Depends(get_db)) -> dict:
    brands = db.query(Brand.slug).order_by(Brand.slug).all()
    return {"brands": [b.slug for b in brands]}


def _job_to_response(job: AgentJob, brand_slug: str) -> AgentJobResponse:
    return AgentJobResponse(
        id=job.id,
        brand_slug=brand_slug,
        model=job.model,
        status=job.status,
        celery_task_id=job.celery_task_id,
        started_at=job.started_at,
        completed_at=job.completed_at,
        tool_calls=job.tool_calls,
        total_input_tokens=job.total_input_tokens,
        total_output_tokens=job.total_output_tokens,
        total_cost_usd=job.total_cost_usd,
        session_file=job.session_file,
        result=job.result,
        errors=job.errors,
        created_at=job.created_at,
    )
