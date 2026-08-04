"""Tests for `app.models.chunk`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models.chunk import Chunk


def _make_chunk(**overrides: object) -> Chunk:
    defaults: dict[str, object] = {
        "id": "anthropic-docs-overview-0",
        "text": "Claude is a family of large language models developed by Anthropic.",
        "source_url": "https://docs.anthropic.com/en/docs/overview",
        "section_path": "Overview",
        "content_type": "prose",
        "chunk_index": 0,
    }
    defaults.update(overrides)
    return Chunk(**defaults)  # type: ignore[arg-type]


def test_chunk_length_is_derived_from_text() -> None:
    """Happy path: chunk_length always matches len(text), with no way to
    pass a mismatched value in."""
    chunk = _make_chunk(text="twelve chars")

    assert chunk.chunk_length == len("twelve chars")


def test_chunk_rejects_empty_text() -> None:
    """Edge case: an empty chunk is corrupt data, not a valid zero-length chunk."""
    with pytest.raises(ValidationError):
        _make_chunk(text="")


def test_chunk_rejects_negative_chunk_index() -> None:
    """Edge case: chunk_index is a position in a sequence — negative is invalid."""
    with pytest.raises(ValidationError):
        _make_chunk(chunk_index=-1)
