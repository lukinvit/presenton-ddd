"""External MCP server that aggregates all domain MCP tools."""

from __future__ import annotations

import asyncio
from typing import Any

from fastmcp import Client as FastMCPClient
from fastmcp import FastMCP
from mcp_gateway.router import MCPRouter

_GATEWAY_PORT = 8001


class MCPGatewayServer:
    """Aggregating MCP server.

    On startup it fetches the tool list from every domain MCP server and
    re-registers each tool locally, forwarding calls to the correct domain.
    """

    def __init__(
        self,
        domain_urls: dict[str, str] | None = None,
        port: int = _GATEWAY_PORT,
    ) -> None:
        self.router = MCPRouter(domain_urls)
        self.port = port
        self.mcp = FastMCP(name="presenton-gateway")

    async def _register_domain_tools(self, domain: str, url: str) -> None:
        """Connect to one domain MCP server and mirror its tools."""
        try:
            async with FastMCPClient(url) as client:
                tools = await client.list_tools()
                for tool in tools:
                    tool_name = tool.name

                    async def _handler(
                        _url: str = url, _tool: str = tool_name, **kwargs: Any
                    ) -> Any:
                        async with FastMCPClient(_url) as c:
                            return await c.call_tool(_tool, kwargs)

                    self.mcp.tool(name=tool_name)(_handler)
        except Exception as exc:
            # Log and continue — the gateway starts even if a domain is down
            import structlog

            log = structlog.get_logger(__name__)
            log.warning("mcp_gateway.domain_unavailable", domain=domain, url=url, error=str(exc))

    async def build(self) -> None:
        """Discover and register tools from all domain servers."""
        await asyncio.gather(
            *[
                self._register_domain_tools(domain, url)
                for domain, url in self.router.domain_urls.items()
            ]
        )

    async def start(self) -> None:
        """Build tool registry then start serving."""
        await self.build()
        await self.mcp.run_async(transport="sse", port=self.port)


def main() -> None:
    server = MCPGatewayServer(port=_GATEWAY_PORT)
    asyncio.run(server.start())


if __name__ == "__main__":
    main()
