# Contributing

Thanks for your interest in improving `llama-index-readers-scrappey`.

## Development setup

```bash
git clone https://github.com/YOUR_USER/llama-index-readers-scrappey.git
cd llama-index-readers-scrappey

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -e ".[dev]" pytest pytest-asyncio pytest-httpx
```

## Running tests

Unit tests (no network, all mocked):

```bash
pytest tests -m "not integration"
```

Full suite including the live Scrappey call (needs a real API key):

```bash
cp .env.example .env           # then fill in SCRAPPEY_API_KEY
export $(grep -v '^#' .env | xargs)   # or use your preferred env loader
pytest tests
```

The live test scrapes `https://example.com` and costs one Scrappey request.

## Secrets hygiene

- Never commit `.env`, real API keys, or request/response dumps. `.gitignore` blocks `.env` / `.env.*` but not `.env.example`.
- If you paste a real key into an issue, comment, or commit message **by accident**, rotate it at scrappey.com immediately — commit history survives a force-push in most clones.
- CI runs unit tests only; the live integration test is skipped unless a repo secret `SCRAPPEY_API_KEY` is configured on the fork. Do not enable it on PRs from untrusted contributors.

## Code style

- Formatting: `black` (line length default).
- Linting: `ruff`.
- Typing: `mypy` (see `tool.mypy` in `pyproject.toml`).

```bash
ruff check .
mypy llama_index/
```

## Submitting changes

1. Open an issue first for non-trivial changes so we can align on scope.
2. Keep PRs focused — one behavior change per PR.
3. Add or update tests for any new behavior. The reader is small; coverage should stay ~100%.
4. Update `CHANGELOG.md` under `[Unreleased]`.
5. Bump version in `pyproject.toml` only when a release is cut, not in every PR.

## Roadmap candidates

See the "Roadmap" section in [README.md](README.md). Good first issues:

- Session reuse (`sessions.create` / `sessions.destroy`).
- `proxyCountry`, `premiumProxy`, `browser` knobs.
- `browserActions`, `customHeaders`, `cookies`, `postData` passthrough.
- POST-body scraping via `cmd: "request.post"`.
