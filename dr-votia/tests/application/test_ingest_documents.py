"""Ingestion use case tested with a fake reader, embeddings and store."""

from __future__ import annotations

from pathlib import Path

from dr_votia.application.ingest_documents import (
    IngestDocuments,
    SourceSpec,
    plan_ingestion,
)
from dr_votia.domain.models import Candidato, EmbeddedChunk, Fragment, Tipo


class FakeReader:
    """Returns two long fragments regardless of path."""

    def supports(self, path: Path) -> bool:
        return path.suffix == ".fake"

    def read(self, path: Path) -> list[Fragment]:
        body = "contenido de prueba sobre seguridad y homicidio. " * 10
        return [Fragment(text=body, page=1), Fragment(text=body, page=2)]


class FakeEmbeddings:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [0.1, 0.2]


class FakeStore:
    def __init__(self) -> None:
        self.added: list[EmbeddedChunk] = []

    def add(self, chunks: list[EmbeddedChunk]) -> int:
        self.added.extend(chunks)
        return len(chunks)

    def search(self, *args: object, **kwargs: object) -> list:
        return []

    def clear(self) -> None:
        self.cleared = True
        self.added.clear()


def _spec() -> SourceSpec:
    return SourceSpec(
        path=Path("doc.fake"),
        tipo=Tipo.PROPUESTA,
        fuente="doc.fake",
        candidato=Candidato.FAJARDO,
        año=2026,
    )


def test_reset_clears_store_before_inserting() -> None:
    store = FakeStore()
    use_case = IngestDocuments([FakeReader()], FakeEmbeddings(), store)

    use_case([_spec()], reset=True)

    assert store.cleared is True
    assert len(store.added) > 0  # re-populated after the clear


def test_plan_counts_chunks_without_paid_calls() -> None:
    report = plan_ingestion([FakeReader()], [_spec()])

    assert report.total_chunks > 0
    assert report.inserted == 0
    assert report.per_source["doc.fake"] == report.total_chunks


def test_ingest_embeds_and_stores_every_chunk() -> None:
    store = FakeStore()
    use_case = IngestDocuments([FakeReader()], FakeEmbeddings(), store)

    report = use_case([_spec()])

    assert report.inserted == report.total_chunks
    assert len(store.added) == report.total_chunks
    # Metadata from the spec must be stamped onto stored chunks.
    assert all(ec.chunk.candidato == Candidato.FAJARDO for ec in store.added)
    assert all(len(ec.embedding) == 2 for ec in store.added)
