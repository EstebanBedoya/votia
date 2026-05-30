# Reporte de recolección de datos — Dr. Contexto

**Fecha de ejecución:** 2026-05-29
**Fuente de instrucciones:** `datos.md`
**Carpeta de salida:** `dr-contexto-data/`
**Método:** descargas directas (`curl`), scraping HTML→texto con script propio (`scripts/html2text.py`, solo stdlib de Python) y extracción factual asistida para historiales.

---

## 1. Resumen ejecutivo

| Bloque | Estado | Detalle |
|---|---|---|
| **1 — Planes de gobierno** | ✅ **Completo (5/5)** | Los 5 candidatos con PDF; Valencia además en texto plano |
| **2 — Datasets nacionales** | ✅ **Núcleo completo** | DANE (pobreza + desempleo), Indepaz (balance + líderes), Banrep. Faltan colas menores (ver §4) |
| **3 — Historiales de gestión** | ✅ **5/5 construidos** | Datos verificados + vacíos marcados explícitamente para extracción manual |
| **4 — Fuentes de análisis** | ⚠️ **Parcial** | Razón Pública completo; FEDe/CONDOR son SPAs JS (texto mínimo); Alfil con rate-limit (429) |

**Hallazgo operativo:** todos los links del `datos.md` están vivos al 2026-05-29, salvo dos correcciones: el v1 de López y el link de deuda de Banrep (ver §3 y §4).

---

## 2. Inventario de archivos

### `planes_gobierno/` — Bloque 1 ✅
| Archivo | Origen | Notas |
|---|---|---|
| `cepeda_plan_gobierno_2026.pdf` | PDF directo (movimientopactohistorico.co) | 20 MB · ~720k chars de texto seleccionable |
| `fajardo_plan_gobierno_2026.pdf` | PDF directo (La Silla Vacía) | 62 págs · texto seleccionable |
| `lopez_plan_gobierno_2026_v2.pdf` | PDF directo (claudia-lopez.com) | 37 págs · "Una Nueva Historia" (versión más completa) |
| `valencia_plan_gobierno_2026.pdf` | PDF oficial hallado en el sitio ("111 puntos plan de gobierno.pdf") | 8 págs |
| `valencia_plan_gobierno_2026.txt` | Scraping de la página web | 111 puntos completos en texto |
| `espriella_plan_gobierno_2026.pdf` | PDF oficial (wordpress) | Documento deliberadamente breve |
| `espriella_wordpress_complemento.txt` | Scraping del artículo | Complemento |

### `datasets_nacionales/` — Bloque 2 ✅ núcleo
| Archivo | Fuente | Contenido |
|---|---|---|
| `dane_pobreza_boletin_2024.pdf` | DANE | Boletín pobreza monetaria 2024 (26 págs, metodología + cifras) |
| `dane_pobreza_nacional_2012_2024.xlsx` | DANE (anexo oficial) | Serie histórica nacional de pobreza |
| `dane_pobreza_departamental_2024.xlsx` | DANE (anexo oficial) | Pobreza por departamento 2024 |
| `dane_desempleo_geih_abr2026.xlsx` | DANE (anexo GEIH) | Mercado laboral, dato más reciente: **abril 2026** |
| `indepaz_balance_violencia_2025.pdf` | Indepaz | Balance completo de violencias 2025 (informe consolidado) |
| `indepaz_lideres_2024_texto.txt` | Indepaz (scraping) | **Lista nominal** de líderes asesinados 2024/2025/2026 |
| `banrep_indicadores_economicos_2026.pdf` | Banrep (BIE) | Incluye "Deuda bruta del SPNF y GNC (% del PIB)" + PIB + situación fiscal |
| `transparencia_itep_texto.txt` | Transparencia x Colombia (scraping) | Texto de la página del índice |

### `historiales_gestiones/` — Bloque 3 ✅
| Archivo | Cargos verificables | Dato clave |
|---|---|---|
| `fajardo_historial_gestiones.md` | 2 (Alcalde Medellín + Gobernador Antioquia) | Homicidios Antioquia 50,1→31,1 x100k (-38%) |
| `lopez_historial_gestion.md` | 1 (Alcaldesa Bogotá) + Senadora | Seguridad **negativa**: homicidios +3%, hurtos +12,3% |
| `cepeda_historial_congreso.md` | 0 ejecutivos (legislativo desde 2010) | DDHH, paz, caso Uribe |
| `valencia_historial_congreso.md` | 0 ejecutivos (Senadora desde 2014) | Salto electoral: 63k (2022) → 3,2M en consulta 2026 |
| `espriella_sin_gestion_previa.md` | **0 (dato analizable)** | Sin cargo público previo; 62% de firmas inválidas |

### `fuentes_analisis/` — Bloque 4 ⚠️
| Archivo | Estado |
|---|---|
| `razon_publica_comparativo.txt` | ✅ Análisis comparativo completo (~137k chars) |
| `fede_propuestas.txt` | ⚠️ SPA JS — solo texto estático mínimo |
| `condor_comparador.txt` | ⚠️ SPA JS — solo texto estático mínimo |

### `scripts/`
| Archivo | Uso |
|---|---|
| `html2text.py` | Extractor HTML→texto (stdlib). Uso: `python3 html2text.py in.html out.txt` |

> Nota: en cada subcarpeta se conservó un `_raw_html/` con el HTML crudo de cada página scrapeada, por trazabilidad y para re-extracción si se mejora el parser.

---

## 3. Correcciones aplicadas vs. `datos.md`

1. **López v1 (portada verde, feb 2026):** el link `claudia-lopez.com/.../2026/02/Programa-de-Gobierno-Claudia-Lopez.pdf` devuelve **HTML, no PDF** (caído). Se descartó. El v2 "Una Nueva Historia" es la versión completa y quedó descargado.
2. **Banrep deuda:** el link `banrep.gov.co/es/estadisticas/deuda-sector-publico` da **404**. La URL vigente es `/es/estadisticas/deuda-publica`, pero es una app JS sin archivo descargable directo. Sustituido por el **Boletín de Indicadores Económicos (BIE)**, que contiene la serie de deuda pública % PIB.
3. **Valencia / Espriella:** no requerían "imprimir como PDF" manual — se localizaron los **PDF oficiales reales** dentro del HTML y se descargaron directo.

---

## 4. Pendientes y limitaciones honestas

### Rate-limiting (HTTP 429) el 2026-05-29 — reintentar
- **Alfil** (`alfil.co/2026/...`): citas textuales por candidato. Bloqueado. Reintentar para complementar Espriella y Valencia.
- **La Silla Vacía** perfil de Paloma Valencia: bloqueado. Afecta el detalle legislativo de su historial.

### Sitios JS (SPA) — el scraping estático no alcanza
- **FEDe** (`propuestascandidatos.fedecolombia.org`) y **CONDOR** (`condorlatam.com/co/planes`): renderizan con JavaScript; el HTML estático trae poco. Para extraerlos haría falta un navegador headless (Playwright/Selenium) — no instalado en este entorno.
- **Banrep / DANE series interactivas:** las series navegables requieren exportación manual desde sus visores. Se obtuvo el dato vía anexos .xlsx (DANE) y el BIE (Banrep).

### Datos de Bloque 3 marcados como "pendiente de verificación manual"
Los historiales contienen **solo cifras verificadas en las fuentes** (no se inventó ningún número). Quedan marcados explícitamente como pendientes:
- **Fajardo:** tasa de homicidios Medellín 2003-2007; % presupuesto en educación (ambos cargos); proyectos CTI Antioquia. → Observatorio Seguridad Medellín + informes de gestión.
- **López:** homicidios Bogotá x100k 2019-2023; deuda distrital en billones; % avance Metro; calificación Bogotá Cómo Vamos. → SCJ, Hacienda Distrital, Bogotá Cómo Vamos.
- **Valencia y Cepeda:** registro de votaciones y proyectos radicados/aprobados. → Congreso Visible (perfiles enlazados en cada archivo).

### Colas menores de Bloque 2 no descargadas
- DANE PIB / cuentas nacionales (serie aparte), MinSalud (afiliación SGSSS) y MinEducación (SNIES): son hubs web; no se priorizaron por estar marcados como prioridad baja en `datos.md`. El BIE de Banrep ya cubre el PIB reciente (+2,2% Q1 2026 según `datos.md`).

---

## 5. Próximos pasos recomendados (en orden de valor)

1. **Reintentar Alfil + La Silla Vacía** (esperar a que pase el 429) para cerrar el detalle de Valencia y Espriella.
2. **Instalar un headless browser** si se quiere capturar FEDe y CONDOR (las dos fuentes comparativas más estructuradas).
3. **Cerrar los vacíos de Bloque 3** entrando a Congreso Visible (Valencia/Cepeda) y a los observatorios distritales (López) e informes de gestión municipales (Fajardo).
4. **Parsear los .xlsx de DANE** a CSV/tablas limpias para alimentar el modelo (hoy están en formato anexo oficial con varias hojas).

---

## 6. Datos clave ya disponibles para el agente

- **Pobreza monetaria nacional 2024:** 31,8% (boletín DANE descargado).
- **Desempleo:** serie hasta abril 2026 (GEIH).
- **Conflicto:** balance Indepaz 2025 + lista nominal de líderes asesinados 2024-2026.
- **Fiscal:** deuda pública % PIB y situación fiscal SPC/GNC (BIE Banrep).
- **Trayectorias:** 2 candidatos con gestión ejecutiva (Fajardo, López), 2 legislativos (Cepeda, Valencia), 1 sin gestión previa (Espriella) — todos con su archivo de historial.
