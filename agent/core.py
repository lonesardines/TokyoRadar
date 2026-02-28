"""AgentLoop: the main while-loop that talks to the LLM with tool use."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from openai import OpenAI

from agent.tracker import TokenTracker
from agent.recorder import SessionRecorder, SessionReplayer

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 20  # safety limit to prevent infinite loops
# Keep the N most recent tool outputs in full; mask older ones
OBSERVATION_WINDOW = 4
# Max chars for a single tool output before inline truncation
TOOL_OUTPUT_MAX_CHARS = 4000


@dataclass
class ToolCall:
    """Record of a single tool invocation."""
    name: str
    input: dict
    output: Any
    duration_ms: float


@dataclass
class AgentResult:
    """Result of a complete agent run."""
    messages: list[dict] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)
    final_text: str = ""
    tracker: TokenTracker | None = None

    def to_dict(self) -> dict:
        return {
            "final_text": self.final_text,
            "tool_calls": [
                {"name": tc.name, "input": tc.input, "output": tc.output,
                 "duration_ms": tc.duration_ms}
                for tc in self.tool_calls
            ],
            "usage": self.tracker.summary() if self.tracker else {},
        }


class AgentLoop:
    """Drives a multi-turn LLM conversation with tool use via OpenAI-compatible API."""

    def __init__(
        self,
        tools: dict[str, Any],
        system_prompt: str,
        model: str = "qwen-plus",
        api_key: str | None = None,
        base_url: str | None = None,
        tracker: TokenTracker | None = None,
        recorder: SessionRecorder | None = None,
        replayer: SessionReplayer | None = None,
        dry_run: bool = False,
    ) -> None:
        from tokyoradar_shared.config import settings

        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools  # dict[name, ToolDef]
        self.tracker = tracker or TokenTracker()
        self.recorder = recorder
        self.replayer = replayer
        self.dry_run = dry_run

        if replayer is None:
            if model.startswith("gemini-"):
                _api_key = api_key or settings.GEMINI_API_KEY
                _base_url = base_url or settings.GEMINI_BASE_URL
            else:
                _api_key = api_key or settings.DASHSCOPE_API_KEY
                _base_url = base_url or settings.DASHSCOPE_BASE_URL
            self.client = OpenAI(api_key=_api_key, base_url=_base_url)
        else:
            self.client = None  # replay mode — no API calls

    def run(self, user_message: str) -> AgentResult:
        """Main agent loop with tool use."""
        messages: list[dict] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]
        result = AgentResult(tracker=self.tracker)

        for iteration in range(MAX_ITERATIONS):
            response = self._call_api(messages)
            choice = response.choices[0]

            # Append assistant message to history
            assistant_msg = self._choice_to_dict(choice)
            messages.append(assistant_msg)

            # If no tool calls, we're done
            if choice.finish_reason != "tool_calls" or not choice.message.tool_calls:
                result.final_text = choice.message.content or ""
                break

            # Execute each tool call
            for tool_call in choice.message.tool_calls:
                tc_result = self._execute_tool(tool_call)
                result.tool_calls.append(tc_result)

                # Append tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tc_result.output, default=str),
                })
        else:
            logger.warning("Agent hit max iterations (%d)", MAX_ITERATIONS)
            result.final_text = "(max iterations reached)"

        result.messages = messages
        return result

    def _call_api(self, messages: list[dict]) -> Any:
        """Call the LLM API with tracking and recording.

        Applies observation masking: only the most recent OBSERVATION_WINDOW
        tool outputs are kept in full. Older tool outputs are replaced with a
        short placeholder to prevent context bloat.
        """
        if self.replayer:
            return self._replay_api_call()

        # Build tool schemas for the API
        tool_schemas = [
            {
                "type": "function",
                "function": {
                    "name": td.name,
                    "description": td.description,
                    "parameters": td.input_schema,
                },
            }
            for td in self.tools.values()
        ]

        # Apply observation masking — keep recent tool outputs, mask older ones
        masked_messages = _mask_old_observations(messages, OBSERVATION_WINDOW)

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": masked_messages,
        }
        if tool_schemas:
            kwargs["tools"] = tool_schemas

        t0 = time.monotonic()
        response = self.client.chat.completions.create(**kwargs)
        latency_ms = (time.monotonic() - t0) * 1000

        # Track usage
        self.tracker.record(response, latency_ms, self.model)

        # Record session
        if self.recorder:
            self.recorder.record_api_call(
                messages=masked_messages,
                response_dict=_response_to_dict(response),
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                },
                latency_ms=latency_ms,
                model=self.model,
            )

        return response

    def _replay_api_call(self) -> Any:
        """Return a mock response from the replayer."""
        resp_dict = self.replayer.next_api_response()
        if resp_dict is None:
            raise RuntimeError("Replayer exhausted: no more API responses")
        return _dict_to_mock_response(resp_dict)

    @staticmethod
    def _validate_tool_input(name: str, args: dict) -> dict | None:
        """Validate tool arguments, return error dict if fabrication detected."""
        # Catch fabricated placeholder URLs
        _PLACEHOLDER_PATTERNS = ("/12345", "/item/0", "/products/unknown", "/example")

        if name == "save_price_listings":
            for listing in args.get("listings", []):
                slug = listing.get("retailer_slug", "")
                if not slug:
                    return {"error": "retailer_slug is required for each listing."}
                # Common fabrication: using brand name as retailer slug
                if slug.endswith("-official") or slug.endswith("-store"):
                    return {
                        "error": f"retailer_slug '{slug}' is not valid. "
                        f"Use ONLY slugs from list_retailers() or "
                        f"valid_retailer_slugs in get_brand_info. "
                        f"For Japanese official stores use 'brand-official-jp'."
                    }
                url = listing.get("url", "")
                if url and any(p in url for p in _PLACEHOLDER_PATTERNS):
                    return {
                        "error": f"URL '{url}' looks fabricated (placeholder). "
                        f"Only use URLs returned by scraping tools."
                    }

        if name == "save_items":
            for item in args.get("items", []):
                url = item.get("source_url", "")
                if url and any(p in url for p in _PLACEHOLDER_PATTERNS):
                    return {
                        "error": f"source_url '{url}' looks fabricated. "
                        f"Only use URLs from scraping tool outputs."
                    }

        return None

    def _execute_tool(self, tool_call) -> ToolCall:
        """Execute a single tool call, or return mock/cached in dry-run/replay mode."""
        name = tool_call.function.name
        try:
            args = json.loads(tool_call.function.arguments)
        except (json.JSONDecodeError, TypeError):
            args = {}

        if self.replayer:
            output = self.replayer.next_tool_result()
            if output is None:
                output = {"error": "replayer exhausted"}
            return ToolCall(name=name, input=args, output=output, duration_ms=0)

        if self.dry_run:
            output = {"dry_run": True, "tool": name, "args": args,
                       "message": f"Dry-run: {name} was not executed"}
            return ToolCall(name=name, input=args, output=output, duration_ms=0)

        # Validate inputs before execution (catch fabricated data)
        validation_error = self._validate_tool_input(name, args)
        if validation_error:
            logger.warning("Validation rejected %s: %s", name, validation_error)
            return ToolCall(name=name, input=args, output=validation_error, duration_ms=0)

        # Live execution
        tool_def = self.tools.get(name)
        if tool_def is None:
            output = {"error": f"Unknown tool: {name}"}
            return ToolCall(name=name, input=args, output=output, duration_ms=0)

        t0 = time.monotonic()
        try:
            output = tool_def.handler(**args)
        except Exception as exc:
            logger.exception("Tool %s failed", name)
            output = {"error": str(exc)}
        duration_ms = (time.monotonic() - t0) * 1000

        if self.recorder:
            self.recorder.record_tool_execution(
                tool_name=name,
                tool_input=args,
                tool_output=output,
                duration_ms=duration_ms,
            )

        return ToolCall(name=name, input=args, output=output, duration_ms=duration_ms)

    @staticmethod
    def _choice_to_dict(choice) -> dict:
        """Convert an OpenAI choice to a serializable dict for message history."""
        msg: dict[str, Any] = {"role": "assistant"}
        if choice.message.content:
            msg["content"] = choice.message.content
        # Capture reasoning_content from deep-thinking models (qwen3.5-plus etc.)
        reasoning = getattr(choice.message, "reasoning_content", None)
        if reasoning:
            msg["reasoning_content"] = reasoning
        if choice.message.tool_calls:
            msg["tool_calls"] = []
            for tc in choice.message.tool_calls:
                tc_dict: dict[str, Any] = {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                # Preserve Gemini thought_signature (extra_content) for multi-turn tool use
                extra_content = getattr(tc, "extra_content", None)
                if extra_content:
                    tc_dict["extra_content"] = extra_content
                msg["tool_calls"].append(tc_dict)
        return msg


def _mask_old_observations(messages: list[dict], window: int) -> list[dict]:
    """Aggressively compress older messages to reduce context size.

    1. Old tool outputs (beyond the most recent `window`) → short placeholder.
    2. Old assistant messages that only contain tool_calls (no text content)
       → compressed to a one-line summary of which tools were called.
    3. Recent tool outputs that exceed TOOL_OUTPUT_MAX_CHARS → inline truncation.
    """
    # Find indices of all tool messages
    tool_indices = [i for i, m in enumerate(messages) if m.get("role") == "tool"]

    if len(tool_indices) <= window:
        mask_set: set[int] = set()
    else:
        mask_set = set(tool_indices[:-window])

    # Find assistant messages whose tool outputs have been masked
    # (the assistant msg right before a masked tool msg)
    old_assistant_set: set[int] = set()
    for ti in mask_set:
        for j in range(ti - 1, -1, -1):
            if messages[j].get("role") == "assistant":
                old_assistant_set.add(j)
                break

    masked = []
    for i, msg in enumerate(messages):
        if i in mask_set:
            content = msg.get("content", "")
            masked.append({
                **msg,
                "content": f"[output omitted — {len(content)} chars]",
            })
        elif i in old_assistant_set and msg.get("tool_calls") and not msg.get("content"):
            # Compress old assistant tool_calls to a short summary
            tc_names = [tc["function"]["name"] for tc in msg["tool_calls"]]
            masked.append({
                "role": "assistant",
                "content": f"[called: {', '.join(tc_names)}]",
                "tool_calls": msg["tool_calls"],  # keep for API compatibility
            })
        elif msg.get("role") == "tool" and i not in mask_set:
            # Truncate oversized recent tool outputs
            content = msg.get("content", "")
            if len(content) > TOOL_OUTPUT_MAX_CHARS:
                masked.append({
                    **msg,
                    "content": content[:TOOL_OUTPUT_MAX_CHARS]
                    + f"\n... [truncated, {len(content)} total chars]",
                })
            else:
                masked.append(msg)
        else:
            masked.append(msg)
    return masked


def _response_to_dict(response) -> dict:
    """Serialize an OpenAI ChatCompletion response to a dict."""
    choice = response.choices[0]
    result: dict[str, Any] = {
        "finish_reason": choice.finish_reason,
        "content": choice.message.content,
    }
    # Capture reasoning content from deep-thinking models
    reasoning = getattr(choice.message, "reasoning_content", None)
    if reasoning:
        result["reasoning_content"] = reasoning
    if choice.message.tool_calls:
        tc_list = []
        for tc in choice.message.tool_calls:
            tc_dict: dict[str, Any] = {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            extra_content = getattr(tc, "extra_content", None)
            if extra_content:
                tc_dict["extra_content"] = extra_content
            tc_list.append(tc_dict)
        result["tool_calls"] = tc_list
    return result


class _MockMessage:
    def __init__(self, content, tool_calls):
        self.content = content
        self.tool_calls = tool_calls


class _MockFunctionCall:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class _MockToolCall:
    def __init__(self, tc_dict):
        self.id = tc_dict["id"]
        self.function = _MockFunctionCall(
            tc_dict["function"]["name"],
            tc_dict["function"]["arguments"],
        )


class _MockChoice:
    def __init__(self, resp_dict):
        self.finish_reason = resp_dict.get("finish_reason", "stop")
        tool_calls = None
        if resp_dict.get("tool_calls"):
            tool_calls = [_MockToolCall(tc) for tc in resp_dict["tool_calls"]]
        self.message = _MockMessage(
            content=resp_dict.get("content"),
            tool_calls=tool_calls,
        )


class _MockUsage:
    def __init__(self):
        self.prompt_tokens = 0
        self.completion_tokens = 0


class _MockResponse:
    def __init__(self, resp_dict):
        self.choices = [_MockChoice(resp_dict)]
        self.usage = _MockUsage()


def _dict_to_mock_response(resp_dict: dict):
    return _MockResponse(resp_dict)
