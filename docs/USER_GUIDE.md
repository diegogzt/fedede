# Guía de Usuario - FDD (Financial Due Diligence)

## ¿Qué es FDD?

FDD es una aplicación de escritorio que genera automáticamente cuestionarios de Due Diligence financiero a partir de balances contables en formato Excel o CSV.

**Entrada:** Balance mensual con cuentas contables
**Salida:** Excel con preguntas organizadas por categoría (PL, BS, Compras, etc.)

---

## Inicio Rápido

### 1. Instalación

```bash
# Clonar repositorio
git clone <url-del-repo>
cd FinanceDueDilligenceV1

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configuración Inicial

Crear archivo `.env` en la raíz:

```env
# Para usar OpenAI
OPENAI_API_KEY=tu-clave-api

# Para usar Ollama (local)
OLLAMA_HOST=http://localhost:11434
```

### 3. Ejecutar Aplicación

```bash
python main.py
```

---

## Interfaz de Usuario

```
┌────────────────────────────────────────────────────────────────────┐
│  Financial Due Diligence Generator                            [─][□][×]
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─ Archivo de Entrada ─────────────────────────────────────────┐ │
│  │  [Seleccionar archivo...]  balance_2024.xlsx                  │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌─ Configuración ───────────────────────────────────────────────┐│
│  │  Umbral variación %: [10   ]    Umbral absoluto: [50000  ]    ││
│  │  Proveedor IA: [OpenAI ▼]       Modelo: [gpt-4o-mini ▼]       ││
│  │  [✓] Modo estricto (máxima anonimización)                     ││
│  └───────────────────────────────────────────────────────────────┘│
│                                                                    │
│  ┌─ Progreso ────────────────────────────────────────────────────┐│
│  │  [████████████████░░░░░░░░░░░░░░] 55%                         ││
│  │  Procesando: Generando preguntas...                           ││
│  └───────────────────────────────────────────────────────────────┘│
│                                                                    │
│  ┌─ Vista Previa ────────────────────────────────────────────────┐│
│  │  | Pregunta               | Categoría | FY23    | FY24    |   ││
│  │  |------------------------|-----------|---------|---------|   ││
│  │  | Explique la reducción  | PL        | 5.2M    | 3.1M    |   ││
│  │  | del 40% en ingresos... |           |         |         |   ││
│  └───────────────────────────────────────────────────────────────┘│
│                                                                    │
│  [ Generar Reporte ]                              [ Exportar Excel ]│
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│  Listo | Último reporte: output_2024-01-15.xlsx                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Formato de Archivo de Entrada

### Estructura Esperada

| Código  | Descripción    | Ene 2023 | Feb 2023 | ... | Dic 2024 | Ene 2025 |
| ------- | -------------- | -------- | -------- | --- | -------- | -------- |
| 7000001 | Ventas España  | 100000   | 110000   | ... | 120000   | 80000    |
| 7000002 | Ventas Export  | 50000    | 55000    | ... | 60000    | 40000    |
| 6000001 | Coste Personal | -30000   | -31000   | ... | -35000   | -25000   |

### Requisitos

- **Formato:** Excel (.xlsx) o CSV
- **Columnas obligatorias:** Código, Descripción
- **Columnas de datos:** Formato "Mes Año" (ej: "Ene 2023", "Feb 2023")
- **Años:** Mínimo 2 años de datos para comparar

### Detección de Periodos

El sistema detecta automáticamente:

- **Años completos (FY):** Si hay 12 meses de datos
- **Años incompletos (YTD):** Si hay menos de 12 meses

Ejemplo:

- 2023: 12 meses → FY23
- 2024: 12 meses → FY24
- 2025: 8 meses → YTD25

Para comparación justa, se crean automáticamente:

- FY23 vs FY24 (12 meses vs 12 meses)
- YTD24 vs YTD25 (8 meses vs 8 meses)

---

## Configuración de Umbrales

### Umbral de Variación Porcentual

Define el cambio mínimo (en %) para considerar un ítem relevante.

| Valor | Efecto                          |
| ----- | ------------------------------- |
| 5%    | Muy sensible, muchas preguntas  |
| 10%   | Equilibrado (recomendado)       |
| 20%   | Solo variaciones grandes        |
| 50%   | Solo cambios muy significativos |

### Umbral Absoluto

Define el cambio mínimo en valor absoluto (€) para considerar un ítem relevante.

| Valor   | Efecto                        |
| ------- | ----------------------------- |
| 10,000  | Incluye cuentas pequeñas      |
| 50,000  | Equilibrado (recomendado)     |
| 100,000 | Solo cuentas medianas-grandes |
| 500,000 | Solo cuentas muy grandes      |

### Combinación de Umbrales

Un ítem se incluye si cumple **ambos** criterios:

- Variación % >= umbral porcentual
- Variación absoluta >= umbral absoluto

---

## Modos de Generación de Preguntas

### OpenAI (Recomendado para calidad)

```
Proveedor: OpenAI
Modelo: gpt-4o-mini (recomendado) o gpt-4
```

**Ventajas:**

- Preguntas muy naturales y específicas
- Contexto y matices

**Requisitos:**

- Cuenta de OpenAI con créditos
- Clave API configurada
- Conexión a internet

**Seguridad:**

- ✅ Modo estricto habilitado: datos anonimizados
- ⚠️ Modo estricto deshabilitado: datos sensibles pueden enviarse

### Ollama (Recomendado para privacidad)

```
Proveedor: Ollama
Modelo: llama2, mistral, codellama, etc.
```

**Ventajas:**

- 100% local, datos nunca salen
- Sin costos de API
- Sin internet

**Requisitos:**

- Ollama instalado y ejecutándose
- GPU recomendada (8GB+ VRAM)

**Instalación de Ollama:**

```bash
# Windows
winget install Ollama.Ollama

# Descargar modelo
ollama pull llama2
```

### Rule-Based (Sin IA)

```
Proveedor: Rule-Based
```

**Ventajas:**

- Sin dependencias externas
- Muy rápido
- 100% determinístico

**Desventajas:**

- Preguntas más genéricas
- Sin contexto específico

---

## Archivo de Salida

### Estructura del Excel Generado

El reporte se genera en `data/output/` con el formato:
`QA_Report_YYYY-MM-DD_HHMMSS.xlsx`

### Tabs del Excel

| Tab        | Contenido                            |
| ---------- | ------------------------------------ |
| General    | Todas las preguntas                  |
| PL         | Profit & Loss (cuenta de resultados) |
| BS         | Balance Sheet (balance de situación) |
| Compras    | Análisis de compras                  |
| Transporte | Costes logísticos                    |

### Columnas

| Columna     | Descripción                  |
| ----------- | ---------------------------- |
| Pregunta    | La pregunta de due diligence |
| Código      | Código de la cuenta          |
| Descripción | Descripción de la cuenta     |
| Categoría   | PL, BS, Compras, etc.        |
| Prioridad   | Alta, Media, Baja            |
| FY23        | Valor del ejercicio 2023     |
| FY24        | Valor del ejercicio 2024     |
| YTD24       | Acumulado 2024 (si aplica)   |
| YTD25       | Acumulado 2025 (si aplica)   |
| Var %       | Variación porcentual         |

---

## Solución de Problemas

### "No se detectan periodos"

**Causa:** El formato de columnas no es reconocido.

**Solución:** Usar formato "Mes Año" exacto:

- ✅ "Ene 2023", "Feb 2023"
- ❌ "01/2023", "2023-01"

### "Todas las columnas muestran '-'"

**Causa:** Los años detectados son incompletos.

**Solución:** Verificar que hay al menos un año con 12 meses de datos.

### "Error de conexión con OpenAI"

**Causas posibles:**

1. API key incorrecta o expirada
2. Sin conexión a internet
3. Límite de rate alcanzado

**Solución:** Verificar `.env` y conexión, o usar Ollama.

### "Ollama no responde"

**Causa:** Servidor Ollama no está ejecutándose.

**Solución:**

```bash
# Iniciar Ollama
ollama serve

# Verificar modelos disponibles
ollama list
```

---

## Ejemplos de Uso

### Caso 1: Due Diligence estándar

1. Cargar balance anual de la empresa objetivo
2. Configurar umbral 10% / 50,000€
3. Usar OpenAI con modo estricto
4. Exportar y revisar preguntas

### Caso 2: Análisis rápido interno

1. Cargar balance mensual
2. Configurar umbral 20% / 100,000€
3. Usar Rule-Based (sin IA)
4. Revisar principales variaciones

### Caso 3: Datos muy confidenciales

1. Cargar balance de la operación
2. Usar Ollama (local)
3. Los datos nunca salen del equipo
4. Exportar para revisión interna

---

## Soporte

Para reportar problemas o sugerir mejoras:

1. Revisar documentación en `/docs/`
2. Consultar FAQ en este documento
3. Contactar al equipo de desarrollo

---

## Ver También

- [DATA_PRIVACY.md](DATA_PRIVACY.md) - Privacidad de datos
- [ARCHITECTURE.md](ARCHITECTURE.md) - Arquitectura técnica
- [ALGORITHM.md](ALGORITHM.md) - Algoritmos utilizados
