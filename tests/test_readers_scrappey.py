"""Unit tests for ScrappeyReader."""

import json
import os
from typing import Any, Dict, Optional

import httpx
import pytest
from pytest_httpx import HTTPXMock

from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document
from llama_index.readers.scrappey import ScrappeyReader
from llama_index.readers.scrappey.base import DEFAULT_API_URL

API_KEY = "test-key"


def _canned_response(
    markdown: Optional[str] = "# Hello\n\nWorld",
    html: str = "<h1>Hello</h1><p>World</p>",
    verified: bool = True,
    current_url: str = "https://example.com/",
    session: str = "abc-123",
) -> Dict[str, Any]:
    """Shape mirrors a real Scrappey response when `markdown: true` is sent."""
    solution: Dict[str, Any] = {
        "verified": verified,
        "currentUrl": current_url,
        "userAgent": "Mozilla/5.0",
        "innerText": "Hello\n\nWorld",
        "response": html,
        "detectedAntibotProviders": {"primaryProvider": "none"},
        "cookies": [],
        "cookieString": "",
        "type": "browser",
    }
    if markdown is not None:
        solution["markdown"] = markdown
    return {
        "solution": solution,
        "timeElapsed": 1234,
        "data": "success",
        "session": session,
    }


def test_class_inheritance() -> None:
    """ScrappeyReader must inherit from BaseReader (via BasePydanticReader)."""
    base_names = [b.__name__ for b in ScrappeyReader.__mro__]
    assert BaseReader.__name__ in base_names
    assert ScrappeyReader.class_name() == "ScrappeyReader"


def test_load_data_single_url_uses_server_markdown(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{DEFAULT_API_URL}?key={API_KEY}",
        json=_canned_response(markdown="# Example Domain\n\nSome text."),
    )

    reader = ScrappeyReader(api_key=API_KEY)
    docs = reader.load_data(["https://example.com"])

    assert len(docs) == 1
    doc = docs[0]
    assert isinstance(doc, Document)
    # Should use server-side Markdown verbatim — no local conversion artifacts.
    assert doc.text == "# Example Domain\n\nSome text."
    assert doc.id_ == "https://example.com"
    assert doc.metadata["source"] == "scrappey"
    assert doc.metadata["url"] == "https://example.com"
    assert doc.metadata["current_url"] == "https://example.com/"
    assert doc.metadata["verified"] is True
    assert doc.metadata["session_id"] == "abc-123"
    assert doc.metadata["time_elapsed_ms"] == 1234


def test_falls_back_to_local_markdownify_when_markdown_missing(
    httpx_mock: HTTPXMock,
) -> None:
    """If Scrappey's response lacks `solution.markdown`, convert HTML locally."""
    httpx_mock.add_response(
        method="POST",
        url=f"{DEFAULT_API_URL}?key={API_KEY}",
        json=_canned_response(markdown=None, html="<h1>Hello</h1>"),
    )

    reader = ScrappeyReader(api_key=API_KEY)
    docs = reader.load_data(["https://example.com"])

    assert "Hello" in docs[0].text
    assert "<h1>" not in docs[0].text  # locally converted


def test_load_data_multiple_urls_preserves_order(httpx_mock: HTTPXMock) -> None:
    urls = [
        "https://example.com/a",
        "https://example.com/b",
        "https://example.com/c",
    ]
    for url in urls:
        httpx_mock.add_response(
            method="POST",
            url=f"{DEFAULT_API_URL}?key={API_KEY}",
            json=_canned_response(markdown=f"# {url}"),
        )

    reader = ScrappeyReader(api_key=API_KEY)
    docs = reader.load_data(urls)

    assert [d.id_ for d in docs] == urls
    assert [d.text for d in docs] == [f"# {u}" for u in urls]


def test_payload_shape_sets_markdown_boolean(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{DEFAULT_API_URL}?key={API_KEY}",
        json=_canned_response(),
    )

    reader = ScrappeyReader(api_key=API_KEY)
    reader.load_data(["https://example.com/path"])

    request = httpx_mock.get_request()
    assert request is not None
    assert request.method == "POST"
    assert f"key={API_KEY}" in str(request.url)

    body = json.loads(request.content)
    assert body == {
        "cmd": "request.get",
        "url": "https://example.com/path",
        "markdown": True,  # BOOLEAN — Scrappey ignores the string "true"
    }


def test_payload_omits_markdown_when_disabled(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{DEFAULT_API_URL}?key={API_KEY}",
        json=_canned_response(markdown=None),
    )

    reader = ScrappeyReader(api_key=API_KEY, as_markdown=False)
    reader.load_data(["https://example.com"])

    body = json.loads(httpx_mock.get_request().content)
    assert "markdown" not in body


def test_raises_on_http_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{DEFAULT_API_URL}?key={API_KEY}",
        status_code=500,
        json={"error": "boom"},
    )

    reader = ScrappeyReader(api_key=API_KEY)
    with pytest.raises(httpx.HTTPStatusError):
        reader.load_data(["https://example.com"])


def test_load_data_empty_list_returns_empty() -> None:
    reader = ScrappeyReader(api_key=API_KEY)
    assert reader.load_data([]) == []


def test_custom_api_url(httpx_mock: HTTPXMock) -> None:
    custom_url = "https://proxy.internal/v1"
    httpx_mock.add_response(
        method="POST",
        url=f"{custom_url}?key={API_KEY}",
        json=_canned_response(),
    )

    reader = ScrappeyReader(api_key=API_KEY, api_url=custom_url)
    reader.load_data(["https://example.com"])

    request = httpx_mock.get_request()
    assert request is not None
    assert str(request.url).startswith(custom_url)


def test_raw_html_mode(httpx_mock: HTTPXMock) -> None:
    """With as_markdown=False, Document.text is the raw HTML from `response`."""
    html = "<h1>Raw</h1>"
    httpx_mock.add_response(
        method="POST",
        url=f"{DEFAULT_API_URL}?key={API_KEY}",
        json=_canned_response(markdown=None, html=html),
    )

    reader = ScrappeyReader(api_key=API_KEY, as_markdown=False)
    docs = reader.load_data(["https://example.com"])

    assert docs[0].text == html


async def test_aload_data(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{DEFAULT_API_URL}?key={API_KEY}",
        json=_canned_response(markdown="# Async"),
    )

    reader = ScrappeyReader(api_key=API_KEY)
    docs = await reader.aload_data(["https://example.com"])

    assert len(docs) == 1
    assert docs[0].text == "# Async"
    assert docs[0].metadata["url"] == "https://example.com"


# --- Opt-in live integration test ---


@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("SCRAPPEY_API_KEY"),
    reason="SCRAPPEY_API_KEY not set",
)
def test_live_scrape_example_com() -> None:
    reader = ScrappeyReader(api_key=os.environ["SCRAPPEY_API_KEY"])
    docs = reader.load_data(["https://example.com"])
    assert len(docs) == 1
    doc = docs[0]
    assert doc.text
    assert "Example Domain" in doc.text
    assert doc.metadata["verified"] is True
    assert doc.metadata["session_id"]
