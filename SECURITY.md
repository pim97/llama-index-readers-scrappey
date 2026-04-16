# Security Policy

## Reporting a vulnerability

If you discover a security issue in `llama-index-readers-scrappey`, please **do not open a public GitHub issue**. Instead, report it privately via GitHub's [private security advisory](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability) feature on this repository.

Include:
- A description of the issue and its impact.
- Steps to reproduce (a minimal proof-of-concept is ideal).
- Affected version(s).

You should receive an acknowledgement within a reasonable timeframe. Coordinated disclosure is appreciated — please give the maintainer a chance to ship a fix before publishing details.

## What is in scope

- Code execution, credential exfiltration, or SSRF in the reader itself.
- Incorrect handling of Scrappey responses that could lead to indexing attacker-controlled content as trusted metadata.
- Dependency supply-chain issues that affect this package specifically.

## What is out of scope

- Vulnerabilities in the upstream Scrappey service — report those to Scrappey directly.
- Vulnerabilities in `llama-index-core`, `httpx`, or `markdownify` — report to their respective projects.
- Prompt-injection content embedded in scraped pages. This reader intentionally returns whatever Scrappey fetched; downstream LLM ingestion is responsible for prompt-injection defenses.

## Secret handling

- API keys are accepted only via the `api_key` constructor argument — they are never logged, never written to disk, and never included in exception messages.
- Test fixtures use the literal string `"test-key"`; no real credentials are shipped in the repository.
- `.gitignore` blocks `.env`, `.env.*` (with an explicit allow for `.env.example`), `*.pem`, and `*.key` to make accidental commits harder.
