from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from fastmcp import Client as FastMCPClient


@dataclass
class MCPToolCall:
    tool: str
    arguments: dict[str, Any] = field(default_factory=dict)


class MCPClient:
    """Client for calling MCP tools across domains."""

    def __init__(self, base_urls: dict[str, str]) -> None:
        self.base_urls = base_urls

    def _resolve_domain(self, tool_name: str) -> str:
        domain = tool_name.split(".")[0]
        if domain not in self.base_urls:
            raise ValueError(f"Unknown domain for tool '{tool_name}': '{domain}'")
        return domain

    async def call(self, tool: str, **kwargs: Any) -> Any:
        domain = self._resolve_domain(tool)
        url = self.base_urls[domain]
        async with FastMCPClient(url) as client:
            return await client.call_tool(tool, kwargs)

    async def call_parallel(self, calls: list[MCPToolCall]) -> list[Any]:
        tasks = [self.call(c.tool, **c.arguments) for c in calls]
        return await asyncio.gather(*tasks)
