"""CLI entrypoint (Typer). A driving adapter over the application use cases.

Commands:
    ingest   Read → chunk → embed → store the data manifest.
    ask      Ask a question (RAG) and print the grounded answer.

The web entrypoint (later) will be a second driving adapter calling the very
same use cases via ``build_container`` — no business logic lives here.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer

from dr_votia.application.ingest_documents import plan_ingestion
from dr_votia.domain.models import Candidato, Query, Tema, Tipo
from dr_votia.entrypoints.container import build_container, build_readers
from dr_votia.entrypoints.sources import build_sources

app = typer.Typer(help="Dr. votIA — RAG sobre datos electorales de Colombia.")

DEFAULT_DATA_ROOT = Path("../dr-contexto-data")


def _print_report(per_source: dict[str, int], total: int) -> None:
    for fuente, count in per_source.items():
        marker = "  " if count else "⚠️"
        typer.echo(f"  {marker} {count:>5}  {fuente}")
    typer.echo(f"\n  Total chunks: {total}")


@app.command()
def ingest(
    data_root: Annotated[Path, typer.Option(help="Carpeta raíz de los datos.")] = DEFAULT_DATA_ROOT,
    dry_run: Annotated[
        bool, typer.Option(help="Cuenta chunks sin embeber ni insertar (sin costo).")
    ] = False,
    reset: Annotated[
        bool, typer.Option(help="Vacía la tabla antes de insertar (re-ingesta limpia).")
    ] = False,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="No pedir confirmación.")] = False,
) -> None:
    """Ingiere el manifiesto de datos en Supabase."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    data_root = data_root.resolve()
    readers = build_readers()
    specs = build_sources(data_root)

    missing = [s.fuente for s in specs if not s.path.exists()]
    if missing:
        typer.secho("Archivos no encontrados:", fg=typer.colors.YELLOW)
        for name in missing:
            typer.echo(f"  - {name}")
        typer.echo("")
    specs = [s for s in specs if s.path.exists()]

    if dry_run:
        typer.secho("DRY RUN — sin llamadas a APIs ni inserciones.\n", fg=typer.colors.CYAN)
        report = plan_ingestion(readers, specs)
        _print_report(report.per_source, report.total_chunks)
        return

    container = build_container()
    report_preview = plan_ingestion(readers, specs)
    _print_report(report_preview.per_source, report_preview.total_chunks)
    cost = report_preview.total_chunks * 800 / 1_000_000 * 0.06
    typer.echo(f"  Costo estimado embeddings: ~${cost:.4f} USD")
    if reset:
        typer.secho("  --reset: la tabla se vaciará antes de insertar.", fg=typer.colors.YELLOW)
    typer.echo("")

    if not yes:
        typer.confirm("¿Generar embeddings e insertar en Supabase?", abort=True)

    result = container.ingest(
        specs,
        reset=reset,
        on_progress=lambda fuente, n: typer.echo(f"  · {fuente}: {n} chunks"),
    )
    typer.secho(
        f"\n✅ Ingesta completa — {result.inserted} chunks insertados.",
        fg=typer.colors.GREEN,
    )


@app.command()
def ask(
    pregunta: Annotated[str, typer.Argument(help="La pregunta a responder.")],
    k: Annotated[int, typer.Option(help="Cantidad de chunks a recuperar.")] = 5,
    candidato: Annotated[Candidato | None, typer.Option(help="Filtrar por candidato.")] = None,
    tema: Annotated[Tema | None, typer.Option(help="Filtrar por tema.")] = None,
    tipo: Annotated[Tipo | None, typer.Option(help="Filtrar por tipo.")] = None,
) -> None:
    """Responde una pregunta con RAG (retrieval + Claude)."""
    container = build_container()
    answer = container.answer(Query(text=pregunta, k=k, candidato=candidato, tema=tema, tipo=tipo))

    typer.echo(answer.text)
    typer.echo("\n— Fuentes —")
    for s in answer.sources:
        typer.echo(
            f"  [{s.candidato or '·'} · {s.tema or '·'} · {s.tipo}] "
            f"sim={s.similarity:.3f}  {s.fuente}"
        )


@app.command()
def serve(
    host: Annotated[str, typer.Option(help="Host de escucha.")] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="Puerto.")] = 8000,
    reload: Annotated[bool, typer.Option(help="Auto-reload en desarrollo.")] = False,
) -> None:
    """Levanta la API web (requiere el extra: uv sync --extra web)."""
    try:
        import uvicorn
    except ImportError as error:
        typer.secho("Falta el extra web. Instalá con: uv sync --extra web", fg=typer.colors.RED)
        raise typer.Exit(1) from error
    uvicorn.run("dr_votia.entrypoints.web.app:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
