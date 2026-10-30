import io
import sys

from article_summarizer_cli.cli import run
from article_summarizer_cli.config import Config
from article_summarizer_cli.client import SummarizerError


def _install_fake_client(monkeypatch, summary_text="Summarized result."):
    import article_summarizer_cli.cli as cli_mod

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        def summarize(self, text, system_prompt=None, messages=None):
            return summary_text

    monkeypatch.setattr(cli_mod, "SummarizerClient", FakeClient)


def test_run_prints_summary(tmp_path, monkeypatch, capsys):
    _install_fake_client(monkeypatch)
    monkeypatch.setattr(
        Config,
        "from_env",
        classmethod(
            lambda cls: Config(
                endpoint="http://localhost:11434",
                model="llama3",
                output_dir=str(tmp_path / "summaries"),
                timeout=60,
            )
        ),
    )
    code = run(["--no-disclaimer", "--no-save", "the quick brown fox"])
    assert code == 0
    captured = capsys.readouterr()
    assert "Summarized result." in captured.out


def test_run_writes_output_file(tmp_path, monkeypatch):
    _install_fake_client(monkeypatch, summary_text="file summary.")
    monkeypatch.setattr(
        Config,
        "from_env",
        classmethod(
            lambda cls: Config(
                endpoint="http://localhost:11434",
                model="llama3",
                output_dir=str(tmp_path / "summaries"),
                timeout=60,
            )
        ),
    )
    out_file = tmp_path / "out.txt"
    code = run(["--no-disclaimer", "--no-save", "--output", str(out_file), "some text"])
    assert code == 0
    assert out_file.read_text(encoding="utf-8").strip().endswith("file summary.")


def test_run_rejects_empty_input(monkeypatch, capsys):
    _install_fake_client(monkeypatch)
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    code = run(["--no-disclaimer", "--no-save"])
    assert code != 0
    captured = capsys.readouterr()
    assert "no text provided" in captured.err


def test_run_endpoint_error_returns_nonzero(tmp_path, monkeypatch, capsys):
    import article_summarizer_cli.cli as cli_mod

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        def summarize(self, text, system_prompt=None, messages=None):
            raise SummarizerError("connection refused")

    monkeypatch.setattr(cli_mod, "SummarizerClient", FakeClient)
    monkeypatch.setattr(
        Config,
        "from_env",
        classmethod(
            lambda cls: Config(
                endpoint="http://localhost:11434",
                model="llama3",
                output_dir=str(tmp_path / "summaries"),
                timeout=60,
            )
        ),
    )
    code = run(["--no-disclaimer", "--no-save", "text"])
    assert code == 1
    captured = capsys.readouterr()
    assert "connection refused" in captured.err


def test_run_saves_locally(tmp_path, monkeypatch, capsys):
    _install_fake_client(monkeypatch)
    monkeypatch.setattr(
        Config,
        "from_env",
        classmethod(
            lambda cls: Config(
                endpoint="http://localhost:11434",
                model="llama3",
                output_dir=str(tmp_path / "summaries"),
                timeout=60,
            )
        ),
    )
    code = run(["--no-disclaimer", "saved article text"])
    assert code == 0
    saved = list((tmp_path / "summaries").glob("*.md"))
    assert len(saved) == 1
    content = saved[0].read_text(encoding="utf-8")
    assert "Summarized result." in content
    captured = capsys.readouterr()
    assert f"saved locally: {saved[0]}" in captured.err
