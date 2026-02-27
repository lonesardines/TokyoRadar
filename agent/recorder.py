"""Session recording and replay for agent debugging."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class SessionRecorder:
    """Records full agent sessions to JSONL files for replay and debugging."""

    def __init__(self, session_dir: Path) -> None:
        session_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.file = session_dir / f"{self.session_id}.jsonl"
        self._entries: list[dict] = []

    def record_api_call(
        self,
        messages: list[dict],
        response_dict: dict,
        usage: dict,
        latency_ms: float,
        model: str,
    ) -> None:
        """Append one API round-trip to the session file."""
        entry = {
            "type": "api_call",
            "model": model,
            "request": {"messages": messages},
            "response": response_dict,
            "usage": usage,
            "latency_ms": round(latency_ms, 1),
            "timestamp": datetime.now().isoformat(),
        }
        self._append(entry)

    def record_tool_execution(
        self,
        tool_name: str,
        tool_input: dict,
        tool_output: Any,
        duration_ms: float,
    ) -> None:
        """Append tool execution to the session file."""
        entry = {
            "type": "tool_exec",
            "name": tool_name,
            "input": tool_input,
            "output": tool_output,
            "duration_ms": round(duration_ms, 1),
            "timestamp": datetime.now().isoformat(),
        }
        self._append(entry)

    def _append(self, entry: dict) -> None:
        self._entries.append(entry)
        with open(self.file, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    @property
    def entry_count(self) -> int:
        return len(self._entries)


class SessionReplayer:
    """Replays a recorded session without making real API calls or tool executions."""

    def __init__(self, session_file: Path) -> None:
        self.entries = [
            json.loads(line)
            for line in session_file.read_text().splitlines()
            if line.strip()
        ]
        self._api_cursor = 0
        self._tool_cursor = 0

    @property
    def api_calls(self) -> list[dict]:
        return [e for e in self.entries if e["type"] == "api_call"]

    @property
    def tool_execs(self) -> list[dict]:
        return [e for e in self.entries if e["type"] == "tool_exec"]

    def next_api_response(self) -> dict | None:
        """Return next recorded API response (no actual API call)."""
        calls = self.api_calls
        if self._api_cursor >= len(calls):
            return None
        entry = calls[self._api_cursor]
        self._api_cursor += 1
        return entry["response"]

    def next_tool_result(self) -> Any | None:
        """Return next recorded tool result (no actual execution)."""
        execs = self.tool_execs
        if self._tool_cursor >= len(execs):
            return None
        entry = execs[self._tool_cursor]
        self._tool_cursor += 1
        return entry["output"]

    def summary(self) -> dict:
        """Return summary stats for the recorded session."""
        api_calls = self.api_calls
        total_input = sum(c.get("usage", {}).get("prompt_tokens", 0) for c in api_calls)
        total_output = sum(c.get("usage", {}).get("completion_tokens", 0) for c in api_calls)
        total_latency = sum(c.get("latency_ms", 0) for c in api_calls)
        return {
            "api_calls": len(api_calls),
            "tool_executions": len(self.tool_execs),
            "total_entries": len(self.entries),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_latency_ms": round(total_latency, 1),
        }
