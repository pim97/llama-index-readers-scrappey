# Changelog

All notable changes to this project are documented here. This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.0] — Initial release

### Added
- `ScrappeyReader`: LlamaIndex `BasePydanticReader` that loads web pages via the [Scrappey](https://scrappey.com) API.
- `load_data(urls: List[str]) -> List[Document]` sync method.
- `aload_data(urls: List[str]) -> List[Document]` async method (via `httpx.AsyncClient`).
- `as_markdown` option (default `True`) — converts the scraped HTML to Markdown locally with [`markdownify`](https://pypi.org/project/markdownify/). Set `False` for raw HTML.
- Document metadata: `source`, `url`, `current_url`, `verified`, `detected_antibot_providers`, `session_id`, `time_elapsed_ms`.
- Unit-test suite (9 tests) using `pytest-httpx` mocks plus one opt-in live integration test gated on `SCRAPPEY_API_KEY`.

### Notes
- Scrappey's `publisher.scrappey.com/api/v1` endpoint returns HTML in `solution.response`. Scrappey has no server-side Markdown output mode — Markdown conversion is performed locally by this reader.
