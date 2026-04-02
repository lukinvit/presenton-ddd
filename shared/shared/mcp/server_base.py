from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastmcp import FastMCP


class DomainMCPServer:
    """Base MCP server for a bounded context domain."""

    def __init__(self, name: str, port: int) -> None:
        self.name = name
        self.port = port
        self.mcp = FastMCP(name=f"presenton-{name}")
        self.registered_tools: dict[str, Callable[..., Any]] = {}
        self._register_health()

    def _register_health(self) -> None:
        @self.tool("health.check")
        async def health_check() -> dict[str, str]:
            return {"status": "ok", "domain": self.name}

    def tool(self, name: str) -> Callable[..., Any]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.registered_tools[name] = func
            self.mcp.tool(name=name)(func)
            return func

        return decorator

    async def start(self) -> None:
        await self.mcp.run_async(transport="sse", port=self.port)
