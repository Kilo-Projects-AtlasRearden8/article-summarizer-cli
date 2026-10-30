"""HTTP client for OpenAI-compatible chat/completions endpoints."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Iterable


@dataclass
class ChatMessage:
    role: str
    content: str


class SummarizerError(Exception):
    """Raised when the summarizer endpoint cannot be reached or fails."""


class SummarizerClient:
    """Thin client over an OpenAI-compatible /v1/chat/completions endpoint.

    Default target is a local Ollama instance (http://localhost:11434), which
    exposes an OpenAI-compatible chat API. No API keys are ever required or
    sent.
    """

    def __init__(
        self,
        endpoint: str = "http://localhost:11434",
        model: str = "llama3",
        timeout: int = 60,
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _chat_url(self) -> str:
        return f"{self.endpoint}/v1/chat/completions"

    def summarize(
        self,
        text: str,
        system_prompt: str | None = None,
        messages: Iterable[ChatMessage] | None = None,
    ) -> str:
        """Send text to the endpoint and return the assistant's reply."""
        if messages is None:
            built: list[ChatMessage] = []
            if system_prompt:
                built.append(ChatMessage("system", system_prompt))
            built.append(ChatMessage("user", text))
        else:
            built = list(messages)

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in built],
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self._chat_url(),
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read()
        except urllib.error.URLError as exc:
            raise SummarizerError(
                f"Could not reach summarizer endpoint {self.endpoint}: {exc}"
            ) from exc
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise SummarizerError(f"Invalid JSON response from endpoint: {exc}") from exc

        try:
            parsed = json.loads(body)
            return parsed["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise SummarizerError(f"Unexpected response shape from endpoint: {exc}") from exc
