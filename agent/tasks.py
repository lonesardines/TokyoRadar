"""Celery task wrappers for running the agent in production."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from agent.celery_app import app

logger = logging.getLogger(__name__)

SESSIONS_DIR = Path("sessions")


def _update_job_status(job_id: int, **kwargs) -> None:
    """Update an AgentJob record in the database."""
    from sqlalchemy import update
    from tokyoradar_shared.database import SessionLocal
    from tokyoradar_shared.models import AgentJob

    with SessionLocal() as db:
        db.execute(
            update(AgentJob).where(AgentJob.id == job_id).values(**kwargs)
        )
        db.commit()


@app.task(name="agent.tasks.research_brand")
def research_brand(
    brand_slug: str,
    model: str = "qwen-plus",
    job_id: int | None = None,
) -> dict:
    """Run the agent to research a brand across all channels.

    Scrapes available sources, matches products, and saves price listings.
    """
    from agent.core import AgentLoop
    from agent.prompts import ORCHESTRATOR_PROMPT
    from agent.recorder import SessionRecorder
    from agent.tools import get_all_tools
    from agent.tracker import TokenTracker

    # Mark job as running
    if job_id:
        _update_job_status(job_id, status="running", started_at=datetime.now())

    try:
        tracker = TokenTracker()
        recorder = SessionRecorder(SESSIONS_DIR)

        # Write session_file path immediately so the session endpoint can read
        # the JSONL file while the agent is still running (enables live view).
        if job_id:
            _update_job_status(job_id, session_file=str(recorder.file))

        loop = AgentLoop(
            tools=get_all_tools(),
            system_prompt=ORCHESTRATOR_PROMPT,
            model=model,
            tracker=tracker,
            recorder=recorder,
        )

        message = (
            f"Research {brand_slug}: scrape all available channels, "
            f"match products across sources, and save price listings."
        )
        result = loop.run(message)

        summary = {
            "brand_slug": brand_slug,
            "final_text": result.final_text,
            "tool_calls": len(result.tool_calls),
            "session_file": str(recorder.file),
            "usage": tracker.summary(),
        }

        logger.info(
            "Agent research complete for %s: %d tool calls, $%.4f cost",
            brand_slug,
            len(result.tool_calls),
            tracker.total_cost,
        )

        # Mark job as completed
        if job_id:
            usage = tracker.summary()

            # Build snapshot of items + metrics from this run
            from agent.snapshot import build_snapshot
            try:
                snapshot = build_snapshot(str(recorder.file), brand_slug)
            except Exception:
                logger.exception("Failed to build snapshot for %s", brand_slug)
                snapshot = None

            job_result = {"final_text": result.final_text}
            if snapshot:
                job_result["snapshot"] = snapshot

            _update_job_status(
                job_id,
                status="completed",
                completed_at=datetime.now(),
                tool_calls=len(result.tool_calls),
                total_input_tokens=usage.get("total_input_tokens", 0),
                total_output_tokens=usage.get("total_output_tokens", 0),
                total_cost_usd=tracker.total_cost,
                session_file=str(recorder.file),
                result=job_result,
            )

        return summary

    except Exception as exc:
        logger.exception("Agent research failed for %s", brand_slug)
        if job_id:
            _update_job_status(
                job_id,
                status="failed",
                completed_at=datetime.now(),
                errors={"error": str(exc)},
            )
        raise
