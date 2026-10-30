"""Local storage for generated summaries."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def slugify(text: str, max_len: int = 60) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].rstrip("-") or "summary"


def save_summary(
    summary: str,
    source: str,
    output_dir: str = "summaries",
    filename: Optional[str] = None,
) -> Path:
    """Write a summary to a timestamped file under output_dir.

    Returns the path to the written file.
    """
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    if filename is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        filename = f"{stamp}-{slugify(source)}.md"
    path = directory / filename

    header = f"---\nsummary-of: {source}\ncreated-at: {datetime.now(timezone.utc).isoformat()}\n---\n\n"
    path.write_text(header + summary + "\n", encoding="utf-8")
    return path


def list_summaries(output_dir: str = "summaries") -> list[Path]:
    directory = Path(output_dir)
    if not directory.exists():
        return []
    return sorted(directory.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
