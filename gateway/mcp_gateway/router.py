"""Tool name -> domain MCP URL routing."""

from __future__ import annotations

# Default domain -> MCP SSE URL mapping
DEFAULT_DOMAIN_URLS: dict[str, str] = {
    "presentation": "http://presentation:8011/sse",
    "style": "http://style:8021/sse",
    "content": "http://content:8031/sse",
    "rendering": "http://rendering:8041/sse",
    "media": "http://media:8051/sse",
    "agent": "http://agent:8061/sse",
    "auth": "http://auth:8071/sse",
    "identity": "http://identity:8081/sse",
    "web_access": "http://web_access:8091/sse",
    "export": "http://export:8101/sse",
}


class MCPRouter:
    """Routes an MCP tool name to the correct domain URL.

    Tool names follow the convention ``<domain>.<tool>`` (e.g.
    ``presentation.create``). The router extracts the prefix before the first
    dot and looks it up in the domain URL map.
    """

    def __init__(self, domain_urls: dict[str, str] | None = None) -> None:
        self.domain_urls: dict[str, str] = (
            domain_urls if domain_urls is not None else dict(DEFAULT_DOMAIN_URLS)
        )

    def resolve(self, tool_name: str) -> str:
        """Return the MCP URL for *tool_name*.

        Raises:
            ValueError: If the domain prefix is not registered.
        """
        parts = tool_name.split(".", maxsplit=1)
        if len(parts) < 2:
            raise ValueError(
                f"Tool name '{tool_name}' has no domain prefix. Expected format: '<domain>.<tool>'"
            )
        domain = parts[0]
        if domain not in self.domain_urls:
            known = ", ".join(sorted(self.domain_urls))
            raise ValueError(
                f"Unknown domain '{domain}' in tool '{tool_name}'. Known domains: {known}"
            )
        return self.domain_urls[domain]

    def all_urls(self) -> list[str]:
        """Return all registered domain URLs."""
        return list(self.domain_urls.values())
