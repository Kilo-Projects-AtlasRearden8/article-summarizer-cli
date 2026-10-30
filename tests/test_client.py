import json
import urllib.error
from unittest.mock import patch

from article_summarizer_cli.client import ChatMessage, SummarizerClient, SummarizerError


class _FakeResponse:
    def __init__(self, payload: dict, status: int = 200):
        self._payload = payload
        self.status = status

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _successful_response(summary: str) -> dict:
    return {
        "choices": [{"message": {"role": "assistant", "content": summary}}],
        "model": "llama3",
    }


def test_summarize_returns_assistant_content():
    client = SummarizerClient(endpoint="http://localhost:11434", model="llama3")
    payload = _successful_response("This is a summary.")
    with patch("article_summarizer_cli.client.urllib.request.urlopen", return_value=_FakeResponse(payload)):
        result = client.summarize("Some long article text here.")
    assert result == "This is a summary."


def test_summarize_sends_correct_payload():
    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["method"] = request.method
        captured["body"] = json.loads(request.data)
        captured["headers"] = dict(request.header_items())
        return _FakeResponse(_successful_response("ok"))

    client = SummarizerClient(endpoint="http://localhost:11434", model="mistral")
    with patch("article_summarizer_cli.client.urllib.request.urlopen", side_effect=fake_urlopen):
        client.summarize("hi", system_prompt="summarize this")

    assert captured["url"] == "http://localhost:11434/v1/chat/completions"
    assert captured["method"] == "POST"
    assert captured["body"]["model"] == "mistral"
    assert captured["body"]["stream"] is False
    assert captured["body"]["messages"][0] == {"role": "system", "content": "summarize this"}
    assert captured["body"]["messages"][1] == {"role": "user", "content": "hi"}
    ct = [v for k, v in captured["headers"].items() if k.lower() == "content-type"]
    assert ct and "application/json" in ct[0]


def test_summarize_uses_custom_messages():
    client = SummarizerClient()
    payload = _successful_response("custom flow summary")
    with patch("article_summarizer_cli.client.urllib.request.urlopen", return_value=_FakeResponse(payload)):
        result = client.summarize(
            "ignored",
            messages=[ChatMessage("user", "summarize: x")],
        )
    assert result == "custom flow summary"


def test_summarize_raises_on_connection_error():
    client = SummarizerClient(endpoint="http://localhost:9999")
    with patch(
        "article_summarizer_cli.client.urllib.request.urlopen",
        side_effect=urllib.error.URLError("connection refused"),
    ):
        try:
            client.summarize("text")
        except SummarizerError:
            return
    raise AssertionError("expected SummarizerError")


def test_summarize_raises_on_bad_response_shape():
    client = SummarizerClient()
    with patch(
        "article_summarizer_cli.client.urllib.request.urlopen",
        return_value=_FakeResponse({"not": "choices"}),
    ):
        try:
            client.summarize("text")
        except SummarizerError:
            return
    raise AssertionError("expected SummarizerError")
