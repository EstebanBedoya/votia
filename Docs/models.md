# Dr. Contexto — Decisión de Modelos LLM
## Análisis objetivo · OpenRouter · Mayo 2026

---

## Contexto de la decisión

**Agente:** Dr. Contexto — politólogo con RAG que analiza candidatos presidenciales Colombia 2026  
**Requerimientos clave:**
- Razonamiento político complejo con datos estadísticos
- Respuestas largas y estructuradas con citación de fuentes
- Seguimiento estricto de system prompt (persona + reglas de análisis)
- Análisis en español con precisión factual
- Uso personal, ~500 queries en 4 días
- API vía OpenRouter (una sola key, acceso a todos los modelos)

**Criterios de evaluación:** rendimiento en español, factual accuracy, seguimiento de instrucciones complejas, costo por token, consistencia de persona.

---

## Top 5 modelos evaluados

### 🥇 1. Claude Sonnet 4.6
**Proveedor:** Anthropic  
**Precio OpenRouter:** $3.00/M input · $15.00/M output  
**Contexto:** 1M tokens  

**Por qué lidera para este caso:**
- Mejor seguimiento de system prompts complejos del mercado — crítico para mantener el personaje del Dr. Contexto
- Consistencia de tono en respuestas largas y estructuradas
- Rendimiento superior en análisis de texto político en español
- Contexto 1M a precio estándar con soporte de caching
- Mejor price-to-capability ratio para producción general con razonamiento

**Debilidad:** En factual recall de conocimiento del mundo real, Gemini 3.1 Pro mantiene ventaja (SimpleQA-Verified: Gemini 75.6% vs Claude en posición inferior).

**Veredicto:** ✅ Modelo principal del agente.

---

### 🥈 2. DeepSeek V4 Pro
**Proveedor:** DeepSeek (open-weight)  
**Precio OpenRouter:** $0.435/M input · $0.87/M output  
**Contexto:** 1M tokens  

**Por qué está en el top:**
- Primer modelo open-weight que llega cerca de Claude Opus 4.7 y GPT-5.5 en benchmarks de razonamiento
- Aproximadamente 1/30 del costo por token vs modelos frontier cerrados
- SWE-bench Verified: 80.6% — dentro de 0.2 puntos de Claude Opus 4.6
- 1.6T parámetros totales, 49B activados (MoE), arquitectura eficiente

**Por qué NO es el #1 para Dr. Contexto:**
- SimpleQA-Verified: 57.9% vs Gemini 75.6% — brecha significativa en recall factual
- Para un agente que cita datos históricos y estadísticas, alucinar en hechos es inaceptable
- Trained on Huawei Ascend 950PR chips (no NVIDIA) — no es bloqueante para uso personal pero es un dato
- Texto only al lanzamiento — sin procesamiento de imágenes/PDFs directo

**Veredicto:** ⚠️ Excelente relación costo/rendimiento, pero el riesgo de alucinación factual lo descarta como modelo principal para este agente.

---

### 🥉 3. Gemini 3.1 Pro Preview
**Proveedor:** Google  
**Precio OpenRouter:** $2.00/M input · $12.00/M output  
**Contexto:** 1M tokens  

**Por qué está aquí:**
- Mejor factual accuracy del mercado: SimpleQA-Verified 75.6%
- HLE (Humanity's Last Exam): 44.4% — el más alto del top 5
- Soporte nativo de PDFs, imágenes, audio, video
- Razonamiento configurable por niveles

**Por qué no es el #1:**
- Modelo en Preview — menor estabilidad en producción
- Precio similar a Sonnet con peor seguimiento de instrucciones complejas y consistencia de persona
- Tool calling menos robusto que Sonnet para agentic workflows

**Veredicto:** 🔄 Alternativa válida si la prioridad absoluta es no alucinar en datos históricos. Considerar si los datos de gestión de candidatos son difíciles de verificar.

---

### 4. Gemini 3.5 Flash
**Proveedor:** Google  
**Precio OpenRouter:** $1.50/M input · $9.00/M output  
**Contexto:** 1M tokens  

**Características:**
- Near-Pro level coding y razonamiento a precio Flash
- Soporte nativo PDFs, audio, video, imágenes
- Reasoning configurable (minimal/low/medium/high)
- Optimizado para loops agénticos paralelos

**Veredicto:** 💡 Buena opción para capa de pre-procesamiento o queries de menor complejidad. Mitad del precio de Sonnet.

---

### 5. DeepSeek V4 Flash
**Proveedor:** DeepSeek (open-weight)  
**Precio OpenRouter:** < $0.435/M input (precio inferior a V4 Pro)  
**Contexto:** 1M tokens  

**Características:**
- SWE-bench Verified: 79.0% vs 80.6% de V4-Pro — solo 1.6 puntos de diferencia
- Misma arquitectura base que V4 Pro, menor costo
- Fuerte para tareas de clasificación, extracción, retrieval

**Veredicto:** 💡 Fallback económico para tareas de baja complejidad en el pipeline RAG.

---

## Decisión final: arquitectura dual de modelos

No usar un solo modelo. Usar dos con roles distintos:

| Rol | Modelo | Precio output | Por qué |
|---|---|---|---|
| **Agente principal** — respuestas del Dr. Contexto, análisis político, veredictos comparativos | **Claude Sonnet 4.6** | $15/M | Mejor seguimiento de system prompt, tono consistente, análisis estructurado en español |
| **Pipeline RAG** — clasificación de chunks, pre-procesamiento, queries de retrieval simples | **DeepSeek V4 Flash** | < $0.87/M | ~20x más barato, suficiente para tareas de baja complejidad |

### Flujo concreto

```
Usuario hace pregunta
        ↓
DeepSeek V4 Flash → reformula query para retrieval, clasifica tema
        ↓
pgvector → recupera chunks relevantes (k=5)
        ↓
Claude Sonnet 4.6 → recibe [system prompt Dr. Contexto] + [chunks RAG] + [pregunta]
        ↓
Respuesta estructurada: diagnóstico → análisis por candidato → veredicto
```

---

## Estimación de costos con arquitectura dual

| Componente | Volumen estimado | Costo |
|---|---|---|
| Claude Sonnet 4.6 — ~500 queries, ~2K tokens output promedio | 1M output tokens | ~$15 |
| Claude Sonnet 4.6 — input con contexto RAG, ~3K tokens promedio | 1.5M input tokens | ~$4.50 |
| DeepSeek V4 Flash — pre-procesamiento RAG, ~500 queries | volumen bajo | ~$0.20 |
| **Total estimado** | | **~$20 USD** |

> Para uso personal en 4 días, sigue siendo completamente razonable. El costo real del proyecto sigue siendo tiempo, no dinero.

---

## Descartados y por qué

| Modelo | Razón del descarte |
|---|---|
| Claude Opus 4.6 ($5/$25) | Sobrecosto para este volumen — Sonnet da el 90% del rendimiento al 60% del precio |
| GPT-5.5 | Más caro que Opus, sin ventaja diferencial para español o análisis político |
| Xiaomi MiMo-V2-Pro | Alta popularidad en OpenRouter pero sin track record suficiente para análisis factual político |
| Llama 3.3 70B | Gratis pero rendimiento insuficiente para el nivel de análisis requerido |

---

*Fuente de precios: OpenRouter — mayo 2026*  
*Benchmarks: SWE-bench Verified, SimpleQA-Verified, HLE (Humanity's Last Exam)*  
*Documento parte del plan Dr. Contexto — ver `dr-contexto-plan.md`*