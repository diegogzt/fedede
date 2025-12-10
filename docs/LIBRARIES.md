# Librerías Utilizadas

## Resumen de Dependencias

| Librería      | Versión | Propósito               | Crítica     |
| ------------- | ------- | ----------------------- | ----------- |
| pandas        | ≥2.0    | Manipulación de datos   | ✅ Sí       |
| openpyxl      | ≥3.1    | Lectura/escritura Excel | ✅ Sí       |
| openai        | ≥1.0    | API de OpenAI           | ⚠️ Opcional |
| requests      | ≥2.28   | HTTP para Ollama        | ⚠️ Opcional |
| python-dotenv | ≥1.0    | Variables de entorno    | ✅ Sí       |
| pytest        | ≥7.0    | Testing                 | 🧪 Dev      |
| pytest-mock   | ≥3.10   | Mocking en tests        | 🧪 Dev      |

## Dependencias de Producción

### pandas (≥2.0)

**Propósito:** Manipulación y análisis de datos tabulares.

**Uso en el proyecto:**

- `DataNormalizer`: Normalización de datos de balance
- `ExcelReader`: Conversión de Excel a DataFrames
- `FinancialAnalyzer`: Cálculos de variaciones

**Funciones principales usadas:**

```python
# Lectura
pd.read_excel()
pd.read_csv()

# Manipulación
df.groupby()
df.pivot_table()
df.merge()

# Agregación
df.sum()
df.mean()
df.apply()
```

**Por qué esta librería:**

- Estándar de la industria para datos tabulares
- Rendimiento optimizado con NumPy
- Excelente manejo de fechas y series temporales
- Integración nativa con Excel

---

### openpyxl (≥3.1)

**Propósito:** Lectura y escritura de archivos Excel (.xlsx).

**Uso en el proyecto:**

- `ExcelReader`: Lectura de balances de entrada
- `ExcelExporter`: Generación de reportes con múltiples tabs

**Funciones principales usadas:**

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border
from openpyxl.utils.dataframe import dataframe_to_rows

# Crear libro
wb = Workbook()
ws = wb.active

# Estilos
ws['A1'].font = Font(bold=True)
ws['A1'].fill = PatternFill(start_color="...", fill_type="solid")

# Guardar
wb.save("output.xlsx")
```

**Por qué esta librería:**

- Soporte completo para .xlsx (Office 2010+)
- Permite estilos, formatos y múltiples hojas
- No requiere Excel instalado
- Alternativas consideradas:
  - `xlrd`: Solo lectura, obsoleto para xlsx
  - `xlsxwriter`: Solo escritura
  - `xlwings`: Requiere Excel instalado

---

### openai (≥1.0)

**Propósito:** Generación de preguntas usando GPT-4.

**Uso en el proyecto:**

- `AIService`: Cliente para OpenAI API
- `prompts.py`: Templates de prompts

**Funciones principales usadas:**

```python
from openai import OpenAI

client = OpenAI(api_key="...")
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7,
    max_tokens=500
)
```

**Consideraciones de seguridad:**

- ⚠️ API key debe estar en variables de entorno
- ⚠️ No enviar datos sensibles directamente
- 🛡️ Usar `DataAnonymizer` antes de enviar datos
- Ver [DATA_PRIVACY.md](DATA_PRIVACY.md) para detalles

**Por qué esta librería:**

- SDK oficial de OpenAI
- Tipado completo (Python 3.8+)
- Manejo de errores robusto
- Soporte para streaming (futuro)

---

### requests (≥2.28)

**Propósito:** Cliente HTTP para Ollama (IA local).

**Uso en el proyecto:**

- `OllamaClient`: Comunicación con servidor Ollama local

**Funciones principales usadas:**

```python
import requests

response = requests.post(
    "http://localhost:11434/api/generate",
    json={"model": "llama2", "prompt": prompt},
    timeout=60
)
```

**Por qué esta librería:**

- Estándar de facto para HTTP en Python
- API simple e intuitiva
- Manejo de errores robusto
- Soporte para timeout y reintentos

**Ventajas de Ollama sobre OpenAI:**

- ✅ Datos permanecen en local
- ✅ Sin costos por API
- ✅ Sin dependencia de internet
- ❌ Requiere GPU potente
- ❌ Calidad variable según modelo

---

### python-dotenv (≥1.0)

**Propósito:** Carga de variables de entorno desde archivos `.env`.

**Uso en el proyecto:**

- `settings.py`: Carga de configuración sensible
- `ai_service.py`: Carga de API keys

**Uso:**

```python
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
```

**Archivo `.env` recomendado:**

```env
# .env (NO COMMITEAR)
OPENAI_API_KEY=sk-proj-xxxxx
OLLAMA_HOST=http://localhost:11434
LOG_LEVEL=INFO
```

**Por qué esta librería:**

- Estándar para gestión de secretos en desarrollo
- Compatible con despliegues en producción
- Evita hardcodear credenciales

---

## Dependencias de Desarrollo

### pytest (≥7.0)

**Propósito:** Framework de testing.

**Uso en el proyecto:**

- `tests/`: Todos los tests unitarios
- `pytest.ini`: Configuración de pytest

**Configuración (pytest.ini):**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --tb=short
```

**Comandos principales:**

```bash
# Ejecutar todos los tests
pytest

# Con coverage
pytest --cov=src

# Solo un archivo
pytest tests/test_processors.py

# Filtrar por nombre
pytest -k "test_fiscal"
```

---

### pytest-mock (≥3.10)

**Propósito:** Mocking simplificado para pytest.

**Uso en el proyecto:**

```python
def test_ai_service(mocker):
    # Mock de OpenAI
    mock_client = mocker.patch('src.ai.ai_service.OpenAI')
    mock_client.return_value.chat.completions.create.return_value = ...

    result = ai_service.generate_question(...)
    assert result == expected
```

---

## Librerías del Sistema (Built-in)

### tkinter

**Propósito:** Interfaz gráfica de usuario.

**Uso en el proyecto:**

- `src/gui/`: Toda la interfaz de usuario

**Por qué tkinter:**

- Incluido en Python (sin instalación adicional)
- Cross-platform (Windows, macOS, Linux)
- Suficiente para aplicaciones de escritorio simples
- Alternativas consideradas:
  - PyQt: Más potente pero licencia compleja
  - wxPython: Requiere instalación adicional
  - Kivy: Orientado a móviles

### logging

**Propósito:** Sistema de logging estructurado.

**Uso en el proyecto:**

- `src/core/logger.py`: Configuración centralizada
- Todos los módulos usan logging

### dataclasses

**Propósito:** Definición de modelos de datos.

**Uso en el proyecto:**

- `src/processors/models.py`: BalanceRow, QAItem, etc.
- `src/ai/data_anonymizer.py`: AnonymizedData

### typing

**Propósito:** Type hints para mejor documentación y autocompletado.

**Uso en el proyecto:**

- Todos los módulos usan type hints
- Compatible con mypy para verificación estática

### math

**Propósito:** Funciones matemáticas (isnan, abs, etc.).

**Uso en el proyecto:**

- `DataNormalizer`: Verificación de valores NaN
- `DataAnonymizer`: Clasificación de magnitudes

### enum

**Propósito:** Enumeraciones para valores discretos.

**Uso en el proyecto:**

- `DataAnonymizer`: SensitivityLevel, VariationMagnitude

---

## Instalación

### Producción

```bash
pip install -r requirements.txt
```

### Desarrollo

```bash
pip install -r requirements.txt
pip install pytest pytest-mock pytest-cov
```

### Archivo requirements.txt actual

```
pandas>=2.0.0
openpyxl>=3.1.0
openai>=1.0.0
requests>=2.28.0
python-dotenv>=1.0.0
```

---

## Compatibilidad

| Python | Estado        | Notas              |
| ------ | ------------- | ------------------ |
| 3.10   | ⚠️ Compatible | Mínimo recomendado |
| 3.11   | ✅ Soportado  | Probado            |
| 3.12   | ✅ Soportado  | Actual             |
| 3.13   | ❓ No probado | Debería funcionar  |

---

## Ver También

- [ARCHITECTURE.md](ARCHITECTURE.md) - Arquitectura del sistema
- [requirements.txt](../requirements.txt) - Dependencias actuales
