"""Configuration for the summarizer CLI.

All settings can be overridden with environment variables:
    ARTICLE_SUMMARIZER_ENDPOINT   OpenAI-compatible base URL (default Ollama)
    ARTICLE_SUMMARIZER_MODEL      Model name to request
    ARTICLE_SUMMARIZER_OUTPUT_DIR Directory for saved summaries
    ARTICLE_SUMMARIZER_TIMEOUT    HTTP request timeout in seconds
"""

from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_ENDPOINT = "http://localhost:11434"
DEFAULT_MODEL = "llama3"
DEFAULT_OUTPUT_DIR = "summaries"
DEFAULT_TIMEOUT = 60


@dataclass
class Config:
    endpoint: str
    model: str
    output_dir: str
    timeout: int

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            endpoint=os.environ.get("ARTICLE_SUMMARIZER_ENDPOINT", DEFAULT_ENDPOINT),
            model=os.environ.get("ARTICLE_SUMMARIZER_MODEL", DEFAULT_MODEL),
            output_dir=os.environ.get("ARTICLE_SUMMARIZER_OUTPUT_DIR", DEFAULT_OUTPUT_DIR),
            timeout=int(os.environ.get("ARTICLE_SUMMARIZER_TIMEOUT", str(DEFAULT_TIMEOUT))),
        )
