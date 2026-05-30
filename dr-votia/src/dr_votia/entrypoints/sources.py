"""Data manifest: real files in dr-contexto-data/ → ingestion metadata.

This is configuration, not logic. It maps the files that actually exist on disk
(verified 2026-05-29) to the candidato / tema / tipo / año each chunk should
carry. Edit here when sources change — the use cases never hard-code filenames.
"""

from __future__ import annotations

from pathlib import Path

from dr_votia.application.ingest_documents import SourceSpec
from dr_votia.domain.models import Candidato, Tema, Tipo


def build_sources(data_root: Path) -> list[SourceSpec]:
    plans = data_root / "planes_gobierno"
    historiales = data_root / "historiales_gestiones"
    datasets = data_root / "datasets_nacionales"

    specs: list[SourceSpec] = []

    # ── Planes de gobierno (PDF) · tipo=propuesta · año 2026 ──────────────────
    for candidato, filename in [
        (Candidato.CEPEDA, "cepeda_plan_gobierno_2026.pdf"),
        (Candidato.FAJARDO, "fajardo_plan_gobierno_2026.pdf"),
        (Candidato.LOPEZ, "lopez_plan_gobierno_2026_v2.pdf"),
        (Candidato.VALENCIA, "valencia_plan_gobierno_2026.pdf"),
        (Candidato.ESPRIELLA, "espriella_plan_gobierno_2026.pdf"),
    ]:
        specs.append(
            SourceSpec(
                path=plans / filename,
                tipo=Tipo.PROPUESTA,
                fuente=filename,
                candidato=candidato,
                año=2026,
            )
        )

    # Espriella's plan is thin; a WordPress complement adds proposal content.
    specs.append(
        SourceSpec(
            path=plans / "espriella_wordpress_complemento.txt",
            tipo=Tipo.PROPUESTA,
            fuente="espriella_wordpress_complemento.txt",
            candidato=Candidato.ESPRIELLA,
            año=2026,
        )
    )

    # ── Historiales de gestión (Markdown) · tipo=dato_historico · año 2024 ────
    for candidato, filename in [
        (Candidato.FAJARDO, "fajardo_historial_gestiones.md"),
        (Candidato.LOPEZ, "lopez_historial_gestion.md"),
        (Candidato.VALENCIA, "valencia_historial_congreso.md"),
        (Candidato.CEPEDA, "cepeda_historial_congreso.md"),
        (Candidato.ESPRIELLA, "espriella_sin_gestion_previa.md"),
    ]:
        specs.append(
            SourceSpec(
                path=historiales / filename,
                tipo=Tipo.DATO_HISTORICO,
                fuente=filename,
                candidato=candidato,
                año=2024,
            )
        )

    # ── Datasets nacionales · tipo=estadistica_nacional · candidato=nacional ──
    national: list[tuple[str, Tema, str, int]] = [
        # (filename, tema, subtema, año)
        ("dane_pobreza_nacional_2012_2024.xlsx", Tema.ECONOMIA, "pobreza_monetaria", 2024),
        ("dane_pobreza_departamental_2024.xlsx", Tema.ECONOMIA, "pobreza_departamental", 2024),
        ("dane_pobreza_boletin_2024.pdf", Tema.ECONOMIA, "pobreza_boletin", 2024),
        # Desempleo: el XLSX crudo (21 hojas × cientos de columnas, ~970K celdas) no
        # es apto para embeber celda por celda. Se ingiere el resumen curado que genera
        # scripts/extract_desempleo.py (cifras clave: promedios anuales + último dato,
        # nacional y 13 ciudades). Regenerar el .md si se actualiza el XLSX.
        ("dane_desempleo_resumen.md", Tema.ECONOMIA, "desempleo", 2026),
        ("banrep_indicadores_economicos_2026.pdf", Tema.ECONOMIA, "indicadores_macro", 2026),
        ("indepaz_balance_violencia_2025.pdf", Tema.SEGURIDAD, "balance_violencia", 2025),
        ("indepaz_lideres_2024_texto.txt", Tema.SEGURIDAD, "lideres_asesinados", 2024),
        ("transparencia_itep_texto.txt", Tema.ANTICORRUPCION, "itep", 2024),
    ]
    for filename, tema, subtema, año in national:
        specs.append(
            SourceSpec(
                path=datasets / filename,
                tipo=Tipo.ESTADISTICA_NACIONAL,
                fuente=filename,
                candidato=Candidato.NACIONAL,
                tema=tema,
                subtema=subtema,
                año=año,
            )
        )

    # ── PENDIENTE: fuentes_analisis/ (análisis comparativos de terceros) ──────
    # Comparan a varios candidatos a la vez, así que no encajan en un único
    # `candidato`. Decisión de negocio pendiente antes de ingerirlos:
    #   - condor_comparador.txt
    #   - fede_propuestas.txt
    #   - razon_publica_comparativo.txt
    # Opciones: (a) candidato=None + tipo nuevo "analisis"; (b) dividir por
    # candidato; (c) dejarlos fuera del índice de hechos.

    return specs
