# Algoritmos del Sistema FDD

Este documento describe los algoritmos principales utilizados en el sistema.

## 1. Detección de Periodos Fiscales

### Problema

Los balances contables vienen en formato mensual (Ene, Feb, ..., Dic) con múltiples años.
Necesitamos:

1. Detectar qué años fiscales hay
2. Identificar si cada año está completo (12 meses) o incompleto
3. Agregar datos por año fiscal
4. Mostrar comparativas correctas (FY vs FY, YTD vs YTD)

### Algoritmo: `detect_fiscal_periods()`

**Ubicación:** `src/processors/data_normalizer.py`

```
ENTRADA: DataFrame con columnas mensuales
         Ejemplo: ["Ene 2023", "Feb 2023", ..., "Ago 2025"]

SALIDA:  - fiscal_years: Lista de años completos (12 meses)
         - fiscal_years_all: Todos los años detectados
         - incomplete_years: Años con menos de 12 meses
         - month_columns: Mapeo año → lista de columnas mes
```

**Pseudocódigo:**

```
FUNCIÓN detect_fiscal_periods(df):
    # Paso 1: Extraer todas las columnas que parecen meses
    month_columns = {}
    PARA CADA columna EN df.columns:
        SI columna MATCH patrón "(Mes) (Año)":
            year = extraer_año(columna)
            month = extraer_mes(columna)
            month_columns[year].append(columna)

    # Paso 2: Clasificar años
    fiscal_years_complete = []
    incomplete_years = []

    PARA CADA year EN month_columns:
        SI len(month_columns[year]) == 12:
            fiscal_years_complete.append(year)
        SINO:
            incomplete_years.append(year)

    # Paso 3: Ordenar
    fiscal_years_complete.sort()

    RETORNAR fiscal_years_complete, incomplete_years, month_columns
```

**Ejemplo Real:**

```
Entrada:
  Columnas: ["Ene 2023", "Feb 2023", ..., "Dic 2024", "Ene 2025", ..., "Ago 2025"]

Proceso:
  2023: 12 meses encontrados → COMPLETO
  2024: 12 meses encontrados → COMPLETO
  2025: 8 meses encontrados  → INCOMPLETO

Salida:
  fiscal_years: [2023, 2024]
  incomplete_years: [2025]
  month_columns: {
    2023: ["Ene 2023", "Feb 2023", ..., "Dic 2023"],
    2024: ["Ene 2024", "Feb 2024", ..., "Dic 2024"],
    2025: ["Ene 2025", "Feb 2025", ..., "Ago 2025"]
  }
```

### Casos Especiales

| Escenario              | Comportamiento                          |
| ---------------------- | --------------------------------------- |
| Año con 11 meses       | Se marca como incompleto                |
| Año fiscal julio-junio | ❌ No soportado (asume enero-diciembre) |
| Columnas desordenadas  | Se ordenan automáticamente              |
| Formato "2023-01"      | Soportado via regex                     |

---

## 2. Agregación por Periodo

### Problema

Una vez detectados los periodos, necesitamos sumar todos los meses de cada año para obtener:

- FY (Fiscal Year): Suma de los 12 meses
- YTD (Year To Date): Suma de los meses disponibles (para años incompletos)

### Algoritmo: `aggregate_by_period()`

**Ubicación:** `src/processors/data_normalizer.py`

```
ENTRADA: DataFrame con datos mensuales + periodos detectados

SALIDA:  DataFrame con columnas agregadas (FY23, FY24, YTD24, YTD25, etc.)
```

**Pseudocódigo:**

```
FUNCIÓN aggregate_by_period(df, fiscal_years, incomplete_years, month_columns):
    result = df.copy()

    # Agregar años completos como FY
    PARA CADA year EN fiscal_years:
        cols = month_columns[year]
        result[f"FY{year%100}"] = df[cols].sum(axis=1)

    # Agregar años incompletos como YTD
    PARA CADA year EN incomplete_years:
        cols = month_columns[year]
        result[f"YTD{year%100}"] = df[cols].sum(axis=1)

    # Para comparaciones YTD justas, crear YTD del año anterior
    # con los mismos meses
    PARA CADA year EN incomplete_years:
        SI (year - 1) EN month_columns:
            # Obtener solo los meses equivalentes del año anterior
            n_months = len(month_columns[year])
            prev_cols = month_columns[year-1][:n_months]
            result[f"YTD{(year-1)%100}"] = df[prev_cols].sum(axis=1)

    RETORNAR result
```

**Ejemplo:**

```
Si 2025 tiene Ene-Ago (8 meses):
- Crear YTD25 = suma(Ene 2025 ... Ago 2025)
- Crear YTD24 = suma(Ene 2024 ... Ago 2024)  ← mismos 8 meses

Esto permite comparación justa:
- YTD25 vs YTD24 (ambos 8 meses)
- FY24 vs FY23 (ambos 12 meses)
```

---

## 3. Cálculo de Variaciones

### Problema

Dado un ítem con valores en dos periodos, calcular la variación absoluta y porcentual.

### Algoritmo: `calculate_variation()`

**Ubicación:** `src/processors/financial_analyzer.py`

```
ENTRADA: valor_base, valor_compare

SALIDA:  variación_abs, variación_pct
```

**Pseudocódigo:**

```
FUNCIÓN calculate_variation(base, compare):
    # Variación absoluta
    var_abs = compare - base

    # Variación porcentual
    SI base == 0:
        SI compare == 0:
            var_pct = 0
        SINO SI compare > 0:
            var_pct = 100  # Apareció (infinito normalizado)
        SINO:
            var_pct = -100
    SINO:
        var_pct = ((compare - base) / abs(base)) * 100

    RETORNAR var_abs, var_pct
```

**Casos especiales manejados:**

| Base | Compare | Var Abs | Var % | Descripción         |
| ---- | ------- | ------- | ----- | ------------------- |
| 100  | 150     | 50      | 50%   | Incremento normal   |
| 100  | 50      | -50     | -50%  | Decremento normal   |
| 0    | 100     | 100     | 100%  | Nueva cuenta        |
| 100  | 0       | -100    | -100% | Cuenta desaparecida |
| 0    | 0       | 0       | 0%    | Sin actividad       |
| -100 | -50     | 50      | 50%   | Menos pérdida       |
| NaN  | 100     | -       | -     | No calculable       |

---

## 4. Detección de Items Materiales

### Problema

No todos los ítems son relevantes para due diligence. Necesitamos filtrar por materialidad.

### Algoritmo: `is_material()`

**Ubicación:** `src/processors/financial_analyzer.py`

```
ENTRADA: item, threshold_pct, threshold_abs

SALIDA:  bool (es material o no)
```

**Criterios de materialidad:**

```
UN ITEM ES MATERIAL SI:
    (|variación_pct| >= threshold_pct)
    Y
    (|variación_abs| >= threshold_abs)
    Y
    (valor_max >= min_value)
```

**Configuración por defecto:**

- `threshold_pct`: 10% (variación mínima)
- `threshold_abs`: 50,000 (variación absoluta mínima)
- `min_value`: 100,000 (valor mínimo de la cuenta)

---

## 5. Generación de Preguntas

### Modos de Generación

El sistema soporta 3 modos:

| Modo         | Descripción   | Privacidad       | Calidad |
| ------------ | ------------- | ---------------- | ------- |
| `openai`     | GPT-4 vía API | ⚠️ Datos salen   | ⭐⭐⭐  |
| `ollama`     | LLM local     | ✅ Datos locales | ⭐⭐    |
| `rule_based` | Reglas fijas  | ✅ Sin IA        | ⭐      |

### Algoritmo: `generate_question()` (OpenAI con anonimización)

**Ubicación:** `src/ai/ai_service.py` + `src/ai/data_anonymizer.py`

```
ENTRADA: VariationItem (con datos sensibles)

SALIDA:  pregunta (string)
```

**Flujo con anonimización (RECOMENDADO):**

```
FUNCIÓN generate_question_safe(item):
    # 1. Anonimizar datos antes de enviar
    anonymizer = DataAnonymizer(strict_mode=True)
    anon_data = anonymizer.anonymize(
        description=item.descripcion,
        account_code=item.codigo,
        value_base=item.valor_base,
        value_compare=item.valor_compare,
        variation_pct=item.variacion_pct,
        ...
    )

    # 2. Crear prompt con datos anónimos
    prompt = f"""
    Genera pregunta para:
    - Tipo: {anon_data.category_generic}  # "Cuenta de ingresos"
    - Variación: {anon_data.variation_magnitude}  # "significativa"
    - Cambio: {anon_data.variation_percentage}%  # Solo el %
    - Importancia: {anon_data.value_range}  # "grande"
    """

    # 3. Enviar a OpenAI (datos seguros)
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    # 4. Retornar pregunta
    RETORNAR response.choices[0].message.content
```

**Lo que se envía a OpenAI (DESPUÉS de anonimizar):**

```
✅ "Cuenta de ingresos" (no "Ventas Iberdrola S.A.")
✅ "variación significativa" (no "-2,450,000€")
✅ "40%" (solo el porcentaje)
✅ "cuenta grande" (no el monto exacto)
```

**Lo que NO se envía:**

```
❌ Nombre de la empresa
❌ Montos exactos
❌ Nombres de clientes/proveedores
❌ Códigos de cuenta específicos
```

### Algoritmo: `generate_question()` (Rule-based)

**Ubicación:** `src/ai/prompts.py`

```
FUNCIÓN generate_question_rule_based(item):
    SI item.variacion_pct > 0:
        direction = "incremento"
    SINO:
        direction = "decremento"

    SI abs(item.variacion_pct) > 50:
        intensity = "significativo"
    SINO SI abs(item.variacion_pct) > 20:
        intensity = "moderado"
    SINO:
        intensity = "leve"

    template = TEMPLATES[item.categoria][direction][intensity]

    RETORNAR template.format(
        descripcion=item.descripcion,
        variacion=item.variacion_pct
    )
```

**Templates ejemplo:**

```python
TEMPLATES = {
    "PL": {
        "incremento": {
            "significativo": "Explique el incremento del {variacion:.1f}% en {descripcion}.",
            "moderado": "Describa los factores detrás del aumento en {descripcion}.",
            "leve": "Comente sobre la evolución de {descripcion}."
        },
        "decremento": {
            "significativo": "Justifique la reducción del {variacion:.1f}% en {descripcion}.",
            ...
        }
    },
    ...
}
```

---

## 6. Exportación a Excel

### Algoritmo: `export_to_excel()`

**Ubicación:** `src/processors/qa_generator.py`

```
ENTRADA: List[QAItem], output_path

SALIDA:  Archivo Excel con múltiples tabs
```

**Estructura del Excel:**

```
┌─────────────────────────────────────────────────────────────────┐
│ Tab "General"                                                   │
├─────────────────────────────────────────────────────────────────┤
│ Pregunta | Categoría | Prioridad | FY23 | FY24 | YTD24 | YTD25 │
├─────────────────────────────────────────────────────────────────┤
│ ...      | ...       | ...       | ...  | ...  | ...   | ...   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Tab "PL" (Profit & Loss)                                        │
├─────────────────────────────────────────────────────────────────┤
│ Solo filas donde categoria == "PL"                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Tab "BS" (Balance Sheet)                                        │
├─────────────────────────────────────────────────────────────────┤
│ Solo filas donde categoria == "BS"                              │
└─────────────────────────────────────────────────────────────────┘

... (tabs adicionales: Compras, Transporte, etc.)
```

**Pseudocódigo:**

```
FUNCIÓN export_to_excel(items, path):
    wb = Workbook()

    # Tab General
    ws_general = wb.active
    ws_general.title = "General"
    add_headers(ws_general, COLUMNS)
    add_rows(ws_general, items)
    apply_styles(ws_general)

    # Tabs por categoría
    categories = set(item.categoria FOR item IN items)
    PARA CADA cat EN categories:
        ws = wb.create_sheet(title=cat)
        filtered = [i FOR i IN items IF i.categoria == cat]
        add_headers(ws, COLUMNS)
        add_rows(ws, filtered)
        apply_styles(ws)

    wb.save(path)
```

---

## Complejidad Algorítmica

| Algoritmo             | Tiempo  | Espacio | Notas                       |
| --------------------- | ------- | ------- | --------------------------- |
| detect_fiscal_periods | O(n)    | O(n)    | n = columnas                |
| aggregate_by_period   | O(n\*m) | O(n\*m) | n = filas, m = columnas     |
| calculate_variation   | O(1)    | O(1)    | Constante                   |
| is_material           | O(1)    | O(1)    | Constante                   |
| generate_question     | O(1)    | O(1)    | Dominado por latencia de IA |
| export_to_excel       | O(n)    | O(n)    | n = items                   |

---

## Ver También

- [DATA_PRIVACY.md](DATA_PRIVACY.md) - Detalles de anonimización
- [ARCHITECTURE.md](ARCHITECTURE.md) - Arquitectura general
- `src/processors/data_normalizer.py` - Implementación de periodos
- `src/ai/data_anonymizer.py` - Implementación de anonimización
