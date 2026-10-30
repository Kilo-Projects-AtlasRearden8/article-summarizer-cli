"""Command-line interface for the article summarizer."""

from __future__ import annotations

import argparse
import sys
from typing import Iterable, Optional

from .client import ChatMessage, SummarizerClient, SummarizerError
from .config import Config
from .disclaimer import DISCLAIMER_BORDER, format_disclaimer
from .storage import save_summary

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful assistant that summarizes articles and text clearly, "
    "accurately, and concisely. Preserve the key points and tone of the "
    "original. Do not add information that is not present in the source text."
)


def read_input(source: Optional[str], paths: Iterable[str]) -> str:
    """Read text from --file arguments, a positional source, or stdin."""
    chunks: list[str] = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as handle:
            chunks.append(handle.read())
    if source is not None:
        chunks.append(source)
    if chunks:
        return "\n\n".join(chunks)
    return sys.stdin.read()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="article-summarizer",
        description=(
            "Summarize articles and text with a local, OpenAI-compatible LLM "
            "endpoint (default Ollama). Summaries are saved locally."
        ),
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="Text to summarize (or use --file / stdin).",
    )
    parser.add_argument(
        "--file",
        action="append",
        default=[],
        metavar="PATH",
        help="Read text from a file (repeatable).",
    )
    parser.add_argument(
        "--endpoint",
        default=None,
        metavar="URL",
        help="OpenAI-compatible base URL (default: http://localhost:11434, or "
        "$ARTICLE_SUMMARIZER_ENDPOINT).",
    )
    parser.add_argument(
        "--model",
        default=None,
        metavar="NAME",
        help="Model name (default: llama3, or $ARTICLE_SUMMARIZER_MODEL).",
    )
    parser.add_argument(
        "--system",
        default=None,
        metavar="PROMPT",
        help="Custom system prompt for the summarizer.",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="PATH",
        help="Write the summary to this file instead of printing it.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        metavar="DIR",
        help="Directory for saved summaries (default: summaries, or "
        "$ARTICLE_SUMMARIZER_OUTPUT_DIR).",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not save the summary locally.",
    )
    parser.add_argument(
        "--no-disclaimer",
        action="store_true",
        help="Suppress the education-only disclaimer banner.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="article-summarizer 0.1.0",
    )
    return parser


def run(args: Optional[list[str]] = None) -> int:
    parser = build_parser()
    namespace = parser.parse_args(args)

    config = Config.from_env()
    if namespace.endpoint is not None:
        config.endpoint = namespace.endpoint
    if namespace.model is not None:
        config.model = namespace.model
    if namespace.output_dir is not None:
        config.output_dir = namespace.output_dir

    try:
        text = read_input(namespace.text, namespace.file)
    except OSError as exc:
        print(f"error: could not read input: {exc}", file=sys.stderr)
        return 1
    if not text.strip():
        print("error: no text provided (use an argument, --file, or stdin)", file=sys.stderr)
        return 1

    client = SummarizerClient(endpoint=config.endpoint, model=config.model, timeout=config.timeout)
    system_prompt = namespace.system or DEFAULT_SYSTEM_PROMPT

    try:
        summary = client.summarize(text, system_prompt=system_prompt)
    except SummarizerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        print(
            "tip: start a local Ollama server (ollama serve) or point --endpoint at a "
            "running OpenAI-compatible server.",
            file=sys.stderr,
        )
        return 1

    output_parts: list[str] = []
    if not namespace.no_disclaimer:
        output_parts.append(format_disclaimer())
    output_parts.append(summary)
    if not namespace.no_disclaimer:
        output_parts.append(format_disclaimer())
    rendered = "\n".join(output_parts)

    saved_path = None
    if not namespace.no_save:
        source = namespace.text or (namespace.file[0] if namespace.file else "stdin")
        saved_path = save_summary(summary, source=source, output_dir=config.output_dir)

    if namespace.output:
        try:
            with open(namespace.output, "w", encoding="utf-8") as handle:
                handle.write(rendered + "\n")
        except OSError as exc:
            print(f"error: could not write output file: {exc}", file=sys.stderr)
            return 1
    else:
        print(rendered)

    if saved_path is not None:
        print(f"\nsaved locally: {saved_path}", file=sys.stderr)
    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
