# Dr. votIA (ex «Dr. Contexto») — Agente Politólogo con RAG
## Plan de construcción · Elecciones Colombia 2026

> **Estado al 2026-05-30:** Backend RAG **terminado y funcionando** (3.876 chunks
> cargados en pgvector, 27 tests verdes). Falta **todo el frontend** y el endpoint
> de radar/scoring. Ver sección 7 para el detalle por día.

---

## 1. Concepto del agente

**Nombre:** Dr. Contexto  
**Perfil:** Politólogo internacional con PhD, 20 años analizando democracias latinoamericanas. Sin partido, sin miedo. Si una propuesta no tiene cifras que la soporten, lo dice. Si un candidato prometió algo en gestión anterior y no lo cumplió, lo confronta con datos. Habla con precisión académica pero sin jerga innecesaria.

**Método:** Estrictamente empírico. Ninguna afirmación vale sin dato que la respalde.

**Tono:** Brutal con evidencia — no opina desde la ideología, sino desde los números.

---

## 2. Arquitectura técnica

```
PDFs planes de gobierno
Datos históricos de gestiones    →   Chunking + metadata   →   pgvector (Supabase)
Datasets DANE / Indepaz / otros                                        ↓
                                                             RAG retrieval
                                                                       ↓
                                              Claude Sonnet + System Prompt "Dr. Contexto"
                                                                       ↓
                                         Next.js: Chat + Radar chart + Tabla comparativa
```

**Stack (lo que se construyó realmente — difiere del plan original):**
- **Backend:** ✅ Python 3.12 + FastAPI, **arquitectura hexagonal** (domain / application /
  infrastructure / entrypoints). *No NestJS.* Proyecto `dr-votia/`.
- **Frontend:** ⛔ **Pendiente.** Next.js 15 + recharts (aún no iniciado).
- **Vector store:** ✅ Supabase pgvector (proyecto `vaskxyxgehgwrvbjynuy`), tabla
  `documents` con índice HNSW y función `match_documents`.
- **LLM:** ✅ vía **OpenRouter** (no Anthropic directo). Flujo **dual-model**:
  `deepseek/deepseek-v4-flash` reescribe/clasifica la query (barato) →
  `anthropic/claude-sonnet-4.6` redacta la respuesta (calidad).
- **Pipeline RAG:** ✅ Ingesta propia en Python (no LlamaIndex/LangChain), CLI
  `uv run dr-votia ingest`.
- **Embeddings:** ✅ **Voyage `voyage-3.5`** (1024 dims). *No OpenAI* — se eligió
  Voyage por compatibilidad de dimensiones y costo (ver REPORTE_PGVECTOR.md).

---

## 3. Fuentes de datos

### 3.1 Planes de gobierno (PDFs oficiales)

| Candidato | Fuente |
|---|---|
| Iván Cepeda | [movimientopactohistorico.co/docs/programa-gobierno-2026-2030.pdf](https://www.movimientopactohistorico.co/docs/programa-gobierno-2026-2030.pdf) |
| Paloma Valencia | [palomapresidente.com.co/programa-integrado-de-gobierno](https://palomapresidente.com.co/programa-integrado-de-gobierno) — Plan 111 |
| Sergio Fajardo | [lasillavacia.com — Programa Fajardo 2026–2030](https://www.lasillavacia.com/wp-content/uploads/2026/04/Programa_de_gobierno_Sergio_Fajardo_2026_2030-1.pdf) |
| Claudia López | [claudia-lopez.com/wp-content/uploads/2026/02/Programa-de-Gobierno-Claudia-Lopez.pdf](https://claudia-lopez.com/wp-content/uploads/2026/02/Programa-de-Gobierno-Claudia-Lopez.pdf) |
| Abelardo de la Espriella | Verificar en CNE — sin programa formal publicado al momento del análisis |
| Todos | Repositorio CNE: [cne.gov.co/elecciones/elecciones-2026](https://www.cne.gov.co/elecciones/elecciones-2026) |

### 3.2 Datasets de problemáticas Colombia (todos públicos y gratuitos)

| Dataset | Fuente | URL | Qué mide |
|---|---|---|---|
| Pobreza monetaria por dpto | DANE | dane.gov.co | % población bajo línea de pobreza |
| Desempleo histórico | DANE | dane.gov.co | Tasa por trimestre 2015–2025 |
| Homicidios y masacres | Indepaz | indepaz.org.co | Conflicto armado, líderes asesinados |
| Percepción de corrupción | Transparencia por Colombia | transparenciacolombia.org.co | Índice nacional y territorial |
| Cobertura en salud | MinSalud | minsalud.gov.co | Afiliación, mortalidad, acceso |
| Cobertura en educación | MinEducación | mineducacion.gov.co | Matrícula, deserción, calidad |
| Deuda pública | Banco de la República | banrep.gov.co | % PIB histórico |
| Inversión extranjera | ProColombia | procolombia.co | Flujos por sector |

### 3.3 Historial de gestiones anteriores (el activo diferencial)

| Candidato | Cargo previo | Qué buscar |
|---|---|---|
| Sergio Fajardo | Alcalde Medellín 2004–2007 / Gobernador Antioquia 2012–2015 | Tasa de homicidios, cobertura educativa, inversión en ciencia |
| Claudia López | Alcaldesa Bogotá 2020–2023 | Movilidad, seguridad ciudadana, deuda distrital, gestión COVID |
| Paloma Valencia | Senadora 2014–2026 | Votaciones en el Congreso, proyectos radicados/aprobados |
| Iván Cepeda | Senador 2010–2026 | Votaciones, denuncias de parapolítica, proyectos de ley |
| Abelardo de la Espriella | Sin cargo público previo | **Este vacío ya es un dato analizable** |

**Fuentes para historial:** Wikipedia, informes de gestión oficiales, La Silla Vacía (lasillavacia.com), Congreso Visible (congresovisible.uniandes.edu.co).

---

## 4. Estructura de los chunks (metadata crítica)

Cada fragmento de texto indexado en pgvector debe tener este esquema de metadata:

```json
{
  "candidato": "Fajardo",
  "tema": "seguridad",
  "subtema": "homicidios",
  "tipo": "propuesta" | "dato_historico" | "estadistica_nacional",
  "fuente": "plan_gobierno_2026.pdf",
  "pagina": 14,
  "año": 2026,
  "verificable": true
}
```

> **Regla crítica:** el campo `tipo` permite al agente distinguir entre lo que el candidato *promete* y lo que *hizo* o lo que *el país realmente vive*. Sin esto, el agente no puede hacer el análisis diferencial.

---

## 5. Los 6 ejes temáticos del radar

Estos ejes estructuran todas las comparaciones visuales y el análisis del agente:

1. **Seguridad** — propuesta concreta vs. resultados históricos de orden público
2. **Economía y empleo** — modelo fiscal, metas de crecimiento, política de empleo
3. **Salud** — modelo de aseguramiento, cobertura propuesta, crítica al estado actual
4. **Educación** — inversión, calidad, cobertura, ciencia y tecnología
5. **Anticorrupción** — mecanismos propuestos, historial personal, independencia institucional
6. **Medio ambiente y transición energética** — coherencia con acuerdos climáticos y realidad extractivista

**Escala de evaluación por eje (usada en el radar chart):**

| Puntaje | Criterio |
|---|---|
| 5 | Propuesta concreta con meta medible y respaldo estadístico |
| 4 | Propuesta específica sin meta cuantificada |
| 3 | Propuesta general con dirección clara |
| 2 | Retórica sin ancla estadística |
| 1 | Ausencia total de propuesta en el eje |

---

## 6. System prompt — Guacamayo, el politólogo

> **Nombre del agente:** «Guacamayo, el politólogo» (decisión 2026-05-30; antes
> «Dr. Contexto» / «Dr. votIA»). Implementado en `application/prompts.py` con el
> tono empírico «brutal con evidencia» de abajo. El boilerplate de marca del
> producto (título de API, CLI, header OpenRouter) sigue como «Dr. votIA» por ahora.
>
> **Scoring del radar:** lo calcula el **LLM** a partir de los chunks recuperados,
> aplicando la escala 1–5 de la sección 5 (decisión 2026-05-30). Pendiente de
> implementar el endpoint y la lógica de evaluación.

Prompt original de referencia (la implementación real ya lo adaptó al nombre nuevo):


```
Eres el Dr. Contexto, politólogo internacional con PhD en Ciencia Política 
(Universidad de los Andes / LSE). Has analizado 15 democracias latinoamericanas 
durante 20 años. Tu método es estrictamente empírico: ninguna afirmación vale 
sin dato que la respalde.

REGLAS DE ANÁLISIS:
1. Siempre citas la fuente exacta: plan de gobierno (pág. X), DANE (año), 
   Indepaz (año), informe de gestión (cargo, período).
2. Si una propuesta no tiene cifra que la respalde, la clasificas explícitamente 
   como "retórica sin ancla estadística".
3. Si un candidato tuvo gestión previa, confrontas sus propuestas actuales con 
   sus resultados reales medidos. Sin excepción.
4. No tienes partido. Si los datos favorecen a un candidato de izquierda o derecha, 
   los presentas igual.
5. Cuando detectas contradicción entre propuesta y historial, la señalas con 
   nombre propio: "El candidato X propone Y, pero durante su gestión como Z, 
   el indicador W pasó de A a B."
6. Si un candidato no tiene gestión previa, lo señalas como factor de riesgo 
   evaluable: ausencia de trayectoria verificable.
7. Tus comparaciones usan la escala de 1 a 5 definida en los ejes temáticos.

ESTRUCTURA DE RESPUESTA OBLIGATORIA:
→ Diagnóstico estadístico (¿qué dicen los datos del país en este tema?)
→ Análisis por candidato (propuesta + historial + evaluación)
→ Veredicto comparativo (quién tiene la propuesta más sólida estadísticamente y por qué)

CONTEXTO DISPONIBLE (RAG):
{rag_context}
```

---

## 7. Plan de ejecución — 4 días

### Día 1 — Solo datos, cero código ✅ COMPLETO
- [x] Descargar los 5 PDFs de planes de gobierno (Cepeda, Valencia, Fajardo, López, Espriella)
- [x] Descargar datasets DANE (pobreza nacional + departamental, desempleo GEIH abr-2026)
- [x] Descargar datos de Indepaz (balance violencia 2025, líderes 2024)
- [x] Recolectar historial de gestión de Fajardo y López
- [x] Recolectar historial en Congreso de Valencia y Cepeda
- [x] Documentar el vacío de gestión de De la Espriella (`espriella_sin_gestion_previa.md`)
- [x] Definir los 6 ejes finales y la escala de evaluación
- Extra: Banrep (indicadores económicos), Transparencia (ITEP), y `fuentes_analisis/` (Cóndor, Fede, Razón Pública)
- Formatos reales: mezcla de PDF / XLSX / TXT / MD (ver REPORTE_RECOLECCION.md)

### Día 2 — Pipeline RAG ✅ COMPLETO
- [x] Activar pgvector en Supabase, tabla `documents` con schema de metadata (HNSW, `match_documents`)
- [x] Pipeline Python: parsear PDF/XLSX/TXT/MD → chunks → embeddings Voyage → insertar en pgvector
- [x] Ingesta de estadísticas nacionales (`tipo: estadistica_nacional`)
- [x] Retrieval funcionando — **3.876 chunks cargados** (2.277 nacional, 1.568 propuestas, 31 históricos)
- Tests: 27 verdes (domain + application + web con fakes, sin red)

### Día 3 — API + Frontend ⚠️ PARCIAL (backend sí, frontend no)
- [x] Endpoint `POST /chat` (FastAPI) → RAG retrieval → dual-model → respuesta con fuentes
- [x] Endpoint `GET /health`
- [x] **Endpoint `GET /radar/:candidato`** y `GET /radar` → scorecards por eje en JSON
- [x] **Lógica de scoring por LLM** (`application/score_candidates.py`): solidez 1–5
  (media ± desviación sobre K corridas), densidad de evidencia, anclaje nacional,
  coherencia propuesta–gestión, + métricas deterministas (volumen, cobertura, HHI,
  presencia histórica) y confianza. Pre-cálculo vía `uv run dr-votia score` →
  tabla `candidate_scores`. 11 tests nuevos (38 totales)
- [ ] **Next.js: interfaz de chat** con el Dr. votIA
- [ ] **Next.js: radar chart** con recharts (6 ejes, hasta 3 candidatos)
- [ ] **Next.js: tabla comparativa** generada desde JSON del agente

### Día 4 — Calibración ⚠️ PARCIAL
- [x] Refinamiento de query implementado (`refine_query.py`) + clasificación de tema
- [x] System prompt «Dr. Contexto» implementado (`application/prompts.py`)
- [ ] Probar con casos reales difíciles (seguridad creíble / López cumplió / viabilidad fiscal)
- [ ] Afinar tono: brutal pero con evidencia, no con opinión

---

## 8. Costos estimados

| Componente | Detalle | Costo |
|---|---|---|
| Claude Sonnet via API | Uso intensivo 4 días (~500 queries) | ~$5–10 USD |
| Embeddings (Voyage AI o OpenAI) | Ingesta de ~500 chunks | ~$0.10 USD |
| Supabase pgvector | Free tier (suficiente para este volumen) | $0 |
| Vercel (hosting Next.js) | Free tier | $0 |
| Datasets DANE / Indepaz | Públicos | $0 |
| **Total estimado** | | **< $15 USD** |

> El costo real es tiempo, no dinero. El cuello de botella es la recolección y limpieza de datos históricos de gestiones (Día 1).

---

## 9. Riesgos y mitigaciones

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| De la Espriella no tiene programa oficial | Alta | Usar entrevistas + redes sociales como fuente, marcarlo como `fuente: declaraciones_publicas` |
| PDFs con texto no seleccionable (escaneados) | Media | OCR con PyMuPDF o pdf2image + Tesseract |
| Datos históricos de gestiones incompletos | Alta | Priorizar La Silla Vacía y Wikipedia como fuente rápida; profundizar después |
| Sesgo del agente por datos incompletos | Media | El prompt fuerza al agente a declarar explícitamente cuando hay ausencia de datos |
| Tiempo insuficiente para 4 días | Media | MVP mínimo viable: chat funcional + 1 radar con datos manuales si el pipeline falla |

---

## 10. MVP mínimo viable (si el tiempo aprieta)

Si el pipeline RAG completo no está listo antes del 31 de mayo, este es el fallback:

1. **Chat con Claude directo** — sin RAG, pero con los planes de gobierno pegados en el system prompt (caben ~3 PDFs resumidos en el contexto)
2. **Radar estático** — scores calculados manualmente por ti y hardcodeados en el frontend
3. **Sin datos históricos** — se agregan en iteración post-primera vuelta

El agente funciona. No es perfecto, pero sirve para el análisis del 31.

---

*Documento generado: mayo 2026 — Proyecto personal de análisis político con IA*