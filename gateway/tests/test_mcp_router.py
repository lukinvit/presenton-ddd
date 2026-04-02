"""Tests for MCPRouter tool prefix resolution."""

from __future__ import annotations

import pytest
from mcp_gateway.router import DEFAULT_DOMAIN_URLS, MCPRouter

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def router() -> MCPRouter:
    return MCPRouter()


@pytest.fixture
def custom_router() -> MCPRouter:
    return MCPRouter({"presentation": "http://pres:9000/sse", "style": "http://style:9001/sse"})


# ---------------------------------------------------------------------------
# Happy-path resolution
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "tool_name,expected_domain",
    [
        ("presentation.create", "presentation"),
        ("style.apply", "style"),
        ("content.generate", "content"),
        ("rendering.render", "rendering"),
        ("media.upload", "media"),
        ("agent.run", "agent"),
        ("auth.verify", "auth"),
        ("identity.login", "identity"),
        ("web_access.fetch", "web_access"),
        ("export.pdf", "export"),
    ],
)
def test_resolve_known_domains(router: MCPRouter, tool_name: str, expected_domain: str):
    url = router.resolve(tool_name)
    assert url == DEFAULT_DOMAIN_URLS[expected_domain]


def test_resolve_with_custom_urls(custom_router: MCPRouter):
    assert custom_router.resolve("presentation.create") == "http://pres:9000/sse"
    assert custom_router.resolve("style.bold") == "http://style:9001/sse"


def test_resolve_multi_part_tool_name(router: MCPRouter):
    """Tool names with multiple dots use only the first segment as domain."""
    url = router.resolve("presentation.slide.add")
    assert url == DEFAULT_DOMAIN_URLS["presentation"]


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_resolve_missing_domain_prefix_raises(router: MCPRouter):
    with pytest.raises(ValueError, match="no domain prefix"):
        router.resolve("noprefixatall")


def test_resolve_unknown_domain_raises(router: MCPRouter):
    with pytest.raises(ValueError, match="Unknown domain"):
        router.resolve("nonexistent.tool")


def test_resolve_unknown_domain_lists_known(router: MCPRouter):
    try:
        router.resolve("bogus.action")
    except ValueError as exc:
        error_msg = str(exc)
        for domain in DEFAULT_DOMAIN_URLS:
            assert domain in error_msg


# ---------------------------------------------------------------------------
# all_urls()
# ---------------------------------------------------------------------------


def test_all_urls_returns_all(router: MCPRouter):
    urls = router.all_urls()
    assert len(urls) == len(DEFAULT_DOMAIN_URLS)
    for url in DEFAULT_DOMAIN_URLS.values():
        assert url in urls


def test_all_urls_custom_router(custom_router: MCPRouter):
    urls = custom_router.all_urls()
    assert len(urls) == 2
    assert "http://pres:9000/sse" in urls


# ---------------------------------------------------------------------------
# Domain URL map completeness
# ---------------------------------------------------------------------------


def test_default_domain_urls_covers_all_ten_domains():
    expected = {
        "presentation",
        "style",
        "content",
        "rendering",
        "media",
        "agent",
        "auth",
        "identity",
        "web_access",
        "export",
    }
    assert set(DEFAULT_DOMAIN_URLS.keys()) == expected


def test_all_default_urls_use_sse_transport():
    for domain, url in DEFAULT_DOMAIN_URLS.items():
        assert url.endswith("/sse"), f"Domain '{domain}' URL should end with /sse: {url}"


# ---------------------------------------------------------------------------
# Mutability — custom router does not affect defaults
# ---------------------------------------------------------------------------


def test_custom_router_does_not_mutate_defaults():
    original = dict(DEFAULT_DOMAIN_URLS)
    router = MCPRouter({"presentation": "http://custom:9000/sse"})
    router.domain_urls["new_domain"] = "http://new:9999/sse"
    assert original == DEFAULT_DOMAIN_URLS
