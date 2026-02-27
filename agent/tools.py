"""Tool definitions for the agent — tools are now discovered from MCP servers."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class ToolDef:
    """Definition of a tool the agent can call."""
    name: str
    description: str
    input_schema: dict
    handler: Callable[..., Any]


TOOL_REGISTRY: dict[str, ToolDef] = {}


def tool(name: str, description: str, input_schema: dict):
    """Decorator to register a local tool."""
    def decorator(fn: Callable) -> Callable:
        TOOL_REGISTRY[name] = ToolDef(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=fn,
        )
        return fn
    return decorator


@tool(
    name="web_search",
    description=(
        "Search the web using DuckDuckGo. Use when buy_guide is empty or brand is not "
        "in the DB. Returns top 5 results as CSV: title|url|snippet."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query, e.g. 'wtaps official store online shop'",
            },
        },
        "required": ["query"],
    },
)
def web_search(query: str) -> dict:
    """Search the web via DuckDuckGo and return top 5 results."""
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return {"error": "duckduckgo-search not installed"}

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))

        if not results:
            return {"query": query, "count": 0, "results_csv": ""}

        lines = ["title|url|snippet"]
        for r in results:
            title = (r.get("title") or "").replace("|", "-")
            url = r.get("href") or r.get("link") or ""
            snippet = (r.get("body") or "").replace("|", "-")[:200]
            lines.append(f"{title}|{url}|{snippet}")

        return {
            "query": query,
            "count": len(results),
            "results_csv": "\n".join(lines),
        }
    except Exception as exc:
        return {"query": query, "error": str(exc)}


def get_all_tools() -> dict[str, ToolDef]:
    """Discover tools from MCP servers and merge with any local tools."""
    from tokyoradar_shared.config import settings
    from agent.mcp_client import MCPToolAdapter

    adapter = MCPToolAdapter()
    tools: dict[str, ToolDef] = {}

    # Scraper MCP tools (scrape_shopify_store, fetch_page, scrape_sitemap, etc.)
    tools.update(adapter.get_tool_defs(settings.SCRAPER_MCP_URL))

    # Backend DB MCP tools (get_brand_info, search_items_db, save_items, list_retailers, etc.)
    tools.update(adapter.get_tool_defs(settings.BACKEND_MCP_URL))

    # Any locally-registered tools
    tools.update(TOOL_REGISTRY)

    logger.info("Loaded %d tools: %s", len(tools), list(tools.keys()))
    return tools
