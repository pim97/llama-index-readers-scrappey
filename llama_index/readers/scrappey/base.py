"""Scrappey reader for LlamaIndex.

Loads web pages as Markdown via the Scrappey API (https://scrappey.com),
which bypasses anti-bot protections. HTML is fetched via Scrappey and
converted to Markdown locally with `markdownify` (Scrappey itself has no
server-side Markdown output).
"""

from typing import Any, Dict, List

import httpx
from markdownify import markdownify as _html_to_markdown

from llama_index.core.readers.base import BasePydanticReader
from llama_index.core.schema import Document

DEFAULT_API_URL = "https://publisher.scrappey.com/api/v1"


class ScrappeyReader(BasePydanticReader):
    """Reader that fetches web pages via the Scrappey API and returns Markdown.

    Scrappey is a web-scraping API that bypasses anti-bot protections
    (Cloudflare, DataDome, PerimeterX, etc.). Scrappey returns HTML;
    this reader converts it to Markdown locally via `markdownify`,
    which is the format LlamaIndex and most LLMs ingest best.

    Args:
        api_key: Your Scrappey API key. Get one at https://scrappey.com.
        api_url: Override the Scrappey API endpoint (defaults to the
            public endpoint). Useful for self-hosted or proxied setups.
        timeout: HTTP timeout in seconds for each scrape request.
        as_markdown: If True (default), convert the scraped HTML to
            Markdown. If False, the raw HTML is placed in Document.text.

    Example:
        >>> from llama_index.readers.scrappey import ScrappeyReader
        >>> reader = ScrappeyReader(api_key="YOUR_KEY")
        >>> docs = reader.load_data(["https://example.com"])
        >>> print(docs[0].text[:80])
    """

    is_remote: bool = True
    api_key: str
    api_url: str = DEFAULT_API_URL
    timeout: float = 120.0
    as_markdown: bool = True

    @classmethod
    def class_name(cls) -> str:
        return "ScrappeyReader"

    def load_data(self, urls: List[str]) -> List[Document]:
        """Scrape each URL synchronously and return a list of Documents."""
        if not urls:
            return []
        with httpx.Client(timeout=self.timeout) as client:
            return [self._scrape(client, url) for url in urls]

    async def aload_data(self, urls: List[str]) -> List[Document]:
        """Scrape each URL asynchronously and return a list of Documents."""
        if not urls:
            return []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return [await self._ascrape(client, url) for url in urls]

    # --- internals ---

    def _payload(self, url: str) -> Dict[str, Any]:
        # `filter: ["response"]` trims Scrappey's reply to just the HTML
        # body field we use for conversion, cutting bandwidth.
        return {"cmd": "request.get", "url": url}

    def _endpoint(self) -> str:
        # Scrappey authenticates via the `key` query parameter.
        return f"{self.api_url}?key={self.api_key}"

    def _to_document(self, url: str, body: Dict[str, Any]) -> Document:
        solution: Dict[str, Any] = body.get("solution") or {}
        html: str = solution.get("response", "") or ""
        text: str = _html_to_markdown(html) if self.as_markdown and html else html

        metadata: Dict[str, Any] = {
            "source": "scrappey",
            "url": url,
            "current_url": solution.get("currentUrl"),
            "verified": solution.get("verified"),
            "detected_antibot_providers": solution.get("detectedAntibotProviders"),
            "session_id": body.get("session"),
            "time_elapsed_ms": body.get("timeElapsed"),
        }
        return Document(text=text, id_=url, metadata=metadata)

    def _scrape(self, client: httpx.Client, url: str) -> Document:
        response = client.post(self._endpoint(), json=self._payload(url))
        response.raise_for_status()
        return self._to_document(url, response.json())

    async def _ascrape(self, client: httpx.AsyncClient, url: str) -> Document:
        response = await client.post(self._endpoint(), json=self._payload(url))
        response.raise_for_status()
        return self._to_document(url, response.json())
