# Dr. Contexto — Pipeline RAG
## Supabase pgvector + ingesta de datos · Día 2

> Ejecuta cada sección en orden. No saltes pasos.

---

## PASO 1 — Verificar y activar pgvector en Supabase

### 1.1 Verificar si ya está activo

Entra a tu proyecto en Supabase → **SQL Editor** → ejecuta esto:

```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

- Si devuelve una fila → ✅ ya está activo, salta al Paso 2
- Si devuelve vacío → hay que activarlo

### 1.2 Activar pgvector

En el mismo SQL Editor:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Verifica de nuevo con la query del 1.1. Debe devolver una fila.

---

## PASO 2 — Crear el schema en Supabase

Ejecuta este SQL completo en el SQL Editor. Crea la tabla de documentos con todos los campos de metadata que necesita el Dr. Contexto:

```sql
-- Tabla principal de chunks
CREATE TABLE documents (
  id          BIGSERIAL PRIMARY KEY,
  content     TEXT NOT NULL,
  embedding   VECTOR(1024),          -- dimensión para voyage-large-2
  candidato   TEXT,                  -- 'fajardo' | 'lopez' | 'cepeda' | 'valencia' | 'espriella' | 'nacional'
  tema        TEXT,                  -- 'seguridad' | 'economia' | 'salud' | 'educacion' | 'anticorrupcion' | 'medioambiente'
  subtema     TEXT,                  -- detalle dentro del tema
  tipo        TEXT NOT NULL,         -- 'propuesta' | 'dato_historico' | 'estadistica_nacional'
  fuente      TEXT NOT NULL,         -- nombre del archivo o URL de origen
  pagina      INTEGER,               -- número de página en el PDF (si aplica)
  año         INTEGER,               -- año del dato o documento
  verificable BOOLEAN DEFAULT TRUE,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Índice vectorial para búsqueda semántica rápida
CREATE INDEX ON documents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Índices de metadata para filtrado eficiente
CREATE INDEX idx_documents_candidato ON documents(candidato);
CREATE INDEX idx_documents_tema      ON documents(tema);
CREATE INDEX idx_documents_tipo      ON documents(tipo);

-- Función de búsqueda semántica con filtros opcionales
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding  VECTOR(1024),
  match_count      INT     DEFAULT 5,
  filter_candidato TEXT    DEFAULT NULL,
  filter_tema      TEXT    DEFAULT NULL,
  filter_tipo      TEXT    DEFAULT NULL
)
RETURNS TABLE (
  id          BIGINT,
  content     TEXT,
  candidato   TEXT,
  tema        TEXT,
  subtema     TEXT,
  tipo        TEXT,
  fuente      TEXT,
  pagina      INTEGER,
  año         INTEGER,
  similarity  FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    d.id,
    d.content,
    d.candidato,
    d.tema,
    d.subtema,
    d.tipo,
    d.fuente,
    d.pagina,
    d.año,
    1 - (d.embedding <=> query_embedding) AS similarity
  FROM documents d
  WHERE
    (filter_candidato IS NULL OR d.candidato = filter_candidato)
    AND (filter_tema   IS NULL OR d.tema      = filter_tema)
    AND (filter_tipo   IS NULL OR d.tipo      = filter_tipo)
    AND d.embedding IS NOT NULL
  ORDER BY d.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
```

Verifica que se creó correctamente:

```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'documents'
ORDER BY ordinal_position;
```

Debe mostrar 11 columnas incluyendo `embedding` de tipo `USER-DEFINED`.

---

## PASO 3 — Instalar dependencias Python

En tu terminal, dentro del directorio del proyecto:

```bash
pip install pymupdf voyageai supabase python-dotenv tqdm
```

- `pymupdf` → extrae texto de PDFs
- `voyageai` → genera embeddings con voyage-large-2
- `supabase` → cliente Python para Supabase
- `python-dotenv` → maneja variables de entorno
- `tqdm` → barra de progreso en la terminal

---

## PASO 4 — Variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
VOYAGE_API_KEY=pa-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Dónde conseguir cada una:
- `SUPABASE_URL` y `SUPABASE_SERVICE_KEY` → Supabase Dashboard → Settings → API → usa la **service_role** key (no la anon)
- `VOYAGE_API_KEY` → [dash.voyageai.com](https://dash.voyageai.com) → API Keys → Create key

> ⚠️ Usa la `service_role` key de Supabase, no la `anon`. La anon no tiene permisos para insertar.

---

## PASO 5 — Estructura de carpetas esperada

El script asume esta estructura. Ajusta las rutas si las tuyas son distintas:

```
/dr-contexto-data/
├── /planes_gobierno/
│   ├── cepeda_plan_gobierno_2026.pdf
│   ├── fajardo_plan_gobierno_2026.pdf
│   ├── lopez_plan_gobierno_2026_v2.pdf
│   ├── valencia_plan_gobierno_2026.pdf
│   └── espriella_plan_gobierno_2026.pdf
├── /datasets_nacionales/
│   ├── dane_pobreza_2012_2024.csv
│   ├── dane_desempleo_2015_2026.csv
│   ├── banrep_deuda_publica_2010_2025.csv
│   ├── indepaz_lideres_2016_2026.pdf
│   └── indepaz_masacres_2020_2026.csv
└── /historiales_gestiones/
    ├── fajardo_historial_gestiones.md
    ├── lopez_historial_gestion.md
    ├── valencia_historial_congreso.md
    ├── cepeda_historial_congreso.md
    └── espriella_sin_gestion_previa.md
```

---

## PASO 6 — Script de ingesta

Crea el archivo `ingest.py` en la raíz del proyecto:

```python
import os
import re
import csv
import json
from pathlib import Path
from dotenv import load_dotenv

import fitz          # pymupdf
import voyageai
from supabase import create_client, Client
from tqdm import tqdm

load_dotenv()

# ── Clientes ──────────────────────────────────────────────────────────────────
supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_KEY"]
)
vo = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])

# ── Configuración de chunking ─────────────────────────────────────────────────
CHUNK_SIZE    = 800   # caracteres por chunk
CHUNK_OVERLAP = 150   # solapamiento entre chunks para no perder contexto

# ── Mapeo de archivos → metadata ──────────────────────────────────────────────
# Ajusta las rutas si tu estructura de carpetas es distinta
DATA_ROOT = Path("dr-contexto-data")

PDF_PLANS = [
    {
        "path":      DATA_ROOT / "planes_gobierno" / "cepeda_plan_gobierno_2026.pdf",
        "candidato": "cepeda",
        "tipo":      "propuesta",
        "fuente":    "cepeda_plan_gobierno_2026.pdf",
        "año":       2026,
    },
    {
        "path":      DATA_ROOT / "planes_gobierno" / "fajardo_plan_gobierno_2026.pdf",
        "candidato": "fajardo",
        "tipo":      "propuesta",
        "fuente":    "fajardo_plan_gobierno_2026.pdf",
        "año":       2026,
    },
    {
        "path":      DATA_ROOT / "planes_gobierno" / "lopez_plan_gobierno_2026_v2.pdf",
        "candidato": "lopez",
        "tipo":      "propuesta",
        "fuente":    "lopez_plan_gobierno_2026_v2.pdf",
        "año":       2026,
    },
    {
        "path":      DATA_ROOT / "planes_gobierno" / "valencia_plan_gobierno_2026.pdf",
        "candidato": "valencia",
        "tipo":      "propuesta",
        "fuente":    "valencia_plan_gobierno_2026.pdf",
        "año":       2026,
    },
    {
        "path":      DATA_ROOT / "planes_gobierno" / "espriella_plan_gobierno_2026.pdf",
        "candidato": "espriella",
        "tipo":      "propuesta",
        "fuente":    "espriella_plan_gobierno_2026.pdf",
        "año":       2026,
    },
]

PDF_DATASETS = [
    {
        "path":      DATA_ROOT / "datasets_nacionales" / "indepaz_lideres_2016_2026.pdf",
        "candidato": "nacional",
        "tipo":      "estadistica_nacional",
        "tema":      "seguridad",
        "subtema":   "lideres_asesinados",
        "fuente":    "indepaz_lideres_2016_2026.pdf",
        "año":       2026,
    },
    {
        "path":      DATA_ROOT / "datasets_nacionales" / "indepaz_masacres_2020_2026.pdf",
        "candidato": "nacional",
        "tipo":      "estadistica_nacional",
        "tema":      "seguridad",
        "subtema":   "masacres",
        "fuente":    "indepaz_masacres_2020_2026.pdf",
        "año":       2026,
    },
]

MD_HISTORIALES = [
    {
        "path":      DATA_ROOT / "historiales_gestiones" / "fajardo_historial_gestiones.md",
        "candidato": "fajardo",
        "tipo":      "dato_historico",
        "fuente":    "fajardo_historial_gestiones.md",
        "año":       2024,
    },
    {
        "path":      DATA_ROOT / "historiales_gestiones" / "lopez_historial_gestion.md",
        "candidato": "lopez",
        "tipo":      "dato_historico",
        "fuente":    "lopez_historial_gestion.md",
        "año":       2024,
    },
    {
        "path":      DATA_ROOT / "historiales_gestiones" / "valencia_historial_congreso.md",
        "candidato": "valencia",
        "tipo":      "dato_historico",
        "fuente":    "valencia_historial_congreso.md",
        "año":       2024,
    },
    {
        "path":      DATA_ROOT / "historiales_gestiones" / "cepeda_historial_congreso.md",
        "candidato": "cepeda",
        "tipo":      "dato_historico",
        "fuente":    "cepeda_historial_congreso.md",
        "año":       2024,
    },
    {
        "path":      DATA_ROOT / "historiales_gestiones" / "espriella_sin_gestion_previa.md",
        "candidato": "espriella",
        "tipo":      "dato_historico",
        "fuente":    "espriella_sin_gestion_previa.md",
        "año":       2024,
    },
]

CSV_DATASETS = [
    {
        "path":      DATA_ROOT / "datasets_nacionales" / "dane_pobreza_2012_2024.csv",
        "candidato": "nacional",
        "tipo":      "estadistica_nacional",
        "tema":      "economia",
        "subtema":   "pobreza_monetaria",
        "fuente":    "dane_pobreza_2012_2024.csv",
        "año":       2024,
    },
    {
        "path":      DATA_ROOT / "datasets_nacionales" / "dane_desempleo_2015_2026.csv",
        "candidato": "nacional",
        "tipo":      "estadistica_nacional",
        "tema":      "economia",
        "subtema":   "desempleo",
        "fuente":    "dane_desempleo_2015_2026.csv",
        "año":       2026,
    },
    {
        "path":      DATA_ROOT / "datasets_nacionales" / "banrep_deuda_publica_2010_2025.csv",
        "candidato": "nacional",
        "tipo":      "estadistica_nacional",
        "tema":      "economia",
        "subtema":   "deuda_publica",
        "fuente":    "banrep_deuda_publica_2010_2025.csv",
        "año":       2025,
    },
]

# ── Palabras clave para inferir tema automáticamente ─────────────────────────
TEMA_KEYWORDS = {
    "seguridad":      ["seguridad", "homicidio", "crimen", "policía", "fuerza pública",
                       "masacre", "líder", "extorsión", "narcotráfico", "coca", "eln",
                       "farc", "disidencias", "orden público", "delito"],
    "economia":       ["economía", "empleo", "desempleo", "pib", "fiscal", "impuesto",
                       "tributari", "deuda", "inversión", "crecimiento", "inflación",
                       "pobreza", "empresa", "pyme", "trabajo", "salario"],
    "salud":          ["salud", "eps", "hospital", "médico", "enfermedad", "covid",
                       "afiliación", "minsalud", "cobertura", "paciente", "clínica"],
    "educacion":      ["educación", "escuela", "colegio", "universidad", "matrícula",
                       "deserción", "docente", "maestro", "ciencia", "tecnología",
                       "investigación", "cti", "mineduc"],
    "anticorrupcion": ["corrupción", "transparencia", "contratación", "fiscal",
                       "procuraduría", "anticorrupción", "soborno", "peculado",
                       "contraloría", "rendición de cuentas"],
    "medioambiente":  ["ambiente", "clima", "carbono", "energía", "petróleo",
                       "transición", "deforestación", "biodiversidad", "agua",
                       "renovable", "solar", "eólica", "extractiv"],
}

def inferir_tema(texto: str) -> str:
    texto_lower = texto.lower()
    scores = {}
    for tema, keywords in TEMA_KEYWORDS.items():
        scores[tema] = sum(1 for kw in keywords if kw in texto_lower)
    mejor = max(scores, key=scores.get)
    return mejor if scores[mejor] > 0 else "general"

# ── Chunking ──────────────────────────────────────────────────────────────────
def chunk_texto(texto: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Divide texto en chunks con solapamiento, respetando párrafos cuando es posible."""
    parrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
    chunks, chunk_actual = [], ""

    for parrafo in parrafos:
        if len(chunk_actual) + len(parrafo) <= chunk_size:
            chunk_actual += ("\n\n" if chunk_actual else "") + parrafo
        else:
            if chunk_actual:
                chunks.append(chunk_actual)
            # Solapamiento: incluir el final del chunk anterior
            if len(chunk_actual) > overlap:
                chunk_actual = chunk_actual[-overlap:] + "\n\n" + parrafo
            else:
                chunk_actual = parrafo

    if chunk_actual:
        chunks.append(chunk_actual)

    return [c for c in chunks if len(c) > 100]  # descartar chunks muy cortos

# ── Extracción de texto ───────────────────────────────────────────────────────
def extraer_pdf(path: Path) -> list[dict]:
    """Extrae texto de un PDF página por página."""
    doc = fitz.open(str(path))
    paginas = []
    for i, page in enumerate(doc):
        texto = page.get_text("text").strip()
        if texto and len(texto) > 50:
            paginas.append({"texto": texto, "pagina": i + 1})
    doc.close()
    return paginas

def extraer_md(path: Path) -> str:
    """Lee un archivo Markdown."""
    return path.read_text(encoding="utf-8")

def extraer_csv(path: Path) -> str:
    """Convierte CSV a texto legible para embeddings."""
    lineas = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            linea = " | ".join(f"{k}: {v}" for k, v in row.items() if v)
            lineas.append(linea)
    return "\n".join(lineas)

# ── Embeddings ────────────────────────────────────────────────────────────────
def generar_embeddings(textos: list[str]) -> list[list[float]]:
    """Genera embeddings en batches de 128 (límite de Voyage AI)."""
    BATCH_SIZE = 128
    embeddings = []
    for i in range(0, len(textos), BATCH_SIZE):
        batch = textos[i:i + BATCH_SIZE]
        result = vo.embed(batch, model="voyage-large-2", input_type="document")
        embeddings.extend(result.embeddings)
    return embeddings

# ── Inserción en Supabase ─────────────────────────────────────────────────────
def insertar_chunks(chunks: list[dict]) -> None:
    """Inserta chunks con sus embeddings en Supabase en batches de 50."""
    BATCH_SIZE = 50
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        supabase.table("documents").insert(batch).execute()

# ── Procesadores por tipo de archivo ─────────────────────────────────────────
def procesar_pdf_plan(config: dict) -> list[dict]:
    """Procesa un PDF de plan de gobierno."""
    print(f"\n📄 Procesando plan: {config['path'].name}")
    paginas = extraer_pdf(config["path"])
    chunks_data = []

    for pagina in tqdm(paginas, desc="  Páginas"):
        chunks = chunk_texto(pagina["texto"])
        for chunk in chunks:
            tema = inferir_tema(chunk)
            chunks_data.append({
                "content":     chunk,
                "candidato":   config["candidato"],
                "tema":        tema,
                "tipo":        config["tipo"],
                "fuente":      config["fuente"],
                "pagina":      pagina["pagina"],
                "año":         config["año"],
                "verificable": True,
            })

    print(f"  → {len(chunks_data)} chunks extraídos")
    return chunks_data

def procesar_pdf_dataset(config: dict) -> list[dict]:
    """Procesa un PDF de dataset nacional (Indepaz, etc.)."""
    print(f"\n📊 Procesando dataset PDF: {config['path'].name}")
    paginas = extraer_pdf(config["path"])
    chunks_data = []

    for pagina in tqdm(paginas, desc="  Páginas"):
        chunks = chunk_texto(pagina["texto"])
        for chunk in chunks:
            chunks_data.append({
                "content":     chunk,
                "candidato":   config["candidato"],
                "tema":        config.get("tema", inferir_tema(chunk)),
                "subtema":     config.get("subtema"),
                "tipo":        config["tipo"],
                "fuente":      config["fuente"],
                "pagina":      pagina["pagina"],
                "año":         config["año"],
                "verificable": True,
            })

    print(f"  → {len(chunks_data)} chunks extraídos")
    return chunks_data

def procesar_md(config: dict) -> list[dict]:
    """Procesa un archivo Markdown de historial de gestión."""
    print(f"\n📝 Procesando historial: {config['path'].name}")
    texto = extraer_md(config["path"])
    chunks = chunk_texto(texto)
    chunks_data = []

    for chunk in chunks:
        tema = inferir_tema(chunk)
        chunks_data.append({
            "content":     chunk,
            "candidato":   config["candidato"],
            "tema":        tema,
            "tipo":        config["tipo"],
            "fuente":      config["fuente"],
            "año":         config["año"],
            "verificable": True,
        })

    print(f"  → {len(chunks_data)} chunks extraídos")
    return chunks_data

def procesar_csv(config: dict) -> list[dict]:
    """Procesa un CSV de dataset nacional."""
    print(f"\n📈 Procesando CSV: {config['path'].name}")
    texto = extraer_csv(config["path"])
    chunks = chunk_texto(texto, chunk_size=600)  # chunks más pequeños para CSVs
    chunks_data = []

    for chunk in chunks:
        chunks_data.append({
            "content":     chunk,
            "candidato":   config["candidato"],
            "tema":        config.get("tema", "economia"),
            "subtema":     config.get("subtema"),
            "tipo":        config["tipo"],
            "fuente":      config["fuente"],
            "año":         config["año"],
            "verificable": True,
        })

    print(f"  → {len(chunks_data)} chunks extraídos")
    return chunks_data

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("Dr. Contexto — Pipeline de ingesta")
    print("=" * 60)

    todos_los_chunks = []

    # 1. Planes de gobierno (PDFs)
    print("\n▶ BLOQUE 1: Planes de gobierno")
    for config in PDF_PLANS:
        if config["path"].exists():
            todos_los_chunks.extend(procesar_pdf_plan(config))
        else:
            print(f"  ⚠️  No encontrado: {config['path']}")

    # 2. Datasets nacionales (PDFs)
    print("\n▶ BLOQUE 2: Datasets nacionales (PDF)")
    for config in PDF_DATASETS:
        if config["path"].exists():
            todos_los_chunks.extend(procesar_pdf_dataset(config))
        else:
            print(f"  ⚠️  No encontrado: {config['path']}")

    # 3. Historiales de gestión (Markdown)
    print("\n▶ BLOQUE 3: Historiales de gestión")
    for config in MD_HISTORIALES:
        if config["path"].exists():
            todos_los_chunks.extend(procesar_md(config))
        else:
            print(f"  ⚠️  No encontrado: {config['path']}")

    # 4. Datasets numéricos (CSV)
    print("\n▶ BLOQUE 4: Datasets CSV")
    for config in CSV_DATASETS:
        if config["path"].exists():
            todos_los_chunks.extend(procesar_csv(config))
        else:
            print(f"  ⚠️  No encontrado: {config['path']}")

    # Resumen antes de embeddings
    print(f"\n{'=' * 60}")
    print(f"Total chunks a procesar: {len(todos_los_chunks)}")
    print(f"Costo estimado embeddings: ~${len(todos_los_chunks) * 800 / 1_000_000 * 0.12:.4f} USD")
    print(f"{'=' * 60}")
    input("\nPresiona Enter para generar embeddings e insertar en Supabase...")

    # Generar embeddings
    print("\n⚙️  Generando embeddings con voyage-large-2...")
    textos = [c["content"] for c in todos_los_chunks]
    embeddings = generar_embeddings(textos)

    # Adjuntar embeddings a los chunks
    for chunk, emb in zip(todos_los_chunks, embeddings):
        chunk["embedding"] = emb

    # Insertar en Supabase
    print(f"\n⬆️  Insertando {len(todos_los_chunks)} chunks en Supabase...")
    insertar_chunks(todos_los_chunks)

    print(f"\n✅ Ingesta completada")
    print(f"   Chunks insertados: {len(todos_los_chunks)}")
    print(f"   Tabla: documents")

if __name__ == "__main__":
    main()
```

---

## PASO 7 — Ejecutar el pipeline

```bash
python ingest.py
```

El script va a:
1. Procesar todos los archivos y mostrar cuántos chunks extrae de cada uno
2. Pedirte confirmación antes de generar embeddings (para que veas el costo estimado)
3. Generar los embeddings con Voyage AI
4. Insertarlos todos en Supabase

Tiempo estimado: 3–5 minutos dependiendo del volumen total.

---

## PASO 8 — Verificar que todo quedó bien

En Supabase → SQL Editor:

```sql
-- Total de chunks insertados
SELECT COUNT(*) FROM documents;

-- Distribución por candidato
SELECT candidato, COUNT(*) as chunks
FROM documents
GROUP BY candidato
ORDER BY chunks DESC;

-- Distribución por tipo
SELECT tipo, COUNT(*) as chunks
FROM documents
GROUP BY tipo;

-- Distribución por tema
SELECT tema, COUNT(*) as chunks
FROM documents
GROUP BY tema
ORDER BY chunks DESC;

-- Verificar que los embeddings se generaron
SELECT COUNT(*) FROM documents WHERE embedding IS NULL;
-- Este debe devolver 0
```

**Resultado esperado aproximado:**

| candidato | chunks |
|---|---|
| fajardo | 150–300 |
| lopez | 120–250 |
| cepeda | 120–250 |
| valencia | 80–150 |
| espriella | 30–80 |
| nacional | 100–200 |

---

## PASO 9 — Prueba de retrieval

Antes de construir el backend, verifica que el retrieval funciona desde Python:

```python
# test_retrieval.py
import os
from dotenv import load_dotenv
import voyageai
from supabase import create_client

load_dotenv()

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])
vo = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])

def buscar(pregunta: str, k: int = 5, candidato: str = None, tema: str = None):
    # Generar embedding de la pregunta
    result = vo.embed([pregunta], model="voyage-large-2", input_type="query")
    query_embedding = result.embeddings[0]

    # Llamar a la función de Supabase
    response = supabase.rpc("match_documents", {
        "query_embedding":  query_embedding,
        "match_count":      k,
        "filter_candidato": candidato,
        "filter_tema":      tema,
    }).execute()

    return response.data

# Pruebas
preguntas = [
    "¿Qué propone Fajardo en seguridad?",
    "¿Cuál es la tasa de homicidios en Colombia?",
    "¿Qué hizo Claudia López con la deuda de Bogotá?",
    "¿Qué propone Cepeda sobre las EPS?",
    "¿Cuál es la propuesta económica de Valencia?",
]

for pregunta in preguntas:
    print(f"\n{'─' * 50}")
    print(f"🔍 {pregunta}")
    resultados = buscar(pregunta, k=3)
    for r in resultados:
        print(f"  [{r['candidato']} · {r['tema']} · {r['tipo']}] sim={r['similarity']:.3f}")
        print(f"  {r['content'][:150]}...")
```

```bash
python test_retrieval.py
```

Si ves resultados relevantes con similaridad > 0.7 → el pipeline funciona correctamente.

---

## Troubleshooting frecuente

| Error | Causa | Solución |
|---|---|---|
| `could not find extension "vector"` | pgvector no instalado en el plan de Supabase | Activar en SQL Editor con `CREATE EXTENSION vector` |
| `embedding dimension mismatch` | La dimensión del vector no coincide con la columna | Verificar que `voyage-large-2` genera 1024 dims. Si usas otro modelo, ajusta `VECTOR(1024)` en el schema |
| `permission denied for table documents` | Usando la key `anon` en vez de `service_role` | Cambiar `SUPABASE_SERVICE_KEY` por la `service_role` key |
| PDF sin texto extraído | PDF escaneado (imagen) | Instalar `pytesseract` + `pdf2image` y agregar OCR |
| `voyage API rate limit` | Demasiados requests | El script ya usa batches de 128 — si persiste, agregar `time.sleep(1)` entre batches |

---

## Siguiente paso

Con la base de datos cargada y el retrieval verificado, el siguiente paso es el **backend FastAPI** con el endpoint `/chat` que:

1. Recibe la pregunta del usuario
2. Genera el embedding de la pregunta
3. Llama a `match_documents` en Supabase
4. Construye el contexto RAG
5. Llama a Claude Sonnet con el system prompt del Dr. Contexto
6. Devuelve la respuesta estructurada

---

*Documento parte del proyecto Dr. Contexto · ver también `dr-contexto-plan.md`, `dr-contexto-modelos.md`, `dr-contexto-datos.md`*