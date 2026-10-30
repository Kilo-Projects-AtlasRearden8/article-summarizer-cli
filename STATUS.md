# STATUS

## What was built

`article-summarizer` — a local-first Python CLI that summarizes articles and
text through a configurable OpenAI-compatible endpoint (default: Ollama at
`http://localhost:11434`).

Project contents:

- `pyproject.toml` — packaging, `article-summarizer` console script, pytest config
- `article_summarizer_cli/` — package:
  - `client.py` — `SummarizerClient` POSTs to `/v1/chat/completions`, parses the
    assistant reply, converts transport failures into `SummarizerError`
  - `config.py` — `Config` with defaults overridable via `ARTICLE_SUMMARIZER_*`
    environment variables
  - `storage.py` — timestamped Markdown summaries saved to a local directory
    (`summaries/` by default), plus `list_summaries`
  - `disclaimer.py` — education-only disclaimer banner printed with every run
  - `cli.py` — argparse CLI: text argument, `--file` (repeatable), stdin,
    `--endpoint`, `--model`, `--system`, `--output`, `--no-save`,
    `--no-disclaimer`, `--version`
- `tests/` — 16 tests, all mocked at `urllib.request.urlopen`; no network, no
  API keys
- `LICENSE` — MIT, `Copyright (c) 2026 Asdale Dynamics, LLC`
- `README.md` — usage, local-first disclaimers, credits Asdale Dynamics, LLC
- `.gitignore` — Python/venv/build artifacts
- `STATUS.md` — this file

## How to run

```bash
# create & activate a virtualenv (recommended)
python3 -m venv .venv
.venv/bin/pip install -e .

# summarize text directly (needs a running endpoint; Ollama default)
.venv/bin/article-summarizer --no-save "Paste article text here."

# summarize a file with defaults
.venv/bin/article-summarizer --file article.txt

# read from stdin
cat article.txt | .venv/bin/article-summarizer

# different endpoint / model (any OpenAI-compatible server)
.venv/bin/article-summarizer --endpoint http://localhost:1234/v1 --model qwen2.5 --file article.txt

# write to a file, suppress disclaimer banner
.venv/bin/article-summarizer --no-disclaimer --output summary.md --file article.txt

# configure defaults via environment
export ARTICLE_SUMMARIZER_ENDPOINT=http://localhost:11434
export ARTICLE_SUMMARIZER_MODEL=llama3
export ARTICLE_SUMMARIZER_OUTPUT_DIR=summaries

# run tests (fully mocked, offline)
.venv/bin/python -m pytest
```

Summaries are saved to `summaries/<utc-timestamp>-<slug>.md` unless
`--no-save` is passed. Every run prints an education-only disclaimer unless
`--no-disclaimer` is passed.

Ollama setup: `ollama pull llama3` then `ollama serve`, then run the CLI.

## Verification results

- `python3 -m pip install -e .` — builds and installs the wheel successfully
- `.venv/bin/python -m pytest` — **16 passed**
  - 5 client tests (payload shape, custom messages, connection error, bad
    response shape) — all mocked, no network
  - 4 storage tests (slugify, save, custom filename, listing)
  - 7 CLI tests (print, output file, empty input rejection, endpoint error,
    local save) — client faked, no network
- `.venv/bin/article-summarizer --no-disclaimer --no-save "..."` — runs and
  reports a clear, actionable error when no endpoint is reachable
- No `.github/workflows` added; no secrets, API keys, or personal data in any
  file; nothing pushed or published

## Known gaps

- Requires a running OpenAI-compatible endpoint (Ollama by default); the CLI
  itself has no offline/mock mode (mocking exists only in tests).
- No streaming responses; waits for the full completion.
- Single-shot summarization only; no conversation history or multi-turn chat.
- Saved summaries are plain Markdown files with no index, search, or pruning.
- Assumes the target endpoint exposes OpenAI-compatible
  `/v1/chat/completions` (Ollama does in current releases).
