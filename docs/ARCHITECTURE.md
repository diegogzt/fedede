# Arquitectura del Sistema

## Visión General

El sistema Finance Due Diligence (Fedede) es una aplicación web diseñada para automatizar el análisis de documentos financieros. Utiliza una arquitectura cliente-servidor desacoplada.

## Diagrama de Componentes

```mermaid
graph TD
    Client[Frontend (Next.js)] <--> API[Backend API (FastAPI)]
    API --> Engine[Rule Engine]
    API --> DB[(SQLite Traceability DB)]
    Engine --> Excel[Excel Processor]
    Excel --> Files[File System]
```

## Componentes

### 1. Frontend (Next.js)

- **Tecnología**: Next.js 15+, React 19, TypeScript.
- **Estado Global**: Zustand para la gestión de archivos activos y configuración.
- **UI**: Tailwind CSS 4, Shadcn UI, Lucide React.
- **Comunicación**:
  - Cliente API centralizado en `frontend/lib/api.ts`.
  - Proxy configurado en `next.config.ts` para redirigir `/api` al backend.
  - Hooks personalizados como `useReport` para la gestión de datos de reportes.
- **Responsabilidad**:
  - Interfaz de usuario para carga de archivos.
  - Visualización de estado de procesamiento.
  - Dashboard de historial de documentos (Traceability).
  - Análisis financiero y visualización de KPIs (Revenue, Expenses).

### 2. Backend (FastAPI)

- **Tecnología**: Python 3.12, FastAPI, Uvicorn.
- **Responsabilidad**:
  - Exposición de endpoints REST (`/process-document`, `/history`, `/report/{id}`).
  - Gestión de carga y descarga de archivos.
  - Orquestación del procesamiento determinista.
  - Registro de auditoría en base de datos SQLite.

### 3. Motor de Reglas (Rule Engine)

- **Ubicación**: `backend/app/engine/rules.py`
- **Responsabilidad**:
  - Aplica reglas deterministas basadas en patrones (Regex) y umbrales de materialidad y variación.
  - Filtra transacciones irrelevantes.
  - Genera preguntas de auditoría basadas en anomalías detectadas.

### 4. Procesamiento de Datos

- **Ubicación**: `backend/app/processors/`
- **Responsabilidad**:
  - `excel_reader.py`: Lectura y normalización de archivos Excel/CSV.
  - `qa_generator.py`: Generación de reportes de preguntas y respuestas.
  - `financial_analyzer.py`: Análisis de variaciones entre periodos.
  - `models.py`: Definiciones de modelos Pydantic para la API.

### 5. Trazabilidad (Traceability)

- **Ubicación**: `backend/app/core/traceability.py`
- **Tecnología**: SQLite.
- **Responsabilidad**:
  - Almacena un registro de cada archivo procesado.
  - Guarda metadatos: nombre de archivo, fecha, estado, conteo de preguntas por prioridad.
  - Permite la persistencia del historial entre sesiones.

## Flujo de Datos

1. **Carga**: El usuario sube un archivo Excel desde el Frontend.
2. **Recepción**: FastAPI recibe el archivo, los umbrales y el idioma.
3. **Procesamiento**:
   - Se lee el Excel y se normalizan los datos.
   - El `FinancialAnalyzer` calcula variaciones.
   - El `RuleEngine` genera preguntas basadas en los hallazgos.
   - Se genera un reporte JSON y se prepara la exportación a Excel.
4. **Persistencia**: Se registra el evento en la base de datos SQLite con el estado `success` o `error`.
5. **Respuesta**: El Backend devuelve el objeto `ProcessedDocument`.
6. **Visualización**: El Frontend actualiza el estado global (Zustand) y muestra los resultados en el Dashboard y Analytics.
