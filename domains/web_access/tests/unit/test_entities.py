from __future__ import annotations

import dataclasses
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from domains.web_access.domain.entities import ScrapedPage, WebQuery, WebResult
from domains.web_access.domain.value_objects import ContentFormat, SearchEngine


class TestSearchEngine:
    def test_duckduckgo_value(self) -> None:
        assert SearchEngine.DUCKDUCKGO.value == "duckduckgo"

    def test_google_value(self) -> None:
        assert SearchEngine.GOOGLE.value == "google"

    def test_from_string(self) -> None:
        assert SearchEngine("google") == SearchEngine.GOOGLE


class TestContentFormat:
    def test_markdown_value(self) -> None:
        assert ContentFormat.MARKDOWN.value == "markdown"

    def test_html_value(self) -> None:
        assert ContentFormat.HTML.value == "html"

    def test_text_value(self) -> None:
        assert ContentFormat.TEXT.value == "text"


class TestWebResult:
    def test_create_web_result(self) -> None:
        result = WebResult(title="Example", url="https://example.com", snippet="A sample page.")
        assert result.title == "Example"
        assert result.url == "https://example.com"
        assert result.snippet == "A sample page."

    def test_equality_by_value(self) -> None:
        r1 = WebResult(title="A", url="https://a.com", snippet="A page")
        r2 = WebResult(title="A", url="https://a.com", snippet="A page")
        assert r1 == r2

    def test_inequality_when_different(self) -> None:
        r1 = WebResult(title="A", url="https://a.com", snippet="A page")
        r2 = WebResult(title="B", url="https://b.com", snippet="B page")
        assert r1 != r2

    def test_is_frozen(self) -> None:
        result = WebResult(title="T", url="https://t.com", snippet="T")
        with pytest.raises((AttributeError, TypeError, dataclasses.FrozenInstanceError)):
            result.title = "changed"  # type: ignore[misc]


class TestWebQuery:
    def test_create_web_query(self) -> None:
        wq = WebQuery(
            id=uuid.uuid4(),
            query="python web scraping",
            engine=SearchEngine.DUCKDUCKGO,
        )
        assert wq.query == "python web scraping"
        assert wq.engine == SearchEngine.DUCKDUCKGO
        assert wq.results == []

    def test_set_results(self) -> None:
        wq = WebQuery(id=uuid.uuid4(), query="test", engine=SearchEngine.DUCKDUCKGO)
        results = [WebResult(title="T", url="https://t.com", snippet="T snippet")]
        wq.set_results(results)
        assert len(wq.results) == 1
        assert wq.results[0].title == "T"

    def test_is_cache_valid_when_no_expiry(self) -> None:
        wq = WebQuery(id=uuid.uuid4(), query="test", engine=SearchEngine.DUCKDUCKGO)
        assert wq.is_cache_valid() is False

    def test_is_cache_valid_when_future_expiry(self) -> None:
        wq = WebQuery(
            id=uuid.uuid4(),
            query="test",
            engine=SearchEngine.DUCKDUCKGO,
            cached_until=datetime.now(UTC) + timedelta(hours=1),
        )
        assert wq.is_cache_valid() is True

    def test_is_cache_valid_when_expired(self) -> None:
        wq = WebQuery(
            id=uuid.uuid4(),
            query="test",
            engine=SearchEngine.DUCKDUCKGO,
            cached_until=datetime.now(UTC) - timedelta(seconds=1),
        )
        assert wq.is_cache_valid() is False

    def test_equality_by_id(self) -> None:
        id_ = uuid.uuid4()
        wq1 = WebQuery(id=id_, query="test", engine=SearchEngine.DUCKDUCKGO)
        wq2 = WebQuery(id=id_, query="other", engine=SearchEngine.GOOGLE)
        assert wq1 == wq2


class TestScrapedPage:
    def test_create_scraped_page(self) -> None:
        page = ScrapedPage.create(
            url="https://example.com",
            content="# Hello\n\nWorld",
            format=ContentFormat.MARKDOWN,
        )
        assert page.url == "https://example.com"
        assert page.content == "# Hello\n\nWorld"
        assert page.format == ContentFormat.MARKDOWN
        assert isinstance(page.id, uuid.UUID)

    def test_default_format_is_markdown(self) -> None:
        page = ScrapedPage.create(url="https://example.com", content="content")
        assert page.format == ContentFormat.MARKDOWN

    def test_equality_by_id(self) -> None:
        id_ = uuid.uuid4()
        p1 = ScrapedPage(id=id_, url="https://a.com", content="a", format=ContentFormat.HTML)
        p2 = ScrapedPage(id=id_, url="https://b.com", content="b", format=ContentFormat.TEXT)
        assert p1 == p2
