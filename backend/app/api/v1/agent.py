"""Agent admin API — trigger research jobs, view status, inspect sessions."""

from __future__ import annotations

import json
from pathlib import Path

from celery import Celery
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import AgentJob, Brand
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
            started_at=job.started_at,
            completed_at=job.completed_at,
            created_at=job.created_at,
        ))

    return PaginatedResponse(data=data, total=total, page=page, per_page=per_page)


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
