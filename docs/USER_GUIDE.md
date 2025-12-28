# Guía de Usuario - Fedede (Financial Due Diligence)

## ¿Qué es Fedede?

Fedede es una aplicación web diseñada para automatizar la generación de cuestionarios de Due Diligence financiero a partir de balances contables. El sistema analiza variaciones entre periodos y aplica reglas de negocio para identificar anomalías que requieren explicación.

---

## Inicio Rápido

### 1. Acceso

Abre tu navegador en [http://localhost:3000](http://localhost:3000).

### 2. Carga de Datos

1. Ve a la sección **"Cargar Datos"** en la barra lateral.
2. Arrastra o selecciona tu archivo de balance (Excel o CSV).
3. Configura los parámetros de análisis:
   - **Idioma del Reporte:** Español, Inglés o Bilingüe.
   - **Umbral de Variación (%):** Porcentaje mínimo de cambio para generar una pregunta.
   - **Umbral de Materialidad (€):** Valor absoluto mínimo para considerar una variación relevante.
   - **Configuración Avanzada (Opcional):**
     - **Cuentas de Enfoque:** Lista de códigos de cuenta (separados por comas) que quieres analizar sí o sí.
     - **Periodos de Enfoque:** Pares de periodos a comparar (ej: `FY23-FY24, FY24-YTD25`).
4. Haz clic en **"Procesar Documento"**.

### 4. Visualización de Resultados

Una vez procesado, puedes explorar los hallazgos en diferentes vistas:

- **Dashboard:** Resumen general de preguntas por prioridad (Alta, Media, Baja).
- **Analytics:** Comparativa visual de ingresos y gastos entre periodos.
- **Audit:** Lista detallada de todas las preguntas generadas con su justificación técnica.
- **Reports:** Historial de todos los documentos procesados con opción de descarga.

---

## Exportación a Excel

El reporte generado incluye una hoja **"General"** con 25 puntos de control estándar de auditoría, que cubren:

- Conciliaciones bancarias.
- Deuda financiera y CIRBE.
- Impuestos y Seguridad Social.
- Ventas y Clientes.
- Gastos de personal.

---

## Secciones de la Aplicación

### Dashboard

Muestra los KPIs principales del archivo activo o un resumen global si no hay ninguno seleccionado. Incluye gráficos de distribución de prioridades y acceso rápido a los últimos archivos procesados.

### Cargar Datos

El centro de control para nuevos análisis. Permite ajustar los umbrales de auditoría. Es obligatorio confirmar que se han revisado los umbrales antes de procesar.

### Auditoría (Audit)

Vista detallada de las preguntas. Cada ítem incluye:

- Código y descripción de la cuenta.
- Valores de los periodos comparados.
- Variación absoluta y porcentual.
- Pregunta sugerida para el cliente.
- Prioridad asignada automáticamente.

### Análisis (Analytics)

Gráficos interactivos que muestran la evolución de las partidas principales. Permite comparar rápidamente el impacto de las variaciones en el balance general.

---

## Formato de Archivo de Entrada

### Estructura Sugerida

El sistema es flexible, pero se recomienda que el archivo contenga:

- Una columna de **Código** de cuenta.
- Una columna de **Descripción** de cuenta.
- Columnas mensuales o anuales con los valores financieros.

### Requisitos Técnicos

- **Formatos soportados:** .xlsx, .xls, .xlsm, .csv, .txt.
- **Tamaño máximo:** 100MB.
- **Limpieza:** El sistema normaliza automáticamente nombres de columnas y valores nulos.

---

## Exportación

Desde la sección de **Reports**, puedes descargar el análisis final en formato Excel bilingüe, listo para ser enviado al cliente o integrado en el informe de Due Diligence.

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
