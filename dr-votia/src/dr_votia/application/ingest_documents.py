"""Use case: read source files, chunk them, embed them, and store them.

Orchestrates domain rules (chunking, topic inference) and ports (readers,
embeddings, vector store). Knows nothing about PDFs, Voyage or Supabase
specifics — only the interfaces.

``plan_ingestion`` is a keyless companion: it reads and chunks without embedding
or storing, so the file→metadata mapping and chunk counts can be validated
before spending on the embedding API.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from dr_votia.domain.chunking import DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP, chunk_text
from dr_votia.domain.errors import UnsupportedFormatError
from dr_votia.domain.models import Candidato, Chunk, EmbeddedChunk, Tema, Tipo
from dr_votia.domain.ports import DocumentReader, EmbeddingProvider, VectorStore
from dr_votia.domain.topic_inference import infer_tema

ProgressCallback = Callable[[str, int], None]


@dataclass(frozen=True, slots=True)
class SourceSpec:
    """One file to ingest plus the metadata to stamp on its chunks.

    If ``tema`` is ``None`` the topic is inferred per chunk; if set, it overrides
    inference (used for sources whose topic is known, e.g. a poverty dataset).
    """

    path: Path
    tipo: Tipo
    fuente: str
    candidato: Candidato | None = None
    tema: Tema | None = None
    subtema: str | None = None
    año: int | None = None
    chunk_size: int = DEFAULT_CHUNK_SIZE


@dataclass(frozen=True, slots=True)
class IngestReport:
    per_source: dict[str, int] = field(default_factory=dict)
    total_chunks: int = 0
    inserted: int = 0


def _resolve_reader(readers: list[DocumentReader], path: Path) -> DocumentReader:
    for reader in readers:
        if reader.supports(path):
            return reader
    raise UnsupportedFormatError(f"No reader for {path.name}")


def extract_chunks(
    readers: list[DocumentReader],
    spec: SourceSpec,
    *,
    overlap: int = DEFAULT_OVERLAP,
) -> list[Chunk]:
    """Read a source and turn it into chunks. No embedding, no I/O to the store."""
    reader = _resolve_reader(readers, spec.path)
    chunks: list[Chunk] = []
    for fragment in reader.read(spec.path):
        for piece in chunk_text(fragment.text, chunk_size=spec.chunk_size, overlap=overlap):
            chunks.append(
                Chunk(
                    content=piece,
                    tipo=spec.tipo,
                    fuente=spec.fuente,
                    candidato=spec.candidato,
                    tema=spec.tema or infer_tema(piece),
                    subtema=spec.subtema,
                    pagina=fragment.page,
                    año=spec.año,
                )
            )
    return chunks


def plan_ingestion(
    readers: list[DocumentReader],
    specs: list[SourceSpec],
    *,
    overlap: int = DEFAULT_OVERLAP,
) -> IngestReport:
    """Dry run: count chunks per source without touching any paid API."""
    per_source: dict[str, int] = {}
    total = 0
    for spec in specs:
        count = len(extract_chunks(readers, spec, overlap=overlap))
        per_source[spec.fuente] = count
        total += count
    return IngestReport(per_source=per_source, total_chunks=total, inserted=0)


class IngestDocuments:
    def __init__(
        self,
        readers: list[DocumentReader],
        embeddings: EmbeddingProvider,
        store: VectorStore,
        *,
        chunk_overlap: int = DEFAULT_OVERLAP,
    ) -> None:
        self._readers = readers
        self._embeddings = embeddings
        self._store = store
        self._overlap = chunk_overlap

    def __call__(
        self,
        specs: list[SourceSpec],
        *,
        reset: bool = False,
        on_progress: ProgressCallback | None = None,
    ) -> IngestReport:
        if reset:
            self._store.clear()

        all_chunks: list[Chunk] = []
        per_source: dict[str, int] = {}

        for spec in specs:
            source_chunks = extract_chunks(self._readers, spec, overlap=self._overlap)
            per_source[spec.fuente] = len(source_chunks)
            all_chunks.extend(source_chunks)
            if on_progress is not None:
                on_progress(spec.fuente, len(source_chunks))

        if not all_chunks:
            return IngestReport()

        vectors = self._embeddings.embed_documents([c.content for c in all_chunks])
        embedded = [
            EmbeddedChunk(chunk=c, embedding=v) for c, v in zip(all_chunks, vectors, strict=True)
        ]
        inserted = self._store.add(embedded)

        return IngestReport(
            per_source=per_source,
            total_chunks=len(all_chunks),
            inserted=inserted,
        )
