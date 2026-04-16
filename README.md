# LlamaIndex Readers Integration: Scrappey

Use [Scrappey](https://scrappey.com) to load web pages into LlamaIndex as clean Markdown, bypassing anti-bot protections (Cloudflare, DataDome, PerimeterX, etc.).

Scrappey fetches the page through its anti-bot proxy; this reader then converts the returned HTML to Markdown locally with [`markdownify`](https://pypi.org/project/markdownify/), producing LLM-ready text.

## Installation

```bash
pip install llama-index-readers-scrappey
```

## Setup

1. Sign up at [scrappey.com](https://scrappey.com) and grab your API key.
2. Pass it to the reader (or set `SCRAPPEY_API_KEY` and read from env):

## Quickstart

```python
import os
from llama_index.core import VectorStoreIndex
from llama_index.readers.scrappey import ScrappeyReader

reader = ScrappeyReader(api_key=os.environ["SCRAPPEY_API_KEY"])

documents = reader.load_data(
    [
        "https://example.com",
        "https://en.wikipedia.org/wiki/Web_scraping",
    ]
)

index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
print(query_engine.query("Summarize web scraping."))
```

### Async

```python
import asyncio

async def main():
    reader = ScrappeyReader(api_key="...")
    docs = await reader.aload_data(["https://example.com"])
    print(docs[0].text[:200])

asyncio.run(main())
```

### Raw HTML instead of Markdown

```python
reader = ScrappeyReader(api_key="...", as_markdown=False)
docs = reader.load_data(["https://example.com"])
# docs[0].text is the raw HTML returned by Scrappey
```

## Document schema

Each URL produces one `Document`:

| Field                                 | Type           | Value                                         |
| ------------------------------------- | -------------- | --------------------------------------------- |
| `text`                                | `str`          | Markdown body (or raw HTML if `as_markdown=False`) |
| `id_`                                 | `str`          | The source URL (stable ID for ingestion)      |
| `metadata["source"]`                  | `str`          | Always `"scrappey"`                           |
| `metadata["url"]`                     | `str`          | The URL you asked for                         |
| `metadata["current_url"]`             | `str`          | Final URL after redirects                     |
| `metadata["verified"]`                | `bool`         | Scrappey's anti-bot verification flag         |
| `metadata["detected_antibot_providers"]` | `dict`      | e.g. `{"primaryProvider": "cloudflare"}`      |
| `metadata["session_id"]`              | `str`          | Scrappey session ID (reusable for crawls)     |
| `metadata["time_elapsed_ms"]`         | `int`          | How long Scrappey took to fetch the page      |

## Constructor options

| Arg           | Default                                   | Purpose                                       |
| ------------- | ----------------------------------------- | --------------------------------------------- |
| `api_key`     | _required_                                | Scrappey API key                              |
| `api_url`     | `https://publisher.scrappey.com/api/v1`   | Override for self-hosted / proxied endpoints  |
| `timeout`     | `120.0`                                   | Per-request HTTP timeout in seconds           |
| `as_markdown` | `True`                                    | Convert scraped HTML to Markdown locally      |

## Roadmap

v0.1 is intentionally minimal (URLs → Markdown Documents). Planned for later releases:

- Session reuse (`sessions.create` / `sessions.destroy`) for cheaper crawls and consistent fingerprinting
- `proxyCountry`, `premiumProxy`, `browser` configuration
- `browserActions`, `customHeaders`, `cookies`, `postData` passthrough for JS-heavy and auth-gated pages
- POST-body scraping via `cmd: "request.post"`

## Links

- [Scrappey homepage](https://scrappey.com)
- [Scrappey wiki](https://wiki.scrappey.com)
