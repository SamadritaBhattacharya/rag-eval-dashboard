"""Schema for a single retrievable unit of the ingested corpus.

Every ingestion and retrieval component agrees on this one shape: the
chunker (`app.pipeline.chunk`) produces it, the embedder
(`app.pipeline.embed`) embeds its text, the vector store
(`app.pipeline.vectorstore`) persists it, and retrievers return it.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, computed_field

ContentType = Literal["prose", "code"]
"""Anthropic/MCP docs mix conceptual prose with exact-match content (code
samples, parameter names). This is the distinction hybrid retrieval exists
to serve — see ARCHITECTURE.md's hybrid-retrieval rationale."""


class Chunk(BaseModel):
    """A single retrievable unit of the ingested corpus."""

    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    section_path: str = Field(min_length=1)
    content_type: ContentType
    chunk_index: int = Field(ge=0)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def chunk_length(self) -> int:
        """Character length of `text`.

        Derived rather than caller-supplied so it can never drift out of
        sync with the actual content — there's no constructor argument to
        get wrong.
        """
        return len(self.text)
