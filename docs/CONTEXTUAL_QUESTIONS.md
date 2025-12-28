# Mejoras en la Generación de Preguntas y Razones Contextuales

## Resumen de Cambios

Se ha mejorado significativamente el sistema de generación de preguntas y razones para el reporte Q&A, utilizando IA local (Ollama/OpenAI) para crear preguntas contextuales avanzadas.

## Antes vs Después

### ANTES (Preguntas Genéricas):

```
Cuenta: 70000000 - Ventas de mercaderías
Pregunta: "Por favor explique las variaciones en 'Ventas de mercaderías' entre FY23 y FY24"
Razón: "Variación > 20%"
```

### DESPUÉS (Preguntas Contextuales):

```
Cuenta: 70000000 - Ventas de mercaderías
Pregunta:
"(i) Comentar de manera general los principales 'drivers' del crecimiento de ingresos entre FY23 y FY24 (14%)
(ii) ¿Por qué se ve una ralentización de los ingresos entre YTD-Oct24 y YTD-Oct25 (3%) cuando se compara con el crecimiento de los ingresos en el periodo anterior?"

Razón: "Crecimiento del 14% YoY pero desaceleración al 3% YTD sugiere cambio de tendencia que requiere análisis"
```

## Características de las Nuevas Preguntas

1. **Análisis Multi-Periodo**: Comparan múltiples periodos simultáneamente (FY21-FY25, YTD, etc.)
2. **Sub-Preguntas Numeradas**: Formato (i), (ii), (iii) para desglosar análisis complejos
3. **Detección de Tendencias**: Identifican aceleraciones, desaceleraciones, inversiones de tendencia
4. **Datos Específicos**: Mencionan porcentajes exactos y valores absolutos
5. **Orientadas a Drivers**: Solicitan explicación de los factores causales principales

## Características de las Nuevas Razones

1. **Contextuales**: Explican POR QUÉ la pregunta es importante
2. **Específicas**: Mencionan magnitudes exactas de variación
3. **Detectan Patrones**: Identifican cambios de tendencia, nuevos conceptos, desapariciones
4. **Concisas**: Máximo 2 líneas, pero informativas

Ejemplos de razones:

- "Crecimiento del 14% YoY pero desaceleración al 3% YTD sugiere cambio de tendencia"
- "Nueva cuenta significativa (4.3% de ingresos) sin presencia en periodos anteriores"
- "Disminución de 5pp sobre ingresos indica cambio estructural en costos"

## Nuevas Reglas Deterministas (FDD Específicas)

Además de la generación por IA, se han implementado reglas deterministas críticas para el Due Diligence Financiero:

1. **Validación de Naturaleza de Signo**: Detecta automáticamente si una cuenta de activo tiene saldo acreedor (negativo), lo cual es una anomalía contable de alta prioridad.
2. **Lógica de Enfoque (Focus)**: Permite forzar la generación de preguntas para cuentas o periodos específicos definidos por el usuario, ignorando los umbrales de materialidad.
3. **Plantilla de Auditoría Estándar**: El sistema ahora incluye 25 puntos de control fijos en la hoja "General" del reporte Excel, asegurando que los temas críticos (CIRBE, Impuestos, Personal) siempre sean revisados.

## Implementación Técnica

### 1. Nuevos Prompts en `src/ai/prompts.py`

Se crearon dos nuevos templates:

- `question_contextual`: Genera preguntas analizando contexto completo
- `reason_contextual`: Genera razones detalladas

### 2. Método de Preparación de Contexto

`_prepare_item_context()` en `qa_generator.py` prepara un contexto completo que incluye:

- Todos los valores por periodo
- Todas las variaciones detectadas
- Porcentajes sobre ingresos
- Cambios en puntos porcentuales
- Detección automática de:
  - Nuevos conceptos / desaparecidos
  - Inversión de tendencia
  - Aceleración / desaceleración

### 3. Generación con IA

Nuevos métodos en `AIService`:

- `generate_contextual_question()`: Genera pregunta contextual avanzada
- `generate_contextual_reason()`: Genera razón detallada
- `_generate_simple_question_from_context()`: Fallback sin IA
- `_generate_simple_reason_from_context()`: Fallback sin IA

### 4. Integración en el Flujo

El método `generate_report_with_ai()` ahora:

1. Genera reporte base con datos normalizados
2. Identifica items de alta/media prioridad
3. Para cada item importante:
   - Prepara contexto completo
   - Genera pregunta contextual con IA
   - Genera razón contextual con IA
4. Mantiene preguntas basadas en reglas como fallback

## Uso

```python
from src.processors.qa_generator import QAGenerator
from src.processors.models import Priority

# Con IA (Ollama o OpenAI)
generator = QAGenerator(use_ai=True, ai_mode='auto')
report = generator.generate_report_with_ai(
    balance=balance,
    min_priority=Priority.ALTA
)

# Sin IA (basado en reglas)
generator = QAGenerator(use_ai=False)
report = generator.generate_report(
    balance=balance,
    min_priority=Priority.ALTA
)
```

## Beneficios

1. **Mayor Valor para el Cliente**: Preguntas más profesionales y específicas
2. **Menos Trabajo Manual**: No requiere reescribir las preguntas manualmente
3. **Análisis más Profundo**: Detecta patrones que las reglas simples no capturan
4. **Flexibilidad**: Funciona con y sin IA
5. **Escalabilidad**: Procesa grandes volúmenes de cuentas eficientemente

## Requisitos

- **Ollama** (recomendado): IA local gratuita
  - Instalar: https://ollama.com
  - Modelo recomendado: `llama3.2` o `mistral`
- **OpenAI** (alternativa): Requiere API key
  - Configurar: `export OPENAI_API_KEY=sk-...`
- **Sin IA**: Funciona con preguntas basadas en reglas (menos contextuales)

## Tests

Ejecutar tests:

```bash
# Test completo del escenario real
pytest tests/test_real_data_scenario.py -v -s

# Test específico de preguntas contextuales
pytest tests/test_contextual_questions.py -v -s

# Demo interactivo
python scripts/demo_contextual_questions.py
```

## Configuración

En `src/config/settings.py`:

```python
class AISettings:
    temperature: float = 0.7  # Creatividad de las preguntas
    default_model: str = "llama3.2"
    auto_fallback: bool = True  # Usar reglas si IA falla
```

## Rendimiento

- **Sin IA**: ~2-5 segundos para 100 cuentas
- **Con IA (Ollama)**: ~60-120 segundos para 100 cuentas (local)
- **Con IA (OpenAI)**: ~30-60 segundos para 100 cuentas (API)

La IA solo se usa para items de **alta/media prioridad** para optimizar tiempos.
