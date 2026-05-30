"""Supabase pgvector adapter. Implements the VectorStore port.

Writes go through the ``documents`` table; reads go through the
``match_documents`` RPC. Requires the service_role key — RLS is enabled and the
anon role cannot insert or read.
"""

from __future__ import annotations

from typing import Any, cast

from postgrest.types import CountMethod
from supabase import Client, create_client

from dr_votia.domain.models import (
    Candidato,
    EmbeddedChunk,
    RetrievedChunk,
    Tema,
    Tipo,
)

TABLE = "documents"
RPC = "match_documents"
INSERT_BATCH = 50


class SupabaseVectorStore:
    def __init__(
        self,
        url: str,
        service_key: str,
        *,
        insert_batch: int = INSERT_BATCH,
    ) -> None:
        self._client: Client = create_client(url, service_key)
        self._insert_batch = insert_batch

    def add(self, chunks: list[EmbeddedChunk]) -> int:
        rows = [self._to_row(ec) for ec in chunks]
        for start in range(0, len(rows), self._insert_batch):
            batch = rows[start : start + self._insert_batch]
            self._client.table(TABLE).insert(batch).execute()
        return len(rows)

    def clear(self) -> None:
        # PostgREST requires a filter on delete; id is a positive bigserial.
        self._client.table(TABLE).delete().gte("id", 0).execute()

    def search(
        self,
        query_embedding: list[float],
        *,
        k: int = 5,
        candidato: Candidato | None = None,
        tema: Tema | None = None,
        tipo: Tipo | None = None,
    ) -> list[RetrievedChunk]:
        response = self._client.rpc(
            RPC,
            {
                "query_embedding": query_embedding,
                "match_count": k,
                "filter_candidato": candidato.value if candidato else None,
                "filter_tema": tema.value if tema else None,
                "filter_tipo": tipo.value if tipo else None,
            },
        ).execute()
        rows = cast("list[dict[str, Any]]", response.data or [])
        return [self._from_row(row) for row in rows]

    def count(
        self,
        *,
        candidato: Candidato | None = None,
        tema: Tema | None = None,
        tipo: Tipo | None = None,
    ) -> int:
        # count="exact" returns the total in the response regardless of the row
        # payload; limit(1) keeps that payload tiny.
        query = self._client.table(TABLE).select("id", count=CountMethod.exact).limit(1)
        if candidato is not None:
            query = query.eq("candidato", candidato.value)
        if tema is not None:
            query = query.eq("tema", tema.value)
        if tipo is not None:
            query = query.eq("tipo", tipo.value)
        response = query.execute()
        return response.count or 0

    @staticmethod
    def _to_row(ec: EmbeddedChunk) -> dict[str, Any]:
        c = ec.chunk
        return {
            "content": c.content,
            "embedding": ec.embedding,
            "candidato": c.candidato.value if c.candidato else None,
            "tema": c.tema.value if c.tema else None,
            "subtema": c.subtema,
            "tipo": c.tipo.value,
            "fuente": c.fuente,
            "pagina": c.pagina,
            "año": c.año,
            "verificable": c.verificable,
        }

    @staticmethod
    def _from_row(row: dict[str, Any]) -> RetrievedChunk:
        return RetrievedChunk(
            id=row["id"],
            content=row["content"],
            tipo=Tipo(row["tipo"]),
            fuente=row["fuente"],
            similarity=row["similarity"],
            candidato=Candidato(row["candidato"]) if row.get("candidato") else None,
            tema=Tema(row["tema"]) if row.get("tema") else None,
            subtema=row.get("subtema"),
            pagina=row.get("pagina"),
            año=row.get("año"),
        )
