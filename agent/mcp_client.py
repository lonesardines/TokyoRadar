"""MCP Client adapter — connects to MCP servers and wraps tools as ToolDefs."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from agent.tools import ToolDef

logger = logging.getLogger(__name__)


class MCPToolAdapter:
    """Discovers tools from MCP servers and wraps them as ToolDefs for the AgentLoop."""

    def get_tool_defs(self, server_url: str) -> dict[str, ToolDef]:
        """Connect to an MCP server, list tools, and return wrapped ToolDefs."""
        try:
            return asyncio.run(self._discover_tools(server_url))
        except Exception as exc:
            logger.error("Failed to connect to MCP server %s: %s", server_url, exc)
            return {}

    async def _discover_tools(self, server_url: str) -> dict[str, ToolDef]:
        tools: dict[str, ToolDef] = {}

        async with streamablehttp_client(server_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()

                for tool_info in result.tools:
                    name = tool_info.name
                    description = tool_info.description or ""
                    input_schema = tool_info.inputSchema or {"type": "object", "properties": {}}

                    handler = self._make_handler(server_url, name)

                    tools[name] = ToolDef(
                        name=name,
                        description=description,
                        input_schema=input_schema,
                        handler=handler,
                    )

        return tools

    def _make_handler(self, server_url: str, tool_name: str):
        """Create a synchronous handler that calls the MCP tool."""

        def handler(**kwargs: Any) -> Any:
            try:
                return asyncio.run(self._call_tool(server_url, tool_name, kwargs))
            except Exception as exc:
                logger.error("MCP tool %s failed: %s", tool_name, exc)
                return {"error": f"MCP tool call failed: {exc}"}

        return handler

    async def _call_tool(
        self, server_url: str, tool_name: str, arguments: dict, _retries: int = 2,
    ) -> Any:
        last_exc: Exception | None = None
        for attempt in range(1 + _retries):
            try:
                return await self._call_tool_once(server_url, tool_name, arguments)
            except Exception as exc:
                last_exc = exc
                if attempt < _retries:
                    logger.warning(
                        "MCP tool %s attempt %d failed (%s), retrying...",
                        tool_name, attempt + 1, exc,
                    )
                    await asyncio.sleep(0.5 * (attempt + 1))
        raise last_exc  # type: ignore[misc]

    async def _call_tool_once(self, server_url: str, tool_name: str, arguments: dict) -> Any:
        async with streamablehttp_client(server_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=arguments)

                # MCP returns content as list of content blocks
                if result.content:
                    # If single text block, try to parse as JSON
                    if len(result.content) == 1 and result.content[0].type == "text":
                        text = result.content[0].text
                        try:
                            return json.loads(text)
                        except (json.JSONDecodeError, TypeError):
                            return {"result": text}
                    # Multiple blocks — concatenate text
                    texts = [c.text for c in result.content if hasattr(c, "text")]
                    combined = "\n".join(texts)
                    try:
                        return json.loads(combined)
                    except (json.JSONDecodeError, TypeError):
                        return {"result": combined}

                return {"result": None}
