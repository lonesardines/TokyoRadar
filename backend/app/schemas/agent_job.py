from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AgentJobTrigger(BaseModel):
    brand_slug: str
    model: str = "qwen-plus"


class AgentJobResponse(BaseModel):
    id: int
    brand_slug: str
    model: str
    status: str
    celery_task_id: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    tool_calls: int | None = None
    total_input_tokens: int | None = None
    total_output_tokens: int | None = None
    total_cost_usd: float | None = None
    session_file: str | None = None
    result: dict | None = None
    errors: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentJobListResponse(BaseModel):
    id: int
    brand_slug: str
    model: str
    status: str
    tool_calls: int | None = None
    total_input_tokens: int | None = None
    total_output_tokens: int | None = None
    total_cost_usd: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionEntry(BaseModel):
    type: str  # "api_call" | "tool_exec"
    timestamp: str | None = None
    # api_call fields
    model: str | None = None
    usage: dict | None = None
    latency_ms: float | None = None
    cost_usd: float | None = None
    finish_reason: str | None = None
    content: str | None = None
    tool_calls: list[dict] | None = None
    request_messages: list[dict] | None = None
    cumulative_input_tokens: int | None = None
    cumulative_output_tokens: int | None = None
    cumulative_cost_usd: float | None = None
    # tool_exec fields
    name: str | None = None
    input: Any = None
    output: Any = None
    duration_ms: float | None = None


class SessionResponse(BaseModel):
    entries: list[SessionEntry]
    summary: dict
