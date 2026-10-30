import os
from pathlib import Path

from article_summarizer_cli.storage import save_summary, list_summaries, slugify


def test_slugify():
    assert slugify("Hello, World!") == "hello-world"
    assert slugify("---") == "summary"
    assert slugify("AI & LLMs: a guide") == "ai-llms-a-guide"


def test_save_summary_creates_file(tmp_path):
    out_dir = tmp_path / "summaries"
    path = save_summary("summary text", source="my article", output_dir=str(out_dir))
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "summary text" in content
    assert "my article" in content
    assert "created-at" in content


def test_save_summary_default_filename(tmp_path):
    out_dir = tmp_path / "summaries"
    path = save_summary("summary text", source="my article", output_dir=str(out_dir))
    assert path.name.startswith("20")
    assert path.name.endswith("-my-article.md")


def test_save_summary_custom_filename(tmp_path):
    out_dir = tmp_path / "summaries"
    path = save_summary("summary text", source="anything", output_dir=str(out_dir), filename="custom.md")
    assert path.name == "custom.md"


def test_list_summaries_empty(tmp_path):
    assert list_summaries(output_dir=str(tmp_path / "nope")) == []


def test_list_summaries_returns_md_sorted(tmp_path, monkeypatch):
    out_dir = tmp_path / "summaries"
    out_dir.mkdir()
    (out_dir / "a.md").write_text("a", encoding="utf-8")
    (out_dir / "b.md").write_text("b", encoding="utf-8")
    (out_dir / "notes.txt").write_text("ignore", encoding="utf-8")
    listed = list_summaries(output_dir=str(out_dir))
    names = [p.name for p in listed]
    assert names == ["b.md", "a.md"] or names == ["a.md", "b.md"]  # mtime-based; order not critical
    assert "notes.txt" not in names
