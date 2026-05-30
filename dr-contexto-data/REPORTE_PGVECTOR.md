# Reporte — Activación pgvector + Schema RAG (Dr. Contexto)

**Fecha:** 2026-05-29
**Proyecto Supabase:** `vaskxyxgehgwrvbjynuy`
**Pipeline de referencia:** `Docs/pipeline.md`

---

## Estado general

| Paso | Descripción | Estado |
|---|---|---|
| 1 | Activar pgvector | ✅ Hecho y verificado |
| 2 | Crear schema (`documents` + función) | ✅ Hecho y verificado |
| 3 | Dependencias Python | ⏸️ Pendiente (local) |
| 4 | Variables de entorno (`.env`) | ⛔ Bloqueante — faltan secrets |
| 5 | Estructura de carpetas | ⚠️ No coincide con el script |
| 6 | Script de ingesta (`ingest.py`) | ⛔ Requiere reescritura |
| 7 | Ejecutar pipeline | ⛔ Bloqueado por 4 y 6 |
| 8 | Verificar carga | ⛔ Bloqueado |
| 9 | Prueba de retrieval | ⛔ Bloqueado |

---

## Lo que quedó hecho

### Paso 1 — pgvector
- Extensión `vector` **v0.8.0** instalada en el schema `extensions` (convención Supabase, no en `public`).
- Registrado como migración `enable_pgvector_extension`.

### Paso 2 — Schema
- Tabla `public.documents` con 12 columnas. Columna `embedding` de tipo `extensions.vector(1024)`.
- Función `public.match_documents(...)` con filtros opcionales por candidato/tema/tipo.
- Registrado como migración `create_documents_schema`.

**Verificación ejecutada:**
- `documents`: 12 columnas, RLS = `true`, 0 filas.
- Índices: `documents_pkey`, `documents_embedding_hnsw_idx` (HNSW), `idx_documents_candidato`, `idx_documents_tema`, `idx_documents_tipo`.

---

## Decisiones de arquitectura (cambios sobre el pipeline original)

### 1. Modelo de embeddings: `voyage-3.5` (1024 dims) — NO `voyage-large-2`
**Por qué:** el pipeline decía `VECTOR(1024)` "para voyage-large-2", pero **`voyage-large-2` genera 1536 dimensiones**, no 1024. Era una incompatibilidad que habría reventado la ingesta con `embedding dimension mismatch`. Además `voyage-large-2` es de 2.ª generación (legacy). `voyage-3.5` es el modelo vigente, soporta 1024 dims nativo, es más barato y mejor.
**Impacto en el código:** en `ingest.py` y `test_retrieval.py` el modelo debe ser `model="voyage-3.5"` (no `voyage-large-2`). El schema `VECTOR(1024)` queda igual.

### 2. Índice vectorial HNSW — NO ivfflat
**Por qué:** `ivfflat` entrena sus centroides con los datos existentes; crearlo sobre una tabla vacía con `lists=100` produce un índice mal calibrado. **HNSW** se construye de forma incremental, sin entrenamiento previo, y ofrece mejor recall/latencia. Para una tabla que se llena después de crearse, es la opción correcta.

### 3. RLS activado sin políticas
**Por qué:** la tabla se consulta solo desde el backend con la `service_role` key (que ignora RLS). Dejarla con RLS activo y sin políticas la mantiene cerrada al exterior (anon/authenticated no leen nada). Es defensa en profundidad estándar de Supabase.
**Nota:** el advisor reporta `rls_enabled_no_policy` como INFO — es **esperado e intencional** con este diseño.

### 4. Función `match_documents` endurecida
- `security invoker` + `set search_path = public, extensions` (evita el warning `function_search_path_mutable` y resuelve el operador `<=>` de pgvector correctamente).
- `stable` para permitir optimizaciones del planner.

---

## Bloqueantes para continuar (Pasos 3–9)

### Bloqueante A — Faltan secrets (Paso 4)
No existe `.env`. Para la ingesta necesito que vos consigas y cargues:

| Variable | Dónde |
|---|---|
| `SUPABASE_URL` | Dashboard → Settings → API |
| `SUPABASE_SERVICE_KEY` | Dashboard → Settings → API → **service_role** (NO la anon; con RLS activo, anon no inserta) |
| `VOYAGE_API_KEY` | dash.voyageai.com → API Keys |

> No puedo extraer la `service_role` key vía MCP — es un secret. La tenés que copiar vos del dashboard.

### Bloqueante B — Los datos reales NO coinciden con el script (Pasos 5–6)
El `ingest.py` del pipeline asume archivos que no existen tal cual. Comparación real:

| Script espera | Realidad en `dr-contexto-data/` | Acción |
|---|---|---|
| `dane_pobreza_2012_2024.csv` | `dane_pobreza_nacional_2012_2024.xlsx` (XLSX) | Leer XLSX (necesita `openpyxl`/`pandas`, no `csv`) |
| `dane_desempleo_2015_2026.csv` | `dane_desempleo_geih_abr2026.xlsx` (XLSX) | idem |
| `banrep_deuda_publica_2010_2025.csv` | `banrep_indicadores_economicos_2026.pdf` (PDF) | Procesar como PDF, no CSV |
| `indepaz_lideres_2016_2026.pdf` | `indepaz_lideres_2024_texto.txt` (TXT) | Procesar como TXT |
| `indepaz_masacres_2020_2026.pdf` | `indepaz_balance_violencia_2025.pdf` | Re-mapear nombre |
| — | `dane_pobreza_departamental_2024.xlsx` | Sin mapear — ¿incluir? |
| — | `transparencia_itep_texto.txt` | Sin mapear — ¿tema anticorrupción? |
| — | `fuentes_analisis/*.txt` (3 archivos) | Sin mapear — ¿qué candidato/tipo? |

Los 5 planes de gobierno (PDF) y los 5 historiales (MD) **sí coinciden** con el script.

El `ingest.py` necesita reescritura para: (a) usar `voyage-3.5`, (b) leer XLSX, (c) re-mapear nombres reales, (d) decidir qué hacer con los archivos extra (requiere tu criterio de negocio: a qué candidato/tema/tipo asignar cada análisis).

---

## Hallazgo de seguridad pre-existente (no causado por este trabajo)

El advisor detectó una función **anterior** a mi cambio:

- `public.rls_auto_enable()` — es `SECURITY DEFINER` y **ejecutable por `anon` y `authenticated`** vía `/rest/v1/rpc/rls_auto_enable`.
- Riesgo: una función `SECURITY DEFINER` pública corre con privilegios elevados y puede ser invocada sin autenticación.
- Recomendación: revisar si es intencional. Si no, `REVOKE EXECUTE` a anon/authenticated, pasarla a `SECURITY INVOKER`, o moverla a un schema no expuesto.
- Doc: https://supabase.com/docs/guides/database/database-linter?lint=0028_anon_security_definer_function_executable

---

## Próximos pasos

1. **Vos:** crear `.env` con las 3 variables (Bloqueante A).
2. **Yo:** reescribir `ingest.py` (voyage-3.5 + XLSX + nombres reales). Necesito tu criterio para los archivos extra (Bloqueante B).
3. **Yo:** ejecutar ingesta, verificar carga (Paso 8) y prueba de retrieval (Paso 9).
4. **Opcional:** revisar `rls_auto_enable()`.
